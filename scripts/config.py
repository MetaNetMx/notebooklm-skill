"""Shared paths, selectors, and browser configuration."""

import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"
LIBRARY_FILE = DATA_DIR / "library.json"

QUERY_INPUT_SELECTORS = [
    "textarea.query-box-input",
    'textarea[aria-label="Input for queries"]',
    'textarea[aria-label="Feld für Anfragen"]',
    'textarea[aria-label="Campo para consultas"]',
    'textarea[placeholder*="Ask"]',
    'textarea[placeholder*="Pregunta"]',
]

RESPONSE_SELECTORS = [
    ".to-user-container .message-text-content",
    "[data-message-author='bot']",
    "[data-message-author='assistant']",
]

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
]

# Leave unset by default so Chrome reports a platform-consistent user agent.
USER_AGENT = os.environ.get("NOTEBOOKLM_USER_AGENT") or None

LOGIN_TIMEOUT_MINUTES = 10
QUERY_TIMEOUT_SECONDS = 120
PAGE_LOAD_TIMEOUT = 30000
