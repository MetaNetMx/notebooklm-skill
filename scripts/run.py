#!/usr/bin/env python3
"""Run skill scripts inside a self-managed virtual environment."""

import os
import subprocess
import sys
from pathlib import Path


def paths():
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    python_path = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return skill_dir, venv_dir, python_path


def environment_works(python_path: Path) -> bool:
    if not python_path.exists():
        return False
    result = subprocess.run(
        [str(python_path), "-c", "import patchright, dotenv"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def ensure_venv() -> Path:
    skill_dir, venv_dir, python_path = paths()
    setup_script = skill_dir / "scripts" / "setup_environment.py"
    if not environment_works(python_path):
        print("Setting up or repairing the skill environment...")
        result = subprocess.run([sys.executable, str(setup_script)])
        if result.returncode != 0 or not environment_works(python_path):
            print("[X] Failed to set up the environment")
            sys.exit(1)
    return python_path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run.py <script_name> [args...]")
        sys.exit(1)

    script_name = sys.argv[1]
    if script_name.startswith("scripts/"):
        script_name = script_name[8:]
    if not script_name.endswith(".py"):
        script_name += ".py"
    if Path(script_name).name != script_name:
        print("[X] Script name must not contain a path")
        sys.exit(2)

    skill_dir, _, _ = paths()
    script_path = skill_dir / "scripts" / script_name
    if not script_path.is_file():
        print(f"[X] Script not found: {script_name}")
        sys.exit(1)

    command = [str(ensure_venv()), str(script_path), *sys.argv[2:]]
    try:
        result = subprocess.run(command)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
