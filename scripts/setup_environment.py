#!/usr/bin/env python3
"""Create or repair the skill's Python environment.

Patchright is preferred. Playwright is a supported fallback, including managed
agent environments that provide Playwright globally but block package downloads.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Optional


class SkillEnvironment:
    """Manage the skill-local virtual environment and browser backend."""

    def __init__(self) -> None:
        self.skill_dir = Path(__file__).parent.parent
        self.scripts_dir = self.skill_dir / "scripts"
        self.venv_dir = self.skill_dir / ".venv"
        self.requirements_file = self.skill_dir / "requirements.txt"
        if os.name == "nt":
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
            self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"
            self.venv_pip = self.venv_dir / "bin" / "pip"

    @staticmethod
    def _run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(command, check=False, capture_output=capture, text=True)

    @staticmethod
    def _python_has_module(python_executable: Path | str, module: str) -> bool:
        result = SkillEnvironment._run([str(python_executable), "-c", f"import {module}"])
        return result.returncode == 0

    @classmethod
    def _browser_backend(cls, python_executable: Path | str) -> Optional[str]:
        for module in ("patchright", "playwright"):
            if cls._python_has_module(python_executable, module):
                return module
        return None

    @staticmethod
    def _browser_executable() -> Optional[str]:
        override = os.environ.get("NOTEBOOKLM_BROWSER_EXECUTABLE")
        if override and Path(override).is_file():
            return override
        for name in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "chrome",
            "msedge",
        ):
            found = shutil.which(name)
            if found:
                return found

        candidates = []
        if os.name == "nt":
            roots = [
                os.environ.get("PROGRAMFILES"),
                os.environ.get("PROGRAMFILES(X86)"),
                os.environ.get("LOCALAPPDATA"),
            ]
            relative_paths = [
                Path("Google/Chrome/Application/chrome.exe"),
                Path("Microsoft/Edge/Application/msedge.exe"),
                Path("BraveSoftware/Brave-Browser/Application/brave.exe"),
            ]
            candidates.extend(
                Path(root) / relative
                for root in roots
                if root
                for relative in relative_paths
            )
        elif sys.platform == "darwin":
            candidates.extend(
                [
                    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                    Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
                ]
            )
        else:
            candidates.extend(
                [
                    Path("/usr/bin/google-chrome"),
                    Path("/usr/bin/google-chrome-stable"),
                    Path("/usr/bin/chromium"),
                    Path("/usr/bin/chromium-browser"),
                ]
            )

        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None

    def _python_environment_works(self, python_executable: Path | str) -> bool:
        if not Path(python_executable).exists():
            return False
        code = (
            "import sys; "
            f"sys.path.insert(0, {str(self.scripts_dir)!r}); "
            "import dotenv, browser_api; "
            "assert browser_api.BROWSER_BACKEND in {'patchright', 'playwright'}"
        )
        return self._run([str(python_executable), "-c", code]).returncode == 0

    def _environment_works(self) -> bool:
        return self._python_environment_works(self.venv_python)

    def _create_venv(self, *, inherit_system_packages: bool) -> bool:
        if self.venv_dir.exists():
            shutil.rmtree(self.venv_dir)
        try:
            venv.create(
                self.venv_dir,
                with_pip=True,
                system_site_packages=inherit_system_packages,
            )
            mode = " with system packages" if inherit_system_packages else ""
            print(f"Created virtual environment{mode}: {self.venv_dir}")
            return True
        except Exception as exc:
            print(f"[X] Failed to create virtual environment: {exc}")
            return False

    def _ensure_core_dependency(self) -> bool:
        if self._python_has_module(self.venv_python, "dotenv"):
            return True
        if not self.requirements_file.exists():
            print("[X] requirements.txt is missing")
            return False
        result = self._run([str(self.venv_pip), "install", "-r", str(self.requirements_file)])
        if result.returncode == 0 and self._python_has_module(self.venv_python, "dotenv"):
            return True
        print("[X] Could not install core dependencies")
        if result.stderr:
            print(result.stderr.strip())
        return False

    def _ensure_browser_backend(self) -> Optional[str]:
        backend = self._browser_backend(self.venv_python)
        if backend:
            return backend

        for requirement in ("patchright>=1.55,<2", "playwright>=1.55,<2"):
            print(f"Trying browser backend: {requirement}")
            result = self._run([str(self.venv_pip), "install", requirement])
            backend = self._browser_backend(self.venv_python)
            if result.returncode == 0 and backend:
                return backend
        return None

    def _ensure_browser_binary(self, backend: str) -> None:
        executable = self._browser_executable()
        if executable:
            print(f"Using installed browser: {executable}")
            return

        for browser_name in ("chrome", "chromium"):
            result = self._run([str(self.venv_python), "-m", backend, "install", browser_name])
            if result.returncode == 0:
                print(f"Installed {browser_name} through {backend}")
                return
        print(
            "Warning: browser download failed. Install Chrome/Chromium or set "
            "NOTEBOOKLM_BROWSER_EXECUTABLE to its executable path."
        )

    def ensure_venv(self) -> bool:
        # Prefer a local Patchright environment. Playwright remains a valid
        # fallback, but Google login is generally more reliable with Patchright.
        if self._environment_works():
            backend = self._browser_backend(self.venv_python)
            if backend == "patchright":
                return True
            if backend == "playwright":
                print("Existing local environment uses Playwright; trying Patchright upgrade")
                result = self._run([str(self.venv_pip), "install", "patchright>=1.55,<2"])
                if result.returncode == 0 and self._browser_backend(self.venv_python) == "patchright":
                    self._ensure_browser_binary("patchright")
                return self._environment_works()

        host_works = self._python_environment_works(sys.executable)

        # Start isolated so a host Playwright installation does not prevent the
        # preferred Patchright backend from being installed.
        if self._create_venv(inherit_system_packages=False):
            if self._ensure_core_dependency():
                backend = self._ensure_browser_backend()
                if backend:
                    print(f"Browser backend: {backend}")
                    self._ensure_browser_binary(backend)
                    if self._environment_works():
                        return True

        if host_works:
            backend = self._browser_backend(sys.executable) or "unknown"
            print(f"Local setup unavailable; using host {backend} fallback: {sys.executable}")
            return True

        print(
            "[X] No supported browser backend is available. Patchright and "
            "Playwright could not be imported or installed."
        )
        return False

    def is_in_skill_venv(self) -> bool:
        return sys.prefix == str(self.venv_dir)

    def get_python_executable(self) -> str:
        if self._environment_works():
            return str(self.venv_python)
        if self._python_environment_works(sys.executable):
            return sys.executable
        return str(self.venv_python if self.venv_python.exists() else Path(sys.executable))

    def run_script(self, script_name: str, args: Optional[list[str]] = None) -> int:
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            print(f"[X] Script not found: {script_path}")
            return 1
        if not self.ensure_venv():
            return 1
        command = [self.get_python_executable(), str(script_path), *(args or [])]
        return subprocess.run(command, check=False).returncode

    def activate_instructions(self) -> str:
        if os.name == "nt":
            return f"Run: {self.venv_dir / 'Scripts' / 'activate.bat'}"
        return f"Run: source {self.venv_dir / 'bin' / 'activate'}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up NotebookLM skill environment")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run", help="Run a script after setup")
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()

    environment = SkillEnvironment()
    if args.check:
        ready = environment._environment_works() or environment._python_environment_works(sys.executable)
        print(f"Environment ready: {ready}")
        print(f"Python: {environment.get_python_executable()}")
        print(f"System browser backend: {environment._browser_backend(sys.executable) or 'none'}")
        print(f"Browser executable: {environment._browser_executable() or 'not found'}")
        return 0 if ready else 1

    if args.run:
        return environment.run_script(args.run, args.args)

    if not environment.ensure_venv():
        return 1
    print("Environment ready")
    print(f"Python: {environment.get_python_executable()}")
    print(environment.activate_instructions())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
