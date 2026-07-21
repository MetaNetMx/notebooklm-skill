# Security Policy

This skill automates a browser session against your real Google account to talk to NotebookLM (Gemini Notebook), so it's worth being explicit about what that means for your data.

## What this skill stores, and where

Everything lives locally, inside `data/` in the skill folder — never anywhere else, never uploaded anywhere:

- `data/browser_state/state.json` — session cookies for notebooklm.google.com
- `data/browser_state/browser_profile/` — a persistent Chrome profile (cache, local storage, persistent cookies)
- `data/auth_info.json` — non-sensitive metadata (timestamps, not credentials)
- `data/library.json` — the notebook names/URLs you've added to your local library

`data/` is excluded from git via `.gitignore`. **Never commit it, zip it up for a bug report, or paste its contents into an issue.** If you're filing a bug and think a log might contain a cookie value or token, redact it first.

## Threat model / what this is and isn't

- This is **not** an official Google product and has no relationship with Google or Anthropic beyond using their public products as a normal browser user would.
- Authentication is a real, interactive Google login — you type your own password into Google's own login page inside a real Chrome window. The skill never sees or stores your password.
- Because this drives a real browser with your real session, treat it the way you'd treat any third-party browser-automation tool with access to a logged-in account: **use a dedicated Google account if you're not comfortable granting that level of trust**, especially before running someone else's fork or an unreviewed PR.
- We deliberately do not run real Google logins in CI (see `.github/workflows/ci.yml`) — automating credentials in a public CI runner is a bad practice we don't want to normalize, even for our own testing.

## Reporting a vulnerability

If you find something that could leak `data/`'s contents, execute arbitrary code via a crafted notebook/webpage, or otherwise compromise a user's Google session beyond what's described above:

- Please **do not** open a public issue with exploit details.
- Open a private [GitHub Security Advisory](../../security/advisories/new) on this repo, or contact the maintainer directly through their GitHub profile.
- Include: what you found, how to reproduce it, and the affected script(s).

We'll do our best to respond promptly — this is a community-maintained fork, not a funded security team, so please be patient.

## Supported versions

Only the latest commit on `master` is supported. There are no maintained release branches.
