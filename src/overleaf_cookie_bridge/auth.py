import os
import re

import requests

_SECRET_PATTERNS = [
    re.compile(r"(overleaf_session2=)[^;\s]+", re.IGNORECASE),
    re.compile(r"(OVERLEAF_SESSION2=)[^;\s]+"),
    re.compile(r"(Cookie:\s*)[^\n\r]+", re.IGNORECASE),
]


def get_session2_from_env() -> str | None:
    value = os.environ.get("OVERLEAF_SESSION2")
    if not value:
        return None
    return value.strip() or None


def redact_secrets(text: str) -> str:
    redacted = text
    redacted = re.sub(
        r"(overleaf_session2=)[^;\s]+",
        r"\1<redacted>",
        redacted,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(r"(OVERLEAF_SESSION2=)[^;\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(
        r"(Cookie:\s*)(?!.*overleaf_session2=)[^\n\r]+",
        r"\1<redacted>",
        redacted,
        flags=re.IGNORECASE,
    )
    return redacted


def cookie_domain_for_host(host: str) -> str:
    normalized = host.strip().removeprefix("https://").removeprefix("http://").split("/", 1)[0]
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return "." + normalized


def make_session(session2: str, host: str = "www.overleaf.com") -> requests.Session:
    if not session2:
        raise ValueError("session2 cookie is required")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "overleaf-cookie-bridge/0.1 (+https://github.com/jkulhanek/pyoverleaf-compatible)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    session.cookies.set(
        "overleaf_session2",
        session2,
        domain=cookie_domain_for_host(host),
        path="/",
    )
    return session
