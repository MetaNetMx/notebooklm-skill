#!/usr/bin/env python3
"""Install this repository as a local Claude Code or Codex skill."""

import argparse
import os
import shutil
from pathlib import Path

EXCLUDES = {".git", ".venv", "data", "__pycache__", ".pytest_cache"}


def default_root(agent: str) -> Path:
    if agent == "claude":
        return Path.home() / ".claude" / "skills"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills"


def ignore(_, names):
    return [name for name in names if name in EXCLUDES or name.endswith(".pyc")]


def install(agent: str, name: str, force: bool) -> Path:
    source = Path(__file__).resolve().parent.parent
    target = default_root(agent) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not force:
            raise FileExistsError(f"{target} already exists; rerun with --force")
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=ignore)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["claude", "codex", "both"], default="both")
    parser.add_argument("--name", default="notebooklm")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    agents = ["claude", "codex"] if args.agent == "both" else [args.agent]
    try:
        for agent in agents:
            print(f"Installed {agent}: {install(agent, args.name, args.force)}")
    except (OSError, FileExistsError) as exc:
        print(f"[X] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
