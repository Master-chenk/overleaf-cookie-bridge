import io
import zipfile


def _normalize_member_path(path: str) -> str:
    return path.strip("/")


def read_zip_member(zip_bytes: bytes, path: str) -> bytes:
    normalized = _normalize_member_path(path)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        try:
            return zf.read(normalized)
        except KeyError as exc:
            raise FileNotFoundError(f"Path not found in Overleaf zip: {path}") from exc


def zip_member_exists(zip_bytes: bytes, path: str) -> bool:
    normalized = _normalize_member_path(path)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return normalized in zf.namelist()
