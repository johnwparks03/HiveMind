"""Native Windows folder dialog for POST /folders/pick (API_Contract 2.3, story E0-S4).

The dialog runs in its own short-lived process. tkinter does not like running in a worker thread
alongside the server, and a separate process also means a stuck dialog can't stall the agent.
Cancelling returns None, which the endpoint reports as {"path": null}, not as an error.
"""
import subprocess
import sys

# Runs in the child process. Prints the chosen folder, or nothing when cancelled.
_DIALOG = r"""
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
# Topmost, so the dialog doesn't open behind the browser (E0-S4 known risk).
root.attributes("-topmost", True)
root.update()
path = filedialog.askdirectory(parent=root, title="Choose a folder for HiveMind")
root.destroy()
if path:
    print(path)
"""


def pick_folder() -> str | None:
    completed = subprocess.run(
        [sys.executable, "-c", _DIALOG],
        capture_output=True,
        text=True,
        check=False,
    )
    path = completed.stdout.strip()
    return path or None
