#!/usr/bin/env python3
"""
Notebook Discovery for NotebookLM (Gemini Notebook)
Lists every notebook visible on the account's home page, sorted by most recent.

Unlike notebook_manager.py (which manages a local library the user builds by hand),
this script reads the actual "All notebooks" grid from notebooklm.google.com so you
can see what exists on the account without opening a browser yourself.
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from patchright.sync_api import sync_playwright, Page
from config import STATE_FILE
from browser_utils import BrowserFactory

HOME_URL = "https://notebooklm.google.com"

# NotebookLM renamed its UI to "Gemini Notebook" in 2026. The product, URL and
# DOM structure are unchanged, but a one-time welcome modal with a "Comenzar"/
# "Get started" button now appears on first load and blocks the notebook grid.
WELCOME_DISMISS_LABELS = ["Comenzar", "Get started", "Empezar"]

# The home page opens on the "Collections" tab for some accounts, which is
# empty by default. The full grid lives under "All" / "Todos".
ALL_TAB_LABELS = ["Todos", "All"]

MONTHS = {
    # Spanish
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    # English
    "jan": 1, "apr": 4, "aug": 8, "dec": 12,
}


def dismiss_welcome_modal(page: Page) -> None:
    for label in WELCOME_DISMISS_LABELS:
        try:
            btn = page.get_by_text(label, exact=True)
            if btn.count() > 0:
                btn.first.click()
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
    """The grid lazy-loads on scroll; keep scrolling until the count stops growing."""
    previous = 0
    for _ in range(max_rounds):
        links = page.query_selector_all("a[href*='/notebook/']")
        if len(links) == previous:
            break
        previous = len(links)
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(400)


def extract_notebooks(page: Page) -> List[Dict[str, Any]]:
    links = page.query_selector_all("a[href*='/notebook/']")
    notebooks = []
    for link in links:
        href = link.get_attribute("href") or ""
        nb_id = href.split("/notebook/")[-1].split("?")[0]
        title_el = page.query_selector(f"#project-{nb_id}-title")
        subtitle_el = page.query_selector(f"#project-{nb_id}-subtitle")
        notebooks.append({
            "id": nb_id,
            "url": f"{HOME_URL}/notebook/{nb_id}",
            "title": title_el.inner_text().strip() if title_el else None,
            "subtitle": subtitle_el.inner_text().strip() if subtitle_el else None,
        })
    return notebooks


def parse_date(subtitle: Optional[str]):
    """Extract a sortable (year, month, day) tuple from a '21 jul 2026 · N fuentes' style subtitle."""
    if not subtitle:
        return None
    match = re.search(r"(\d{1,2})\s+(\w{3,})\s+(\d{4})", subtitle)
    if not match:
        return None
    day, month_word, year = match.groups()
    month = MONTHS.get(month_word.lower()[:3])
    if not month:
        return None
    return (int(year), month, int(day))


def fetch_notebooks(headless: bool = True) -> List[Dict[str, Any]]:
    if not STATE_FILE.exists():
        raise RuntimeError(
            "Not authenticated. Run: python scripts/run.py auth_manager.py setup"
        )

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)
        try:
            page = context.new_page()
            page.goto(HOME_URL, wait_until="load", timeout=30000)
            page.wait_for_timeout(2500)

            if "accounts.google.com" in page.url:
                raise RuntimeError(
                    "Session expired. Run: python scripts/run.py auth_manager.py reauth"
                )

            dismiss_welcome_modal(page)
            select_all_tab(page)
            page.wait_for_timeout(1500)
            scroll_to_load_all(page)

            return extract_notebooks(page)
        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description="List notebooks from the NotebookLM/Gemini Notebook home page")
    parser.add_argument("--limit", type=int, default=10, help="How many notebooks to show (default: 10)")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a formatted list")
    parser.add_argument("--show-browser", action="store_true", help="Show the browser window (debugging)")
    args = parser.parse_args()

    try:
        notebooks = fetch_notebooks(headless=not args.show_browser)
    except RuntimeError as e:
        print(f"[X] {e}")
        sys.exit(1)

    dated = [(parse_date(nb["subtitle"]), nb) for nb in notebooks]
    dated.sort(key=lambda pair: pair[0] or (0, 0, 0), reverse=True)
    ranked = [nb for _, nb in dated][:args.limit]

    if args.json:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
        return

    print(f"Found {len(notebooks)} notebooks total. Showing the {len(ranked)} most recent:\n")
    for i, nb in enumerate(ranked, 1):
        print(f"{i}. {nb['title']}")
        print(f"   {nb['subtitle']}")
        print(f"   {nb['url']}\n")


if __name__ == "__main__":
    main()
