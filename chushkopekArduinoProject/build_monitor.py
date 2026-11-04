"""Build the Chushkopek monitor as a single-file desktop application."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "ChushkopekMonitor",
        str(ROOT / "monitor.py"),
    ],
    cwd=ROOT,
    check=True,
)
