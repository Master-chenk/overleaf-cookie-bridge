import io
import zipfile

import pytest

from overleaf_cookie_bridge.remote_zip import read_zip_member, zip_member_exists


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_read_zip_member_returns_bytes():
    data = make_zip({"sections/intro.tex": b"hello"})

    assert read_zip_member(data, "sections/intro.tex") == b"hello"


def test_read_zip_member_rejects_missing_path():
    data = make_zip({"main.tex": b"hello"})

    with pytest.raises(FileNotFoundError):
        read_zip_member(data, "missing.tex")


def test_zip_member_exists_checks_path():
    data = make_zip({"main.tex": b"hello"})

    assert zip_member_exists(data, "main.tex")
    assert not zip_member_exists(data, "other.tex")
