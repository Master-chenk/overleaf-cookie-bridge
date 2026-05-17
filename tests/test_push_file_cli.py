import responses
from click.testing import CliRunner
from helpers import make_zip

from overleaf_cookie_bridge.cli import main


def push_args(local, mode):
    return [
        "push-file",
        "p1",
        str(local),
        "--remote",
        "main.tex",
        "--folder-id",
        "root",
        "--entity-id",
        "doc1",
        "--entity-type",
        "doc",
        mode,
    ]


def test_push_file_requires_yes_for_execution(monkeypatch, tmp_path):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    local = tmp_path / "main.tex"
    local.write_text("new")

    result = CliRunner().invoke(
        main,
        [
            "push-file",
            "p1",
            str(local),
            "--remote",
            "main.tex",
            "--folder-id",
            "root",
            "--entity-id",
            "doc1",
        ],
    )

    assert result.exit_code != 0
    assert "--yes" in result.output


@responses.activate
def test_push_file_dry_run_does_not_mutate(monkeypatch, tmp_path):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    monkeypatch.setenv("OVERLEAF_COOKIE_BACKUP_ROOT", str(tmp_path / "backups"))
    local = tmp_path / "main.tex"
    local.write_bytes(b"new")
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": b"old"}),
        content_type="application/zip",
    )

    result = CliRunner().invoke(main, push_args(local, "--dry-run"))

    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert len(responses.calls) == 1


@responses.activate
def test_push_file_replaces_and_verifies(monkeypatch, tmp_path):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    monkeypatch.setenv("OVERLEAF_COOKIE_BACKUP_ROOT", str(tmp_path / "backups"))
    local = tmp_path / "main.tex"
    local.write_bytes(b"new")
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": b"old"}),
        content_type="application/zip",
    )
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>',
    )
    responses.delete("https://www.overleaf.com/project/p1/doc/doc1", status=204)
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>',
    )
    responses.post(
        "https://www.overleaf.com/project/p1/upload?folder_id=root",
        json={"success": True, "entity_id": "doc2", "entity_type": "doc"},
    )
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": b"new"}),
        content_type="application/zip",
    )

    result = CliRunner().invoke(main, push_args(local, "--yes"))

    assert result.exit_code == 0, result.output
    assert "Verified remote content" in result.output
    assert list((tmp_path / "backups" / "p1").glob("*.zip"))


@responses.activate
def test_push_file_fails_when_verification_mismatch(monkeypatch, tmp_path):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    monkeypatch.setenv("OVERLEAF_COOKIE_BACKUP_ROOT", str(tmp_path / "backups"))
    local = tmp_path / "main.tex"
    local.write_bytes(b"new")
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": b"old"}),
    )
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<meta name="ol-csrfToken" content="csrf123">',
    )
    responses.delete("https://www.overleaf.com/project/p1/doc/doc1", status=204)
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<meta name="ol-csrfToken" content="csrf123">',
    )
    responses.post(
        "https://www.overleaf.com/project/p1/upload?folder_id=root",
        json={"success": True, "entity_id": "doc2", "entity_type": "doc"},
    )
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": b"wrong"}),
    )

    result = CliRunner().invoke(main, push_args(local, "--yes"))

    assert result.exit_code != 0
    assert "verification failed" in result.output.lower()
