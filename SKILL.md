---
name: notebooklm
description: Query Google NotebookLM notebooks through a local authenticated browser session and return source-grounded answers from the user's uploaded material. Use when the user mentions NotebookLM, provides a notebooklm.google.com/notebook URL, asks to search or question their NotebookLM sources, manage a local notebook library, authenticate NotebookLM, or list notebooks from their account. Designed for local agents with filesystem, Python, browser, and network access, including Claude Code and Codex CLI; browser automation may use Patchright or Playwright.
---

# NotebookLM Research Assistant

Operate NotebookLM through the bundled Python scripts. Treat this as browser automation, not an official Google API.

## Execution rule

Always invoke scripts through the wrapper:

```bash
python scripts/run.py auth_manager.py ensure --timeout 15
python scripts/run.py notebook_manager.py list
python scripts/run.py ask_question.py --question "..."
```

Do not invoke a script directly unless debugging the wrapper itself.

## Workflow

1. Run `python scripts/run.py auth_manager.py ensure --timeout 15`. This command validates an existing session or opens a visible browser for Google login.
2. Do not stop after `status` reports `Authenticated: No`. Continue immediately with `ensure`; authentication is incomplete until the browser login succeeds.
3. Resolve the notebook:
   - Use `--notebook-url` when the user supplies a NotebookLM URL.
   - Use `--notebook-id` for an entry in the local library.
   - Otherwise use the active local notebook.
4. Ask a self-contained question. Each query opens a fresh browser context, so include relevant context in every follow-up.
5. Compare the result with the user's original request and ask additional NotebookLM questions when material facts are missing.
6. Synthesize the retrieved answers. Do not represent visible citation markers as verified structured citations unless they were separately inspected.

## Authentication

```bash
python scripts/run.py auth_manager.py ensure --timeout 15
python scripts/run.py auth_manager.py setup --timeout 15
python scripts/run.py auth_manager.py validate
python scripts/run.py auth_manager.py reauth
python scripts/run.py auth_manager.py clear
```

Authentication data is stored under `data/browser_state/`. It contains reusable Google session cookies. Never print, commit, upload, archive, or expose that directory. Prefer a dedicated Google account for automation.

## Notebook library

```bash
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPIC1,TOPIC2
python scripts/run.py notebook_manager.py search --query KEYWORD
python scripts/run.py notebook_manager.py activate --id NOTEBOOK_ID
python scripts/run.py notebook_manager.py remove --id NOTEBOOK_ID
python scripts/run.py notebook_manager.py stats
```

When metadata is unknown, query the notebook first and derive a specific name, description, and topics from the answer. Do not invent generic metadata.

To inspect notebooks directly from the account grid:

```bash
python scripts/run.py list_notebooks.py
python scripts/run.py list_notebooks.py --limit 5 --json
```

## Query examples

```bash
python scripts/run.py ask_question.py --question "Summarize the supported authentication flow and cite the relevant source names" --notebook-id api-docs
python scripts/run.py ask_question.py --question "What topics and source types does this notebook contain?" --notebook-url "https://notebooklm.google.com/notebook/..."
python scripts/run.py ask_question.py --question "List every documented edge case for invoice reconciliation" --show-browser
```

## Runtime compatibility

Prefer Patchright when it can be installed. Fall back to an existing Playwright installation when Patchright is unavailable, including managed environments with restricted package indexes. The wrapper may use a compatible host Python instead of creating an isolated `.venv`.

Use `auth_manager.py ensure --timeout 15` as the normal entry point. If `status` reports `Authenticated: No`, do not summarize and stop: execute `ensure` immediately. A sandboxed web session cannot complete Google login, but Codex CLI on the user's desktop should open the browser after command approval.

## Installation for local agents

Install the repository into Claude Code, Codex, or both:

```bash
python scripts/install_skill.py --agent claude
python scripts/install_skill.py --agent codex
python scripts/install_skill.py --agent both
```

Use `--force` only when replacing an existing local installation. Codex installs under `$CODEX_HOME/skills/notebooklm` or `~/.codex/skills/notebooklm` when `CODEX_HOME` is unset.

## Security and reliability

- Accept only `https://notebooklm.google.com/notebook/...` notebook URLs.
- Do not make notebooks public merely to use this skill; first use the authenticated private URL.
- Chrome sandboxing remains enabled by default. Set `NOTEBOOKLM_DISABLE_CHROME_SANDBOX=1` only in an environment that requires it and whose isolation is otherwise understood.
- Set `NOTEBOOKLM_BROWSER_EXECUTABLE` when Chrome or Chromium is installed at a nonstandard path.
- The browser DOM can change without notice. Retry with `--show-browser` when selectors fail.
- Do not claim official Google support, guaranteed account safety, guaranteed citation fidelity, or guaranteed immunity from automation detection.
- Review retrieved information before changing code, deploying, or making high-stakes decisions.

## Cleanup

Preview cleanup:

```bash
python scripts/run.py cleanup_manager.py
```

Delete browser and authentication state while preserving the local notebook library:

```bash
python scripts/run.py cleanup_manager.py --confirm --preserve-library
```
