"""Windows-only OS integration helpers (CLAUDE.md: Windows-only MVP)."""
import ctypes
import uuid
from pathlib import Path

_FOLDERID_DOWNLOADS = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}")


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_uint8 * 8),
    ]


def _guid(value: uuid.UUID) -> _GUID:
    time_low, time_mid, time_hi, clock_hi, clock_low, node = value.fields
    data4 = (ctypes.c_uint8 * 8)(clock_hi, clock_low, *node.to_bytes(6, "big"))
    return _GUID(time_low, time_mid, time_hi, data4)


def downloads_folder() -> Path:
    """The real Windows Downloads folder via SHGetKnownFolderPath (FOLDERID_Downloads),
    not a hardcoded `~/Downloads` guess - respects a user who has relocated it."""
    guid = _guid(_FOLDERID_DOWNLOADS)
    path_ptr = ctypes.c_wchar_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, 0, ctypes.byref(path_ptr))
    if result != 0:
        raise OSError(f"SHGetKnownFolderPath failed: {result}")
    try:
        return Path(path_ptr.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)
