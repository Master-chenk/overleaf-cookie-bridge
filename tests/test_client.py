import pytest
import responses
from helpers import project_html

from overleaf_cookie_bridge.client import (
    InvalidSessionError,
    OverleafCookieClient,
    parse_projects_html,
)


def test_parse_projects_html_extracts_core_fields():
    projects = parse_projects_html(project_html([
        {
            "id": "abc123",
            "name": "Paper",
            "lastUpdated": "2026-05-01T00:00:00.000Z",
            "accessLevel": "owner",
            "source": "owner",
            "archived": False,
            "trashed": False,
        }
    ]))

    assert len(projects) == 1
    assert projects[0].id == "abc123"
    assert projects[0].name == "Paper"
    assert projects[0].access_level == "owner"


def test_parse_projects_html_rejects_missing_blob():
    with pytest.raises(InvalidSessionError):
        parse_projects_html("<html></html>")


@responses.activate
def test_client_list_projects_uses_homepage_blob():
    responses.get(
        "https://www.overleaf.com/",
        body=project_html([
            {
                "id": "p1",
                "name": "Demo",
                "lastUpdated": "now",
                "accessLevel": "readAndWrite",
                "source": "shared",
                "archived": False,
                "trashed": False,
            }
        ]),
        status=200,
    )
    client = OverleafCookieClient(session2="cookie")

    projects = client.list_projects()

    assert [p.name for p in projects] == ["Demo"]


@responses.activate
def test_client_download_project_zip_returns_bytes():
    responses.get(
        "https://www.overleaf.com/project/p1/download/zip",
        body=b"PK fake zip",
        status=200,
        content_type="application/zip",
    )
    client = OverleafCookieClient(session2="cookie")

    assert client.download_project_zip("p1") == b"PK fake zip"
