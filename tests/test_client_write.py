import responses

from overleaf_cookie_bridge.client import OverleafCookieClient


def test_get_csrf_token_fetches_project_page():
    with responses.RequestsMock() as rsps:
        rsps.get(
            "https://www.overleaf.com/project/p1",
            body='<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>',
            status=200,
        )
        client = OverleafCookieClient(session2="cookie")

        assert client.get_csrf_token("p1") == "csrf123"


@responses.activate
def test_upload_file_posts_multipart_with_csrf():
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>',
        status=200,
    )
    responses.post(
        "https://www.overleaf.com/project/p1/upload?folder_id=root",
        json={"success": True, "entity_id": "newdoc", "entity_type": "doc"},
        status=200,
    )
    client = OverleafCookieClient(session2="cookie")

    uploaded = client.upload_file("p1", "root", "main.tex", b"hello")

    assert uploaded.entity_id == "newdoc"
    assert uploaded.entity_type == "doc"
    request = responses.calls[-1].request
    assert request.headers["x-csrf-token"] == "csrf123"
    assert request.headers["Referer"] == "https://www.overleaf.com/project/p1"


@responses.activate
def test_delete_entity_sends_csrf_header():
    responses.get(
        "https://www.overleaf.com/project/p1",
        body='<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>',
        status=200,
    )
    responses.delete("https://www.overleaf.com/project/p1/doc/doc1", status=204)
    client = OverleafCookieClient(session2="cookie")

    client.delete_entity("p1", "doc", "doc1")

    request = responses.calls[-1].request
    assert request.headers["x-csrf-token"] == "csrf123"
