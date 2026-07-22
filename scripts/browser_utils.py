"""Browser launching, persisted auth, and interaction helpers."""

import json
import os
import random
import time
from typing import Optional

from patchright.sync_api import BrowserContext, ElementHandle, Page, Playwright

from config import BROWSER_ARGS, BROWSER_PROFILE_DIR, STATE_FILE, USER_AGENT


class BrowserFactory:
    """Create a persistent, locally authenticated Chrome context."""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR),
    ) -> BrowserContext:
        args = list(BROWSER_ARGS)
        if os.environ.get("NOTEBOOKLM_DISABLE_CHROME_SANDBOX", "").lower() in {"1", "true", "yes"}:
            args.append("--no-sandbox")

        kwargs = {
            "user_data_dir": user_data_dir,
            "channel": "chrome",
            "headless": headless,
            "no_viewport": True,
            "ignore_default_args": ["--enable-automation"],
            "args": args,
        }
        if USER_AGENT:
            kwargs["user_agent"] = USER_AGENT

        context = playwright.chromium.launch_persistent_context(**kwargs)
        BrowserFactory._inject_cookies(context)
        return context

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
