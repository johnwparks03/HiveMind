import time


def wait_for_scan(client, folder_id, timeout=30.0):
    """POST /folders returns before its scan finishes. Waits until the folder leaves 'scanning'
    and returns its row (scan_state 'ready' or 'failed')."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        folder = next(f for f in client.get("/folders").json()["folders"] if f["folder_id"] == folder_id)
        if folder["scan_state"] != "scanning":
            return folder
        time.sleep(0.02)
    raise AssertionError("scan did not finish in time")


def add_folder_and_wait(client, path):
    folder_id = client.post("/folders", json={"path": str(path)}).json()["folder_id"]
    wait_for_scan(client, folder_id)
    return folder_id

