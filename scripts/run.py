#!/usr/bin/env python3
"""Run skill scripts inside a compatible Python environment.

A skill-local environment with Patchright is preferred because Google login is
more reliable there. A compatible host Python (usually Playwright in managed
agent runtimes) is used only when local setup cannot be completed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def paths() -> tuple[Path, Path, Path]:
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    python_path = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return skill_dir, venv_dir, python_path


def environment_works(python_path: Path) -> bool:
    if not python_path.exists():
        return False
    skill_dir, _, _ = paths()
    scripts_dir = skill_dir / "scripts"
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(scripts_dir)!r}); "
        "import dotenv, browser_api; "
        "assert browser_api.BROWSER_BACKEND in {'patchright', 'playwright'}"
    )
    result = subprocess.run(
        [str(python_path), "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def browser_backend(python_path: Path) -> str | None:
    if not environment_works(python_path):
        return None
    skill_dir, _, _ = paths()
    scripts_dir = skill_dir / "scripts"
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(scripts_dir)!r}); "
        "import browser_api; print(browser_api.BROWSER_BACKEND)"
    )
    result = subprocess.run(
        [str(python_path), "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def ensure_runtime() -> Path:
    skill_dir, _, venv_python = paths()
    setup_script = skill_dir / "scripts" / "setup_environment.py"

    if environment_works(venv_python):
        return venv_python

    host_python = Path(sys.executable)
    print("Setting up or repairing the skill-local environment...")
    result = subprocess.run([str(host_python), str(setup_script)], check=False)
    if result.returncode == 0 and environment_works(venv_python):
        backend = browser_backend(venv_python)
        print(f"Using skill-local Python ({backend}): {venv_python}")
        return venv_python

    if environment_works(host_python):
        backend = browser_backend(host_python)
        print(f"Using compatible host Python ({backend} fallback): {host_python}")
        return host_python

    print("[X] Failed to set up a supported browser environment")
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run.py <script_name> [args...]")
        raise SystemExit(1)

    script_name = sys.argv[1]
    if script_name.startswith("scripts/"):
        script_name = script_name[8:]
    if not script_name.endswith(".py"):
        script_name += ".py"
    if Path(script_name).name != script_name:
        print("[X] Script name must not contain a path")
        raise SystemExit(2)

    skill_dir, _, _ = paths()
    script_path = skill_dir / "scripts" / script_name
    if not script_path.is_file():
        print(f"[X] Script not found: {script_name}")
        raise SystemExit(1)

    command = [str(ensure_runtime()), str(script_path), *sys.argv[2:]]
    try:
        result = subprocess.run(command, check=False)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
