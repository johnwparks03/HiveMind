"""Builds infra/layer/python with Linux (manylinux) wheels of psycopg2-binary so the
Lambda layer works when synthesizing from Windows without Docker. Run before
`cdk diff` / `cdk deploy`:  python build_layer.py"""
import shutil
import subprocess
import sys
from pathlib import Path

LAYER_DIR = Path(__file__).parent / "layer"
TARGET = LAYER_DIR / "python"
PACKAGES = ["psycopg2-binary>=2.9.9"]


def main() -> None:
    shutil.rmtree(LAYER_DIR, ignore_errors=True)
    TARGET.mkdir(parents=True)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", *PACKAGES,
        "--target", str(TARGET),
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", "3.12",
        "--only-binary=:all:",
    ])


if __name__ == "__main__":
    main()
