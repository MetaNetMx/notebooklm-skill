"""Browser launching, persisted auth, and interaction helpers."""

from __future__ import annotations

import json
import os
import random
import shutil
import time
from pathlib import Path
from typing import Optional

from browser_api import BROWSER_BACKEND, BrowserContext, ElementHandle, Page, Playwright
from config import BROWSER_ARGS, BROWSER_PROFILE_DIR, STATE_FILE, USER_AGENT


class BrowserFactory:
    """Create a persistent, locally authenticated browser context."""

    @staticmethod
    def find_browser_executable() -> Optional[str]:
        override = os.environ.get("NOTEBOOKLM_BROWSER_EXECUTABLE")
        if override and Path(override).is_file():
            return override
        for name in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "chrome",
        ):
            found = shutil.which(name)
            if found:
                return found
        return None

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR),
    ) -> BrowserContext:
        args = list(BROWSER_ARGS)
        if os.environ.get("NOTEBOOKLM_DISABLE_CHROME_SANDBOX", "").lower() in {
            "1",
            "true",
            "yes",
        }:
            args.append("--no-sandbox")

        base_kwargs = {
            "user_data_dir": user_data_dir,
            "headless": headless,
            "no_viewport": True,
            "ignore_default_args": ["--enable-automation"],
            "args": args,
        }
        if USER_AGENT:
            base_kwargs["user_agent"] = USER_AGENT

        executable = BrowserFactory.find_browser_executable()
        attempts = []
        override = os.environ.get("NOTEBOOKLM_BROWSER_EXECUTABLE")
        if override:
            attempts.append({"executable_path": override})
        else:
            attempts.append({"channel": "chrome"})
            if executable:
                attempts.append({"executable_path": executable})
            attempts.append({})

        errors = []
        for launch_options in attempts:
            try:
                context = playwright.chromium.launch_persistent_context(
                    **base_kwargs,
                    **launch_options,
                )
                BrowserFactory._inject_cookies(context)
                return context
            except Exception as exc:
                errors.append(str(exc))

        concise_errors = " | ".join(error.splitlines()[0] for error in errors)
        raise RuntimeError(
            f"Could not launch a Chromium browser with {BROWSER_BACKEND}. "
            "Install Chrome/Chromium or set NOTEBOOKLM_BROWSER_EXECUTABLE. "
            f"Attempts: {concise_errors}"
        )

    @staticmethod
    def _inject_cookies(context: BrowserContext) -> None:
        if not STATE_FILE.exists():
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as file:
                state = json.load(file)
            cookies = state.get("cookies", [])
            if cookies:
                context.add_cookies(cookies)
        except (OSError, ValueError, TypeError) as exc:
            print(f"  Warning: could not load browser state: {exc}")


class StealthUtils:
    """Small delays and element interactions that resemble normal typing."""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500) -> None:
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def human_type_element(element: ElementHandle, text: str) -> None:
        element.click()
        for char in text:
            element.type(char, delay=random.uniform(25, 75))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

    @staticmethod
    def human_type(page: Page, selector: str, text: str) -> None:
        element: Optional[ElementHandle] = page.query_selector(selector)
        if not element:
            try:
                element = page.wait_for_selector(selector, timeout=2000)
            except Exception:
                element = None
        if not element:
            raise RuntimeError(f"Element not found for typing: {selector}")
        StealthUtils.human_type_element(element, text)

    @staticmethod
    def realistic_click(page: Page, selector: str) -> None:
        element = page.query_selector(selector)
        if not element:
            raise RuntimeError(f"Element not found for click: {selector}")
        box = element.bounding_box()
        if box:
            page.mouse.move(
                box["x"] + box["width"] / 2,
                box["y"] + box["height"] / 2,
                steps=5,
            )
        StealthUtils.random_delay(100, 300)
        element.click()
        StealthUtils.random_delay(100, 300)
