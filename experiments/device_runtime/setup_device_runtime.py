from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.request
import venv
from pathlib import Path


DEVICE_RUNTIME_DIR = Path(__file__).resolve().parent
DEFAULT_VENV_DIR = DEVICE_RUNTIME_DIR / ".venv"
DEFAULT_MODEL_DIR = DEVICE_RUNTIME_DIR / "models"
REQUIREMENTS_FILE = DEVICE_RUNTIME_DIR / "requirements-device.txt"

MODEL_URLS = {
    "pose_landmarker_lite.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    ),
    "face_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install device_runtime Python dependencies and MediaPipe task models."
    )
    parser.add_argument("--venv-dir", default=str(DEFAULT_VENV_DIR))
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--skip-venv", action="store_true", help="Install into the current Python environment.")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    return parser.parse_args()


def run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.check_call(command)


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_venv(venv_dir: Path) -> Path:
    if not venv_python(venv_dir).exists():
        print(f"Creating virtual environment: {venv_dir}")
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    return venv_python(venv_dir)


def install_requirements(python_exe: Path) -> None:
    if not REQUIREMENTS_FILE.is_file():
        raise FileNotFoundError(f"Missing requirements file: {REQUIREMENTS_FILE}")
    run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python_exe), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def download_file(url: str, destination: Path, force: bool = False) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0 and not force:
        print(f"Model exists, skip: {destination}")
        return

    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    print(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        with temp_path.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    temp_path.replace(destination)
    print(f"Saved: {destination}")


def download_models(model_dir: Path, force: bool = False) -> None:
    for filename, url in MODEL_URLS.items():
        download_file(url, model_dir / filename, force=force)


def main() -> int:
    args = parse_args()
    venv_dir = Path(args.venv_dir).expanduser()
    if not venv_dir.is_absolute():
        venv_dir = (DEVICE_RUNTIME_DIR / venv_dir).resolve()

    model_dir = Path(args.model_dir).expanduser()
    if not model_dir.is_absolute():
        model_dir = (DEVICE_RUNTIME_DIR / model_dir).resolve()

    python_exe = Path(sys.executable) if args.skip_venv else ensure_venv(venv_dir)
    install_requirements(python_exe)

    if not args.skip_models:
        download_models(model_dir, force=args.force_download)

    print("")
    print("Setup complete.")
    print(f"Python: {python_exe}")
    print(f"Models: {model_dir}")
    print("")
    print("Run test:")
    print(f"{python_exe} {DEVICE_RUNTIME_DIR / 'person_usage_device_test.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
