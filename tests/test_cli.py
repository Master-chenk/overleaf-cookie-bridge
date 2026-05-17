import responses
from click.testing import CliRunner
from helpers import make_zip, project_html

from overleaf_cookie_bridge.cli import main


def test_cli_verify_requires_cookie(monkeypatch):
    monkeypatch.delenv("OVERLEAF_SESSION2", raising=False)
    result = CliRunner().invoke(main, ["verify"])

    assert result.exit_code != 0
    assert "OVERLEAF_SESSION2" in result.output


@responses.activate
def test_cli_list_outputs_json(monkeypatch):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    responses.get(
        "https://www.overleaf.com/",
        body=project_html([
            {
                "id": "p1",
                "name": "Paper",
                "lastUpdated": "now",
                "accessLevel": "owner",
                "source": "owner",
                "archived": False,
                "trashed": False,
            }
        ]),
    )

    result = CliRunner().invoke(main, ["list", "--json"])

    assert result.exit_code == 0
    assert '"id": "p1"' in result.output


@responses.activate
def test_cli_pull_downloads_backs_up_and_extracts(monkeypatch, tmp_path):
    monkeypatch.setenv("OVERLEAF_SESSION2", "cookie")
    monkeypatch.setenv("OVERLEAF_COOKIE_BACKUP_ROOT", str(tmp_path / "backups"))
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=make_zip({"main.tex": "hello"}),
        content_type="application/zip",
    )

    result = CliRunner().invoke(main, ["pull", "p1", str(tmp_path / "paper")])

    assert result.exit_code == 0
    assert (tmp_path / "paper" / "main.tex").read_text() == "hello"
    assert list((tmp_path / "backups" / "p1").glob("*.zip"))
