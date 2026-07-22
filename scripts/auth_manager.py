#!/usr/bin/env python3
"""Authentication manager for NotebookLM.

Authentication is interactive and stores reusable Google session state under
``data/browser_state``. Browser automation is provided by ``browser_api``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict

from browser_api import BrowserContext, Page, sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import BrowserFactory
from config import AUTH_INFO_FILE, BROWSER_STATE_DIR, DATA_DIR, STATE_FILE


GOOGLE_SESSION_COOKIES = {
    "SID",
    "HSID",
    "SSID",
    "APISID",
    "SAPISID",
    "__Secure-1PSID",
    "__Secure-3PSID",
}


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
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            cookies = state.get("cookies", [])
            names = {cookie.get("name") for cookie in cookies if isinstance(cookie, dict)}
            if not names.intersection(GOOGLE_SESSION_COOKIES):
                return False
        except (OSError, ValueError, TypeError):
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

    @staticmethod
    def _has_google_session(context: BrowserContext) -> bool:
        try:
            names = {cookie.get("name") for cookie in context.cookies()}
            return bool(names.intersection(GOOGLE_SESSION_COOKIES))
        except Exception:
            return False

    @classmethod
    def _notebooklm_ready(cls, page: Page, context: BrowserContext) -> bool:
        return (
            page.url.startswith("https://notebooklm.google.com/")
            and "accounts.google.com" not in page.url
            and cls._has_google_session(context)
        )

    def setup_auth(self, headless: bool = False, timeout_minutes: int = 10) -> bool:
        if headless:
            print("Authentication setup requires a visible browser; remove --headless")
            return False

        print("Starting NotebookLM authentication setup...")
        print(f"Waiting up to {timeout_minutes:g} minutes")
        print("A visible browser window must open. Complete Google login there.")
        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=False)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                "https://notebooklm.google.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if self._notebooklm_ready(page, context):
                print("Already authenticated")
                self._save_browser_state(context)
                self._save_auth_info()
                return True

            print("Log in to Google and wait until the NotebookLM home screen appears.")
            deadline = time.monotonic() + timeout_minutes * 60
            while time.monotonic() < deadline:
                if self._notebooklm_ready(page, context):
                    print("Login successful")
                    self._save_browser_state(context)
                    self._save_auth_info()
                    return True
                time.sleep(2)

            print("Authentication timed out before a valid Google session was detected")
            return False
        except Exception as exc:
            print(f"Authentication failed: {exc}")
            print("Run this command from a normal PowerShell window if Codex cannot open desktop applications:")
            print("  python scripts/run.py auth_manager.py setup --timeout 15")
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
            print("No saved Google session was found")
            return False
        print("Validating authentication...")
        playwright = None
        context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=True)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(
                "https://notebooklm.google.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            valid = self._notebooklm_ready(page, context)
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
        authenticated = bool(info["authenticated"])
        print("\nAuthentication Status:")
        print(f"  Authenticated: {'Yes' if authenticated else 'No'}")
        if info.get("state_age_hours") is not None:
            print(f"  State age: {info['state_age_hours']:.1f} hours")
        if info.get("authenticated_at_iso"):
            print(f"  Last auth: {info['authenticated_at_iso']}")
        print(f"  State file: {info['state_file']}")
        if not authenticated:
            print("\nNext required step:")
            print("  python scripts/run.py auth_manager.py setup --timeout 15")
            print("Do not stop at status; authentication requires a visible browser login.")
            return 3
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
