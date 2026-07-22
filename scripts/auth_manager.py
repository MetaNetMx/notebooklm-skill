#!/usr/bin/env python3
"""
Authentication Manager for NotebookLM.

Uses the selected browser backend from browser_api. Authentication remains
interactive and stores reusable Google session state under data/browser_state/.
"""

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict

from browser_api import BrowserContext, sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import BrowserFactory
from config import AUTH_INFO_FILE, BROWSER_STATE_DIR, DATA_DIR, STATE_FILE


class AuthManager:
    """Manage interactive Google login and persisted NotebookLM browser state."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.state_file = STATE_FILE
        self.auth_info_file = AUTH_INFO_FILE
        self.browser_state_dir = BROWSER_STATE_DIR

    def is_authenticated(self) -> bool:
        if not self.state_file.exists():
            return False
        age_days = (time.time() - self.state_file.stat().st_mtime) / 86400
        if age_days > 7:
            print(f"Warning: browser state is {age_days:.1f} days old and may require re-authentication")
        return True

    def get_auth_info(self) -> Dict[str, Any]:
        info = {
            "authenticated": self.is_authenticated(),
            "state_file": str(self.state_file),
            "state_exists": self.state_file.exists(),
        }
        if self.auth_info_file.exists():
            try:
                with open(self.auth_info_file, "r", encoding="utf-8") as file:
                    info.update(json.load(file))
            except (OSError, ValueError, TypeError):
                pass
        if info["state_exists"]:
            info["state_age_hours"] = (
                time.time() - self.state_file.stat().st_mtime
            ) / 3600
        return info

    def setup_auth(self, headless: bool = False, timeout_minutes: int = 10) -> bool:
        print("Starting authentication setup...")
        print(f"Timeout: {timeout_minutes} minutes")
        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=headless,
            )
            page = context.new_page()
            page.goto("https://notebooklm.google.com", wait_until="domcontentloaded")

            if "notebooklm.google.com" in page.url and "accounts.google.com" not in page.url:
                print("Already authenticated")
                self._save_browser_state(context)
                self._save_auth_info()
                return True

            print("Please log in to your Google account in the browser window")
            timeout_ms = int(timeout_minutes * 60 * 1000)
            page.wait_for_url(
                re.compile(r"^https://notebooklm\.google\.com/"),
                timeout=timeout_ms,
            )
            print("Login successful")
            self._save_browser_state(context)
            self._save_auth_info()
            return True
        except Exception as exc:
            print(f"Authentication failed: {exc}")
            return False
        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass

    def _save_browser_state(self, context: BrowserContext) -> None:
        context.storage_state(path=str(self.state_file))
        print(f"Saved browser state to: {self.state_file}")

    def _save_auth_info(self) -> None:
        try:
            info = {
                "authenticated_at": time.time(),
                "authenticated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(self.auth_info_file, "w", encoding="utf-8") as file:
                json.dump(info, file, indent=2)
        except OSError:
            pass

    def clear_auth(self) -> bool:
        print("Clearing authentication data...")
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            if self.auth_info_file.exists():
                self.auth_info_file.unlink()
            if self.browser_state_dir.exists():
                shutil.rmtree(self.browser_state_dir)
                self.browser_state_dir.mkdir(parents=True, exist_ok=True)
            print("Authentication data cleared")
            return True
        except OSError as exc:
            print(f"Error clearing authentication: {exc}")
            return False

    def re_auth(self, headless: bool = False, timeout_minutes: int = 10) -> bool:
        self.clear_auth()
        return self.setup_auth(headless, timeout_minutes)

    def validate_auth(self) -> bool:
        if not self.is_authenticated():
            return False
        print("Validating authentication...")
        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=True)
            page = context.new_page()
            page.goto(
                "https://notebooklm.google.com",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            valid = (
                "notebooklm.google.com" in page.url
                and "accounts.google.com" not in page.url
            )
            print("Authentication is valid" if valid else "Authentication is invalid")
            return valid
        except Exception as exc:
            print(f"Validation failed: {exc}")
            return False
        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage NotebookLM authentication")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    setup_parser = subparsers.add_parser("setup", help="Set up authentication")
    setup_parser.add_argument("--headless", action="store_true")
    setup_parser.add_argument("--timeout", type=float, default=10)

    subparsers.add_parser("status", help="Check authentication status")
    subparsers.add_parser("validate", help="Validate authentication")
    subparsers.add_parser("clear", help="Clear authentication")

    reauth_parser = subparsers.add_parser("reauth", help="Clear and authenticate again")
    reauth_parser.add_argument("--timeout", type=float, default=10)

    args = parser.parse_args()
    auth = AuthManager()

    if args.command == "setup":
        return 0 if auth.setup_auth(args.headless, args.timeout) else 1
    if args.command == "status":
        info = auth.get_auth_info()
        print("\nAuthentication Status:")
        print(f"  Authenticated: {'Yes' if info['authenticated'] else 'No'}")
        if info.get("state_age_hours") is not None:
            print(f"  State age: {info['state_age_hours']:.1f} hours")
        if info.get("authenticated_at_iso"):
            print(f"  Last auth: {info['authenticated_at_iso']}")
        print(f"  State file: {info['state_file']}")
        return 0
    if args.command == "validate":
        return 0 if auth.validate_auth() else 1
    if args.command == "clear":
        return 0 if auth.clear_auth() else 1
    if args.command == "reauth":
        return 0 if auth.re_auth(timeout_minutes=args.timeout) else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
