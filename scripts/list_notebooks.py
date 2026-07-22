#!/usr/bin/env python3
"""List notebooks visible on the authenticated NotebookLM account home page."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from browser_api import Page, sync_playwright
from browser_utils import BrowserFactory
from config import STATE_FILE

HOME_URL = "https://notebooklm.google.com"
WELCOME_DISMISS_LABELS = ["Comenzar", "Get started", "Empezar"]
ALL_TAB_LABELS = ["Todos", "All"]
MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "jan": 1, "apr": 4, "aug": 8, "dec": 12,
}


def dismiss_welcome_modal(page: Page) -> None:
    for label in WELCOME_DISMISS_LABELS:
        try:
            button = page.get_by_text(label, exact=True)
            if button.count() > 0:
                button.first.click()
                page.wait_for_timeout(1000)
                return
        except Exception:
            continue


def select_all_tab(page: Page) -> None:
    for label in ALL_TAB_LABELS:
        try:
            tab = page.get_by_text(label, exact=True)
            if tab.count() > 0:
                tab.first.click()
                page.wait_for_timeout(1500)
                return
        except Exception:
            continue


def scroll_to_load_all(page: Page, max_rounds: int = 20) -> None:
    previous = 0
    for _ in range(max_rounds):
        links = page.query_selector_all("a[href*='/notebook/']")
        if len(links) == previous:
            break
        previous = len(links)
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(400)


def extract_notebooks(page: Page) -> List[Dict[str, Any]]:
    notebooks = []
    for link in page.query_selector_all("a[href*='/notebook/']"):
        href = link.get_attribute("href") or ""
        notebook_id = href.split("/notebook/")[-1].split("?")[0]
        title = page.query_selector(f"#project-{notebook_id}-title")
        subtitle = page.query_selector(f"#project-{notebook_id}-subtitle")
        notebooks.append(
            {
                "id": notebook_id,
                "url": f"{HOME_URL}/notebook/{notebook_id}",
                "title": title.inner_text().strip() if title else None,
                "subtitle": subtitle.inner_text().strip() if subtitle else None,
            }
        )
    return notebooks


def parse_date(subtitle: Optional[str]):
    if not subtitle:
        return None
    match = re.search(r"(\d{1,2})\s+(\w{3,})\s+(\d{4})", subtitle)
    if not match:
        return None
    day, month_word, year = match.groups()
    month = MONTHS.get(month_word.lower()[:3])
    if not month:
        return None
    return int(year), month, int(day)


def fetch_notebooks(headless: bool = True) -> List[Dict[str, Any]]:
    if not STATE_FILE.exists():
        raise RuntimeError("Not authenticated. Run: python scripts/run.py auth_manager.py setup")

    with sync_playwright() as playwright:
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        try:
            page = context.new_page()
            page.goto(HOME_URL, wait_until="load", timeout=30000)
            page.wait_for_timeout(2500)
            if "accounts.google.com" in page.url:
                raise RuntimeError("Session expired. Run: python scripts/run.py auth_manager.py reauth")
            dismiss_welcome_modal(page)
            select_all_tab(page)
            page.wait_for_timeout(1500)
            scroll_to_load_all(page)
            return extract_notebooks(page)
        finally:
            context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="List notebooks from NotebookLM")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()

    try:
        notebooks = fetch_notebooks(headless=not args.show_browser)
    except RuntimeError as exc:
        print(f"[X] {exc}")
        return 1

    dated = [(parse_date(notebook["subtitle"]), notebook) for notebook in notebooks]
    dated.sort(key=lambda pair: pair[0] or (0, 0, 0), reverse=True)
    ranked = [notebook for _, notebook in dated][: args.limit]

    if args.json:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
        return 0

    print(f"Found {len(notebooks)} notebooks total. Showing {len(ranked)} most recent:\n")
    for index, notebook in enumerate(ranked, 1):
        print(f"{index}. {notebook['title']}")
        print(f"   {notebook['subtitle']}")
        print(f"   {notebook['url']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
