"""Temporary ZIP creation for Download All. Media is stored, never recompressed."""

from __future__ import annotations

import zipfile
from pathlib import Path


def build_archive(files: list[tuple[Path, str]], archive_path: Path) -> int:
    """Write ``files`` (path, arcname) into an uncompressed ZIP. Returns bytes written."""
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for path, arcname in files:
            zf.write(path, arcname=arcname)
    return archive_path.stat().st_size
