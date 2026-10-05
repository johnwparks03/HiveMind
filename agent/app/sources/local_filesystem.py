"""The only v1 Source implementation. Recursive, filtered to SUPPORTED_EXTENSIONS."""
from datetime import datetime
from pathlib import Path

from app.config import SUPPORTED_EXTENSIONS
from app.sources.base import Source, SourceFile


class LocalFilesystemSource(Source):
    def __init__(self, root: str):
        self.root = Path(root)

    def list_files(self) -> list[SourceFile]:
        if not self.root.exists():
            return []
        out = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            stat = path.stat()
            out.append(
                SourceFile(
                    source_path=str(path),
                    filename=path.name,
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )
            )
        return out

    def get_file_bytes(self, source_path: str) -> bytes:
        return Path(source_path).read_bytes()
