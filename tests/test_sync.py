import pytest
from helpers import make_zip

from overleaf_cookie_bridge.sync import backup_zip, extract_zip_safely


def test_extract_zip_safely_extracts_normal_files(tmp_path):
    zip_bytes = make_zip({"main.tex": "hello", "sections/intro.tex": "intro"})

    extract_zip_safely(zip_bytes, tmp_path)

    assert (tmp_path / "main.tex").read_text() == "hello"
    assert (tmp_path / "sections" / "intro.tex").read_text() == "intro"


def test_extract_zip_safely_rejects_path_traversal(tmp_path):
    zip_bytes = make_zip({"../evil.txt": "bad"})

    with pytest.raises(ValueError):
        extract_zip_safely(zip_bytes, tmp_path)

    assert not (tmp_path.parent / "evil.txt").exists()


def test_backup_zip_writes_timestamped_file(tmp_path):
    path = backup_zip(b"zip", project_id="p1", backup_root=tmp_path, timestamp="20260517-003000")

    assert path == tmp_path / "p1" / "20260517-003000.zip"
    assert path.read_bytes() == b"zip"
