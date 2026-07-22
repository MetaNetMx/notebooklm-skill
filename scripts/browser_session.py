#!/usr/bin/env python3
"""Low-level persistent NotebookLM browser session support."""

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from browser_api import BrowserContext, Page

sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import StealthUtils


class BrowserSession:
    """Represent one NotebookLM conversation tab inside a browser context."""

    def __init__(self, session_id: str, context: BrowserContext, notebook_url: str):
        self.id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.message_count = 0
        self.notebook_url = notebook_url
        self.context = context
        self.page: Optional[Page] = None
        self.stealth = StealthUtils()
        self._initialize()

    def _initialize(self) -> None:
        print(f"Creating session {self.id}...")
        self.page = self.context.new_page()
        try:
            self.page.goto(self.notebook_url, wait_until="domcontentloaded", timeout=30000)
            if "accounts.google.com" in self.page.url:
                raise RuntimeError("Authentication required. Run auth_manager.py setup first.")
            self._wait_for_ready()
            self.stealth.random_delay(300, 600)
            print(f"Session {self.id} ready")
        except Exception:
            if self.page:
                self.page.close()
            raise

    def _wait_for_ready(self) -> None:
        assert self.page is not None
        selectors = (
            "textarea.query-box-input",
            'textarea[aria-label="Feld für Anfragen"]',
            'textarea[aria-label="Ask a question"]',
            'textarea[aria-label="Haz una pregunta"]',
        )
        for selector in selectors:
            try:
                self.page.wait_for_selector(selector, timeout=5000, state="visible")
                return
            except Exception:
                continue
        raise RuntimeError("NotebookLM query input was not found")

    def _query_selector(self) -> str:
        assert self.page is not None
        selectors = (
            "textarea.query-box-input",
            'textarea[aria-label="Feld für Anfragen"]',
            'textarea[aria-label="Ask a question"]',
            'textarea[aria-label="Haz una pregunta"]',
        )
        for selector in selectors:
            if self.page.query_selector(selector):
                return selector
        raise RuntimeError("NotebookLM query input was not found")

    def ask(self, question: str) -> Dict[str, Any]:
        assert self.page is not None
        try:
            self.last_activity = time.time()
            self.message_count += 1
            previous_answer = self._snapshot_latest_response()
            selector = self._query_selector()
            self.stealth.realistic_click(self.page, selector)
            self.stealth.human_type(self.page, selector, question)
            self.stealth.random_delay(300, 800)
            self.page.keyboard.press("Enter")
            self.stealth.random_delay(1500, 3000)
            answer = self._wait_for_latest_answer(previous_answer)
            if not answer:
                raise RuntimeError("Empty response from NotebookLM")
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "session_id": self.id,
                "notebook_url": self.notebook_url,
            }
        except Exception as exc:
            return {
                "status": "error",
                "question": question,
                "error": str(exc),
                "session_id": self.id,
            }

    def _snapshot_latest_response(self) -> Optional[str]:
        assert self.page is not None
        try:
            responses = self.page.query_selector_all(".to-user-container .message-text-content")
            if responses:
                return responses[-1].inner_text()
        except Exception:
            pass
        return None

    def _wait_for_latest_answer(self, previous_answer: Optional[str], timeout: int = 120) -> str:
        assert self.page is not None
        start_time = time.time()
        last_candidate = None
        stable_count = 0
        while time.time() - start_time < timeout:
            try:
                thinking = self.page.query_selector("div.thinking-message")
                if thinking and thinking.is_visible():
                    time.sleep(0.5)
                    continue
            except Exception:
                pass

            try:
                responses = self.page.query_selector_all(".to-user-container .message-text-content")
                if responses:
                    latest = responses[-1].inner_text().strip()
                    if latest and latest != previous_answer:
                        if latest == last_candidate:
                            stable_count += 1
                            if stable_count >= 3:
                                return latest
                        else:
                            stable_count = 1
                            last_candidate = latest
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError(f"No response received within {timeout} seconds")

    def reset(self) -> int:
        assert self.page is not None
        self.page.reload(wait_until="domcontentloaded")
        self._wait_for_ready()
        previous_count = self.message_count
        self.message_count = 0
        self.last_activity = time.time()
        return previous_count

    def close(self) -> None:
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "age_seconds": time.time() - self.created_at,
            "inactive_seconds": time.time() - self.last_activity,
            "message_count": self.message_count,
            "notebook_url": self.notebook_url,
        }

    def is_expired(self, timeout_seconds: int = 900) -> bool:
        return (time.time() - self.last_activity) > timeout_seconds


if __name__ == "__main__":
    print("Browser Session Module - use ask_question.py for the main interface")
