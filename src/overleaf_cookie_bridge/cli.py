import json
import os
from pathlib import Path
from typing import Literal

import click

from .auth import get_session2_from_env, redact_secrets
from .client import InvalidSessionError, OverleafBridgeError, OverleafCookieClient
from .remote_zip import read_zip_member
from .sync import backup_zip, default_backup_root, extract_zip_safely


def _client(host: str, timeout: int) -> OverleafCookieClient:
    session2 = get_session2_from_env()
    if not session2:
        raise click.ClickException(
            "Missing OVERLEAF_SESSION2. Set it in the current shell; do not commit or "
            "paste it into files."
        )
    return OverleafCookieClient(session2=session2, host=host, timeout=timeout)


def _backup_root() -> Path:
    configured = os.environ.get("OVERLEAF_COOKIE_BACKUP_ROOT")
    return Path(configured).expanduser() if configured else default_backup_root()


@click.group()
@click.option("--host", default="www.overleaf.com", show_default=True, help="Overleaf host")
@click.option("--timeout", default=30, show_default=True, help="HTTP timeout in seconds")
@click.pass_context
def main(ctx: click.Context, host: str, timeout: int) -> None:
    ctx.obj = {"host": host, "timeout": timeout}


@main.command()
@click.pass_context
def verify(ctx: click.Context) -> None:
    """Verify that OVERLEAF_SESSION2 can access Overleaf."""
    try:
        client = _client(ctx.obj["host"], ctx.obj["timeout"])
        projects = client.list_projects(include_archived=True, include_trashed=True)
    except (InvalidSessionError, OverleafBridgeError) as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc
    click.echo(f"OK: cookie is valid; visible projects: {len(projects)}")


@main.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output machine-readable JSON")
@click.option("--all", "include_all", is_flag=True, help="Include archived and trashed projects")
@click.pass_context
def list_projects(ctx: click.Context, as_json: bool, include_all: bool) -> None:
    """List visible Overleaf projects."""
    try:
        client = _client(ctx.obj["host"], ctx.obj["timeout"])
        projects = client.list_projects(include_archived=include_all, include_trashed=include_all)
    except (InvalidSessionError, OverleafBridgeError) as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc
    if as_json:
        click.echo(json.dumps([p.to_dict() for p in projects], ensure_ascii=False, indent=2))
    else:
        for project in projects:
            click.echo(f"{project.id}\t{project.name}\t{project.access_level}\t{project.last_updated}")


@main.command()
@click.argument("project_id")
@click.pass_context
def backup(ctx: click.Context, project_id: str) -> None:
    """Download a timestamped backup zip for PROJECT_ID."""
    try:
        client = _client(ctx.obj["host"], ctx.obj["timeout"])
        zip_bytes = client.download_project_zip(project_id)
        output = backup_zip(zip_bytes, project_id=project_id, backup_root=_backup_root())
    except OverleafBridgeError as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc
    click.echo(f"Backup saved: {output}")


@main.command()
@click.argument("project_id")
@click.argument("destination", type=click.Path(path_type=Path))
@click.pass_context
def pull(ctx: click.Context, project_id: str, destination: Path) -> None:
    """Backup and extract PROJECT_ID to DESTINATION."""
    try:
        client = _client(ctx.obj["host"], ctx.obj["timeout"])
        zip_bytes = client.download_project_zip(project_id)
        backup_path = backup_zip(zip_bytes, project_id=project_id, backup_root=_backup_root())
        extract_zip_safely(zip_bytes, destination)
    except (OverleafBridgeError, ValueError) as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc
    click.echo(f"Backup saved: {backup_path}")
    click.echo(f"Extracted to: {destination}")


@main.command("push-file")
@click.argument("project_id")
@click.argument("local_file", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--remote", "remote_path", required=True, help="Remote path inside the Overleaf zip")
@click.option("--folder-id", required=True, help="Overleaf parent folder id for the remote file")
@click.option("--entity-id", required=True, help="Existing Overleaf entity id to replace")
@click.option(
    "--entity-type",
    type=click.Choice(["doc", "file"], case_sensitive=False),
    default="doc",
    show_default=True,
    help="Existing Overleaf entity type",
)
@click.option("--dry-run", is_flag=True, help="Show the write plan without mutating Overleaf")
@click.option("--yes", is_flag=True, help="Execute the remote delete+upload replacement")
@click.pass_context
def push_file(
    ctx: click.Context,
    project_id: str,
    local_file: Path,
    remote_path: str,
    folder_id: str,
    entity_id: str,
    entity_type: Literal["doc", "file"],
    dry_run: bool,
    yes: bool,
) -> None:
    """Replace one remote Overleaf file via backup, delete, upload, and zip verification."""
    if not dry_run and not yes:
        raise click.ClickException(
            "Refusing remote mutation without --yes. Use --dry-run to preview."
        )

    try:
        client = _client(ctx.obj["host"], ctx.obj["timeout"])
        local_bytes = local_file.read_bytes()
        before_zip = client.download_project_zip(project_id)
        try:
            before_remote_bytes = read_zip_member(before_zip, remote_path)
        except FileNotFoundError as exc:
            raise click.ClickException(str(exc)) from exc
        backup_path = backup_zip(before_zip, project_id=project_id, backup_root=_backup_root())
    except OverleafBridgeError as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc

    click.echo("Remote replacement plan:")
    click.echo(f"  project:      {project_id}")
    click.echo(f"  remote path:  {remote_path}")
    click.echo(f"  local file:   {local_file}")
    click.echo(f"  old entity:   {entity_type}/{entity_id}")
    click.echo(f"  folder id:    {folder_id}")
    click.echo(f"  backup:       {backup_path}")
    click.echo(f"  old size:     {len(before_remote_bytes)} bytes")
    click.echo(f"  new size:     {len(local_bytes)} bytes")

    if dry_run:
        click.echo("DRY RUN: no remote changes were made.")
        return

    try:
        client.delete_entity(project_id, entity_type, entity_id)
        uploaded = client.upload_file(project_id, folder_id, Path(remote_path).name, local_bytes)
        after_zip = client.download_project_zip(project_id)
        after_remote_bytes = read_zip_member(after_zip, remote_path)
    except (OverleafBridgeError, FileNotFoundError) as exc:
        raise click.ClickException(redact_secrets(str(exc))) from exc

    if after_remote_bytes != local_bytes:
        raise click.ClickException(
            "Remote verification failed: downloaded zip content does not match local file. "
            f"Backup saved at {backup_path}"
        )

    click.echo(f"Deleted remote entity: {entity_type}/{entity_id}")
    click.echo(f"Uploaded remote entity: {uploaded.entity_type}/{uploaded.entity_id}")
    click.echo("Verified remote content matches local file.")
    click.echo(f"Backup saved: {backup_path}")


if __name__ == "__main__":
    main()
