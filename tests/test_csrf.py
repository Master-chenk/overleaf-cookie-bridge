from overleaf_cookie_bridge.client import parse_csrf_html


def test_parse_csrf_html_extracts_token():
    html = '<html><head><meta name="ol-csrfToken" content="csrf123"></head></html>'

    assert parse_csrf_html(html) == "csrf123"
