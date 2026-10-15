"""Builds the Lambda layers with Linux (manylinux) wheels so they work when synthesizing from
Windows without Docker. Run before `cdk diff` / `cdk deploy`:  python build_layer.py

  layer/python       psycopg2-binary, for the VPC Lambdas that talk to Postgres
  auth_layer/python  PyJWT + cryptography, for the WebSocket authorizer (E4-S1)
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
LAYERS = {
    "layer": ["psycopg2-binary>=2.9.9"],
    "auth_layer": ["PyJWT[crypto]>=2.8.0"],
}


def build(layer_name: str, packages: list[str]) -> None:
    layer_dir = HERE / layer_name
    target = layer_dir / "python"
    shutil.rmtree(layer_dir, ignore_errors=True)
    target.mkdir(parents=True)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", *packages,
        "--target", str(target),
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", "3.12",
        "--only-binary=:all:",
    ])


def main() -> None:
    for layer_name, packages in LAYERS.items():
        build(layer_name, packages)


if __name__ == "__main__":
    main()
