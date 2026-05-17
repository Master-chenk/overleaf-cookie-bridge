import zipfile
from datetime import datetime
from pathlib import Path


def default_backup_root() -> Path:
    return Path.home() / ".overleaf-cookie-bridge" / "backups"


def timestamp_now() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_member_path(destination: Path, member_name: str) -> Path:
    destination = destination.resolve()
    target = (destination / member_name).resolve()
    if target != destination and destination not in target.parents:
        raise ValueError(f"Unsafe zip member path: {member_name}")
    return target


def extract_zip_safely(zip_bytes: bytes, destination: str | Path) -> None:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    zip_path = destination.resolve()
    import io

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            _safe_member_path(zip_path, member.filename)
        zf.extractall(zip_path)


def backup_zip(
    zip_bytes: bytes,
    project_id: str,
    backup_root: str | Path | None = None,
    timestamp: str | None = None,
) -> Path:
    root = Path(backup_root) if backup_root is not None else default_backup_root()
    ts = timestamp or timestamp_now()
    project_dir = root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    output = project_dir / f"{ts}.zip"
    output.write_bytes(zip_bytes)
    return output
