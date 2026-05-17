import json
import os
from pathlib import Path

import click

from .auth import get_session2_from_env, redact_secrets
from .client import InvalidSessionError, OverleafBridgeError, OverleafCookieClient
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


if __name__ == "__main__":
    main()
