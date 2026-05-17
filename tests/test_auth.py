

from overleaf_cookie_bridge.auth import (
    get_session2_from_env,
    make_session,
    redact_secrets,
)


def test_get_session2_from_env_prefers_overleaf_session2(monkeypatch):
    monkeypatch.setenv("OVERLEAF_SESSION2", "s%3Aabc.secret")

    assert get_session2_from_env() == "s%3Aabc.secret"


def test_get_session2_from_env_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("OVERLEAF_SESSION2", raising=False)

    assert get_session2_from_env() is None


def test_make_session_sets_cookie_for_overleaf_domain():
    session = make_session("cookie-value", host="www.overleaf.com")

    cookie_header = session.cookies.get_dict(domain=".overleaf.com")

    assert cookie_header["overleaf_session2"] == "cookie-value"


def test_redact_secrets_removes_cookie_values():
    text = "Cookie: overleaf_session2=s%3Aabc.secret; other=x and OVERLEAF_SESSION2=s%3Aabc.secret"

    redacted = redact_secrets(text)

    assert "s%3Aabc.secret" not in redacted
    assert "overleaf_session2=<redacted>" in redacted
    assert "OVERLEAF_SESSION2=<redacted>" in redacted
