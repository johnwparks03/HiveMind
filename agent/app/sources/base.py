"""Source interface. Technical_Blueprint.md section 08 — local filesystem is the only
v1 implementation; a SharePointSource can be added later without touching anything
downstream (indexing, search, publish) as long as it implements this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SourceFile:
    """One file as seen by a Source, before it's registered locally."""
    source_path: str       # Source-specific identifier (a filesystem path for v1)
    filename: str
    created_at: datetime
    modified_at: datetime


class Source(ABC):
    """A place HiveMind can pull indexable files from."""

    @abstractmethod
    def list_files(self) -> list[SourceFile]:
        """Return every file currently available from this source."""

    @abstractmethod
    def get_file_bytes(self, source_path: str) -> bytes:
        """Return the raw bytes of one file, identified by its source_path."""
