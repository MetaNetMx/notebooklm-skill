# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-07-21 (fork: MetaNetMx/notebooklm-skill)

### Added
- **`list_notebooks.py`** - New script that reads the real "All notebooks" grid directly from the account (no manual `add` step needed), sorted by most recent first. Registered in `run.py`'s script list.
- **Windows Setup Notes** in README - documents the two most common fresh-install failures on Windows (missing `patchright` after a partial venv setup, and a `UnicodeEncodeError` from emoji output on the default cp1252 console encoding) with copy-paste fixes.
- Documentation of Google's 2026 rebrand of NotebookLM to **"Gemini Notebook"** - same product/URL, but a one-time welcome modal now appears and is handled automatically by `list_notebooks.py`.

## [1.3.0] - 2025-11-21

### Added
- **Modular Architecture** - Refactored codebase for better maintainability
  - New `config.py` - Centralized configuration (paths, selectors, timeouts)
  - New `browser_utils.py` - BrowserFactory and StealthUtils classes
  - Cleaner separation of concerns across all scripts

### Changed
- **Timeout increased to 120 seconds** - Long queries no longer timeout prematurely
  - `ask_question.py`: 30s → 120s
  - `browser_session.py`: 30s → 120s
  - Resolves Issue #4

### Fixed
- **Thinking Message Detection** - Fixed incomplete answers showing placeholder text
  - Now waits for `div.thinking-message` element to disappear before reading answer
  - Answers like "Reviewing the content..." or "Looking for answers..." no longer returned prematurely
  - Works reliably across all languages and NotebookLM UI changes

- **Correct CSS Selectors** - Updated to match current NotebookLM UI
  - Changed from `.response-content, .message-content` to `.to-user-container .message-text-content`
  - Consistent selectors across all scripts

- **Stability Detection** - Improved answer completeness check
  - Now requires 3 consecutive stable polls instead of 1 second wait
  - Prevents truncated responses during streaming

## [1.2.0] - 2025-10-28

### Added
- Initial public release
- NotebookLM integration via browser automation
- Session-based conversations with Gemini 2.5
- Notebook library management
- Knowledge base preparation tools
- Google authentication with persistent sessions
