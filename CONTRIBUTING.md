# Contributing

Thanks for considering a contribution! This is a small, focused project — a Claude Code Skill, not a framework — so the bar for contributing is low on purpose.

## Before you start

- For small fixes (typos, a broken selector, a doc clarification), just open a PR directly.
- For anything bigger (new script, new dependency, behavior change), open an issue first so we can agree on the approach before you put time into it.

## Development setup

```bash
git clone https://github.com/MetaNetMx/notebooklm-skill
cd notebooklm-skill
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m patchright install chrome
```

Then authenticate against your own Google account to test against a real notebook:

```bash
python scripts/auth_manager.py setup
```

(Note: when developing, call scripts directly with the venv's Python instead of through `run.py`, since `run.py` is the *end-user* convenience wrapper.)

## Testing your change

There's no mocked test suite — this project talks to a real Google product via a real browser, and NotebookLM's DOM has changed shape before. So "testing" means:

1. Run the script(s) you touched against your own NotebookLM/Gemini Notebook account.
2. Confirm the *existing* commands still work too (a selector fix for one thing can silently break another).
3. If you touched anything platform-specific (paths, shell activation, browser launch args), say which OS you tested on in the PR — see the PR template.

CI only verifies that dependencies install and scripts are syntactically valid on Windows/macOS/Linux — it does not (and should not) attempt a real Google login headlessly. See [SECURITY.md](SECURITY.md) for why.

## Code style

- Keep it consistent with the surrounding file. This isn't a large codebase — don't introduce a new pattern for something that already has one.
- No new dependencies unless there's a real reason `patchright`/`python-dotenv` don't already cover.
- If you add a script, register it in `scripts/run.py`'s usage list and in `SKILL.md`'s Script Reference — that's how Claude discovers what's callable.

## Reporting bugs vs. asking questions

- Bug in a script → [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).
- "How do I..." → open a regular issue, no template needed.
- Anything involving account security or credential handling → see [SECURITY.md](SECURITY.md) instead of a public issue.
