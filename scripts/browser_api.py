"""Select the available synchronous browser automation backend.

Patchright is preferred for local installations. Playwright is a supported
fallback for managed or restricted environments where Patchright cannot be
installed but Playwright is already available.
"""

from __future__ import annotations

try:
    from patchright.sync_api import (  # type: ignore
        BrowserContext,
        ElementHandle,
        Page,
        Playwright,
        sync_playwright,
    )

    BROWSER_BACKEND = "patchright"
except ImportError:
    from playwright.sync_api import (  # type: ignore
        BrowserContext,
        ElementHandle,
        Page,
        Playwright,
        sync_playwright,
    )

    BROWSER_BACKEND = "playwright"

__all__ = [
    "BROWSER_BACKEND",
    "BrowserContext",
    "ElementHandle",
    "Page",
    "Playwright",
    "sync_playwright",
]
