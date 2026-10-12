"""Relay (WebSocket) connection state. Stub until E4-S3 builds the real client."""


def state() -> str:
    return "disconnected"  # connected | connecting | disconnected


def close() -> None:
    pass
