#!/usr/bin/env python3
"""Query a NotebookLM notebook through a local authenticated Chrome session."""

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from config import QUERY_INPUT_SELECTORS, RESPONSE_SELECTORS
from browser_utils import BrowserFactory, StealthUtils

FOLLOW_UP_REMINDER = (
    "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? "
    "Before replying to the user, compare this answer with the original request. "
    "If anything is missing, ask another self-contained question because each "
    "NotebookLM query starts a new browser session."
)


def validate_notebook_url(url: str) -> str:
    """Accept only HTTPS NotebookLM notebook URLs."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "notebooklm.google.com":
        raise ValueError("Notebook URL must use https://notebooklm.google.com/notebook/...")
    if not re.match(r"^/notebook/[^/?#]+", parsed.path):
        raise ValueError("URL does not identify a NotebookLM notebook")
    return url


def _is_login_url(url: str) -> bool:
    return "accounts.google.com" in url


def ask_notebooklm(question: str, notebook_url: str, headless: bool = True) -> Optional[str]:
    """Ask NotebookLM one self-contained question and return the visible answer."""
    if not question.strip():
        raise ValueError("Question cannot be empty")
    notebook_url = validate_notebook_url(notebook_url)

    auth = AuthManager()
    if not auth.is_authenticated():
        print("[X] Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        return None

    print(f"Asking: {question}")
    print(f"Notebook: {notebook_url}")

    playwright = None
    context = None
    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        page = context.new_page()
        print("  Opening notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded", timeout=30000)

        if _is_login_url(page.url):
            print("  [X] Google session expired. Run auth_manager.py reauth")
            return None

        page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=15000)

        print("  Waiting for query input...")
        query_element = None
        matched_selector = None
        for selector in QUERY_INPUT_SELECTORS:
            try:
                query_element = page.wait_for_selector(selector, timeout=5000, state="visible")
                if query_element:
                    matched_selector = selector
                    break
            except Exception:
                continue

        if not query_element or not matched_selector:
            print("  [X] Could not find query input. Retry with --show-browser.")
            return None

        print(f"  Found input: {matched_selector}")
        StealthUtils.human_type_element(query_element, question)
        page.keyboard.press("Enter")
        StealthUtils.random_delay(500, 1500)

        print("  Waiting for answer...")
        answer = None
        stable_count = 0
        last_text = None
        deadline = time.time() + 120

        while time.time() < deadline:
            if _is_login_url(page.url):
                print("  [X] Session expired while querying NotebookLM")
                return None

            try:
                thinking = page.query_selector("div.thinking-message")
                if thinking and thinking.is_visible():
                    time.sleep(1)
                    continue
            except Exception:
                pass

            for selector in RESPONSE_SELECTORS:
                try:
                    elements = page.query_selector_all(selector)
                    if not elements:
                        continue
                    text = elements[-1].inner_text().strip()
                    if not text:
                        continue
                    if text == last_text:
                        stable_count += 1
                        if stable_count >= 3:
                            answer = text
                            break
                    else:
                        stable_count = 0
                        last_text = text
                except Exception:
                    continue

            if answer:
                break
            time.sleep(1)

        if not answer:
            print("  [X] Timeout waiting for answer")
            return None

        print("  Answer received")
        return answer + FOLLOW_UP_REMINDER
    except Exception as exc:
        print(f"  [X] Error: {exc}")
        return None
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
    parser = argparse.ArgumentParser(description="Ask NotebookLM a question")
    parser.add_argument("--question", required=True)
    parser.add_argument("--notebook-url")
    parser.add_argument("--notebook-id")
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()

    library = NotebookLibrary()
    notebook_url = args.notebook_url
    used_notebook_id = None

    if not notebook_url and args.notebook_id:
        notebook = library.get_notebook(args.notebook_id)
        if not notebook:
            print(f"[X] Notebook '{args.notebook_id}' not found")
            return 1
        notebook_url = notebook["url"]
        used_notebook_id = args.notebook_id

    if not notebook_url:
        active = library.get_active_notebook()
        if active:
            notebook_url = active["url"]
            used_notebook_id = active["id"]
            print(f"Using active notebook: {active['name']}")
        else:
            print("[X] No notebook selected. Supply --notebook-url or --notebook-id.")
            return 1

    try:
        answer = ask_notebooklm(args.question, notebook_url, headless=not args.show_browser)
    except ValueError as exc:
        print(f"[X] {exc}")
        return 2

    if not answer:
        print("\n[X] Failed to get answer")
        return 1

    if used_notebook_id:
        library.increment_use_count(used_notebook_id)

    print("\n" + "=" * 60)
    print(f"Question: {args.question}")
    print("=" * 60 + "\n")
    print(answer)
    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
