<div align="center">

# NotebookLM Claude Code Skill

**Let [Claude Code](https://github.com/anthropics/claude-code) chat directly with NotebookLM for source-grounded answers based exclusively on your uploaded documents**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://www.anthropic.com/news/skills)
[![Based on](https://img.shields.io/badge/Based%20on-NotebookLM%20MCP-green.svg)](https://github.com/PleasePrompto/notebooklm-mcp)
[![CI](https://github.com/MetaNetMx/notebooklm-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/MetaNetMx/notebooklm-skill/actions/workflows/ci.yml)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-informational)](#platform-specific-setup-notes)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub](https://img.shields.io/github/stars/MetaNetMx/notebooklm-skill?style=social)](https://github.com/MetaNetMx/notebooklm-skill)

> Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Browser automation, library management, persistent auth. Drastically reduced hallucinations - answers only from your uploaded documents.

[Installation](#installation) • [Quick Start](#quick-start) • [Why NotebookLM](#why-notebooklm-not-local-rag) • [How It Works](#how-it-works) • [Contributing](CONTRIBUTING.md) • [MCP Alternative](https://github.com/PleasePrompto/notebooklm-mcp)

</div>

---

## 🍴 About This Fork

This is a fork of [PleasePrompto/notebooklm-skill](https://github.com/PleasePrompto/notebooklm-skill) (all credit for the original design goes there — see [Credits](#credits)). This fork is maintained as a genuinely open, cross-platform project. It adds:

- **Verified cross-platform support** — tested and documented for **Windows, macOS (Intel + Apple Silicon), and Linux**, with per-platform setup notes and CI that installs on all three on every push (see [Platform-Specific Setup Notes](#platform-specific-setup-notes))
- **`list_notebooks.py`** — reads the real "All notebooks" grid straight from the account (no manual add needed) and sorts by most recent, handling the "Gemini Notebook" rebrand's welcome modal automatically
- Notes on Google's 2026 rebrand of NotebookLM to **"Gemini Notebook"** (same product, same URL — just a new name and a one-time welcome dialog)
- Standard open-source scaffolding so it's easy for anyone to contribute: [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md), issue/PR templates, and a lint/install CI workflow
- `.gitattributes` to normalize line endings, so contributions from Windows, macOS, and Linux don't fight each other in diffs

**Contributions are genuinely welcome** — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to get set up and what makes a good PR. If this saves you time, a ⭐ on the repo helps other people find it.

---

## ⚠️ Important: Local Claude Code Only

**This skill works ONLY with local [Claude Code](https://github.com/anthropics/claude-code) installations, NOT in the web UI.**

The web UI runs skills in a sandbox without network access, which this skill requires for browser automation. You must use [Claude Code](https://github.com/anthropics/claude-code) locally on your machine.

---

## The Problem

When you tell [Claude Code](https://github.com/anthropics/claude-code) to "search through my local documentation", here's what happens:
- **Massive token consumption**: Searching through documentation means reading multiple files repeatedly
- **Inaccurate retrieval**: Searches for keywords, misses context and connections between docs
- **Hallucinations**: When it can't find something, it invents plausible-sounding APIs
- **Manual copy-paste**: Switching between NotebookLM browser and your editor constantly

## The Solution

This Claude Code Skill lets [Claude Code](https://github.com/anthropics/claude-code) chat directly with [**NotebookLM**](https://notebooklm.google/) — Google's **source-grounded knowledge base** powered by Gemini 2.5 that provides intelligent, synthesized answers exclusively from your uploaded documents.

```
Your Task → Claude asks NotebookLM → Gemini synthesizes answer → Claude writes correct code
```

**No more copy-paste dance**: Claude asks questions directly and gets answers straight back in the CLI. It builds deep understanding through automatic follow-ups, getting specific implementation details, edge cases, and best practices.

---

## Why NotebookLM, Not Local RAG?

| Approach | Token Cost | Setup Time | Hallucinations | Answer Quality |
|----------|------------|------------|----------------|----------------|
| **Feed docs to Claude** | 🔴 Very high (multiple file reads) | Instant | Yes - fills gaps | Variable retrieval |
| **Web search** | 🟡 Medium | Instant | High - unreliable sources | Hit or miss |
| **Local RAG** | 🟡 Medium-High | Hours (embeddings, chunking) | Medium - retrieval gaps | Depends on setup |
| **NotebookLM Skill** | 🟢 Minimal | 5 minutes | **Minimal** - source-grounded only | Expert synthesis |

### What Makes NotebookLM Superior?

1. **Pre-processed by Gemini**: Upload docs once, get instant expert knowledge
2. **Natural language Q&A**: Not just retrieval — actual understanding and synthesis
3. **Multi-source correlation**: Connects information across 50+ documents
4. **Citation-backed**: Every answer includes source references
5. **No infrastructure**: No vector DBs, embeddings, or chunking strategies needed

---

## Installation

### The simplest installation ever:

```bash
# 1. Create skills directory (if it doesn't exist)
mkdir -p ~/.claude/skills

# 2. Clone this repository
cd ~/.claude/skills
git clone https://github.com/MetaNetMx/notebooklm-skill notebooklm

# 3. That's it! Open Claude Code and say:
"What are my skills?"
```

**Windows users:** if step "installs dependencies automatically" fails or you see a `patchright` import error, jump to [Windows Setup Notes](#windows-setup-notes-fix-for-a-fresh-install) — it's a two-command fix.

When you first use the skill, it automatically:
- Creates an isolated Python environment (`.venv`)
- Installs all dependencies including **Google Chrome**
- Sets up browser automation with Chrome (not Chromium) for maximum reliability
- Everything stays contained in the skill folder

**Note:** The setup uses real Chrome instead of Chromium for cross-platform reliability, consistent browser fingerprinting, and better anti-detection with Google services

---

## Quick Start

### 1. Check your skills

Say in Claude Code:
```
"What skills do I have?"
```

Claude will list your available skills including NotebookLM.

### 2. Authenticate with Google (one-time)

```
"Set up NotebookLM authentication"
```
*A Chrome window opens → log in with your Google account*

> Note: Google renamed NotebookLM's UI to **"Gemini Notebook"** in 2026. It's the same product at the same URL — the only visible change is a one-time "Comenzar"/"Get started" welcome dialog the first time the page loads. The scripts in this skill already dismiss it automatically.

### 3. Create your knowledge base

Go to [notebooklm.google.com](https://notebooklm.google.com) → Create notebook → Upload your docs:
- 📄 PDFs, Google Docs, markdown files
- 🔗 Websites, GitHub repos
- 🎥 YouTube videos
- 📚 Multiple sources per notebook

Share: **⚙️ Share → Anyone with link → Copy**

### 4. Add to your library

**Option A: Let Claude figure it out (Smart Add)**
```
"Query this notebook about its content and add it to my library: [your-link]"
```
Claude will automatically query the notebook to discover its content, then add it with appropriate metadata.

**Option B: Manual add**
```
"Add this NotebookLM to my library: [your-link]"
```
Claude will ask for a name and topics, then save it for future use.

### 5. Start researching

```
"What does my React docs say about hooks?"
```

Claude automatically selects the right notebook and gets the answer directly from NotebookLM.

---

## How It Works

This is a **Claude Code Skill** - a local folder containing instructions and scripts that Claude Code can use when needed. Unlike the [MCP server version](https://github.com/PleasePrompto/notebooklm-mcp), this runs directly in Claude Code without needing a separate server.

### Key Differences from MCP Server

| Feature | This Skill | MCP Server |
|---------|------------|------------|
| **Protocol** | Claude Skills | Model Context Protocol |
| **Installation** | Clone to `~/.claude/skills` | `claude mcp add ...` |
| **Sessions** | Fresh browser each question | Persistent chat sessions |
| **Compatibility** | Claude Code only (local) | Claude Code, Codex, Cursor, etc. |
| **Language** | Python | TypeScript |
| **Distribution** | Git clone | npm package |

### Architecture

```
~/.claude/skills/notebooklm/
├── SKILL.md              # Instructions for Claude
├── scripts/              # Python automation scripts
│   ├── ask_question.py   # Query NotebookLM
│   ├── notebook_manager.py # Library management
│   └── auth_manager.py   # Google authentication
├── .venv/                # Isolated Python environment (auto-created)
└── data/                 # Local notebook library
```

When you mention NotebookLM or send a notebook URL, Claude:
1. Loads the skill instructions
2. Runs the appropriate Python script
3. Opens a browser, asks your question
4. Returns the answer directly to you
5. Uses that knowledge to help with your task

---

## Core Features

### **Source-Grounded Responses**
NotebookLM significantly reduces hallucinations by answering exclusively from your uploaded documents. If information isn't available, it indicates uncertainty rather than inventing content.

### **Direct Integration**
No copy-paste between browser and editor. Claude asks and receives answers programmatically.

### **Smart Library Management**
Save NotebookLM links with tags and descriptions. Claude auto-selects the right notebook for your task.

### **Automatic Authentication**
One-time Google login, then authentication persists across sessions.

### **Self-Contained**
Everything runs in the skill folder with an isolated Python environment. No global installations.

### **Human-Like Automation**
Uses realistic typing speeds and interaction patterns to avoid detection.

---

## Common Commands

| What you say | What happens |
|--------------|--------------|
| *"Set up NotebookLM authentication"* | Opens Chrome for Google login |
| *"Add [link] to my NotebookLM library"* | Saves notebook with metadata |
| *"Show my NotebookLM notebooks"* | Lists all saved notebooks (local library) |
| *"What's the last notebook I created?"* | Reads the real account grid via `list_notebooks.py` and sorts by date |
| *"Ask my API docs about [topic]"* | Queries the relevant notebook |
| *"Use the React notebook"* | Sets active notebook |
| *"Clear NotebookLM data"* | Fresh start (keeps library) |

---

## Real-World Examples

### Example 1: Workshop Manual Query

**User asks**: "Check my Suzuki GSR 600 workshop manual for brake fluid type, engine oil specs, and rear axle torque."

**Claude automatically**:
- Authenticates with NotebookLM
- Asks comprehensive questions about each specification
- Follows up when prompted "Is that ALL you need to know?"
- Provides accurate specifications: DOT 4 brake fluid, SAE 10W-40 oil, 100 N·m rear axle torque

![NotebookLM Chat Example](images/example_notebookchat.png)

### Example 2: Building Without Hallucinations

**You**: "I need to build an n8n workflow for Gmail spam filtering. Use my n8n notebook."

**Claude's internal process:**
```
→ Loads NotebookLM skill
→ Activates n8n notebook
→ Asks comprehensive questions with follow-ups
→ Synthesizes complete answer from multiple queries
```

**Result**: Working workflow on first try, no debugging hallucinated APIs.

---

## Technical Details

### Core Technology
- **Patchright**: Browser automation library (Playwright-based)
- **Python**: Implementation language for this skill
- **Stealth techniques**: Human-like typing and interaction patterns

Note: The MCP server uses the same Patchright library but via TypeScript/npm ecosystem.

### Dependencies
- **patchright==1.55.2**: Browser automation
- **python-dotenv==1.0.0**: Environment configuration
- Automatically installed in `.venv` on first use

### Data Storage

All data is stored locally within the skill directory:

```
~/.claude/skills/notebooklm/data/
├── library.json       - Your notebook library with metadata
├── auth_info.json     - Authentication status info
└── browser_state/     - Browser cookies and session data
```

**Important Security Note:**
- The `data/` directory contains sensitive authentication data and personal notebooks
- It's automatically excluded from git via `.gitignore`
- NEVER manually commit or share the contents of the `data/` directory

### Session Model

Unlike the MCP server, this skill uses a **stateless model**:
- Each question opens a fresh browser
- Asks the question, gets the answer
- Adds a follow-up prompt to encourage Claude to ask more questions
- Closes the browser immediately

This means:
- No persistent chat context
- Each question is independent
- But your notebook library persists
- **Follow-up mechanism**: Each answer includes "Is that ALL you need to know?" to prompt Claude to ask comprehensive follow-ups

For multi-step research, Claude automatically asks follow-up questions when needed.

---

## Limitations

### Skill-Specific
- **Local Claude Code only** - Does not work in web UI (sandbox restrictions)
- **No session persistence** - Each question is independent
- **No follow-up context** - Can't reference "the previous answer"

### NotebookLM
- **Rate limits** - Free tier has daily query limits
- **Manual upload** - You must upload docs to NotebookLM first
- **Share requirement** - Notebooks must be shared publicly

---

## FAQ

**Why doesn't this work in the Claude web UI?**
The web UI runs skills in a sandbox without network access. Browser automation requires network access to reach NotebookLM.

**How is this different from the MCP server?**
This is a simpler, Python-based implementation that runs directly as a Claude Skill. The MCP server is more feature-rich with persistent sessions and works with multiple tools (Codex, Cursor, etc.).

**Can I use both this skill and the MCP server?**
Yes! They serve different purposes. Use the skill for quick Claude Code integration, use the MCP server for persistent sessions and multi-tool support.

**What if Chrome crashes?**
Run: `"Clear NotebookLM browser data"` and try again.

**Is my Google account secure?**
Chrome runs locally on your machine. Your credentials never leave your computer. Use a dedicated Google account if you're concerned.

---

## Troubleshooting

### Skill not found
```bash
# Make sure it's in the right location
ls ~/.claude/skills/notebooklm/
# Should show: SKILL.md, scripts/, etc.
```

### Authentication issues
Say: `"Reset NotebookLM authentication"`

### Browser crashes
Say: `"Clear NotebookLM browser data"`

### Dependencies issues
```bash
# Manual reinstall if needed
cd ~/.claude/skills/notebooklm
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # macOS/Linux — use .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m patchright install chrome
```

### Platform-Specific Setup Notes

`run.py` is meant to set everything up automatically on first use, on any OS. These are the handful of things that occasionally need a manual nudge, by platform.

#### 🍎 macOS (Intel + Apple Silicon)

Setup is usually the smoothest here, but watch for:

- **No `python3` found** — recent macOS versions don't ship Python by default. Install it via [python.org](https://www.python.org/downloads/macos/) or Homebrew: `brew install python@3.12`. Then use `python3` instead of `python` in every command in this README.
- **Gatekeeper prompt on first Chrome launch** — if `patchright install chrome` downloaded a fresh copy of Chrome (rather than reusing one you already had), macOS may show a one-time "Google Chrome.app is an application downloaded from the Internet — are you sure you want to open it?" dialog the very first time a script launches it. Click **Open**. This only happens once.
- **Apple Silicon (M1/M2/M3/M4)** — everything here runs natively (arm64); no Rosetta needed. If you ever see an odd `Bad CPU type in executable` error, it almost always means a stale `.venv` created under a different Python architecture — delete `.venv` and let `run.py` recreate it.
- **`zsh: command not found: python`** — same root cause as the first bullet; use `python3`/`pip3`, or activate the venv (`source .venv/bin/activate`) so plain `python` resolves correctly for the rest of the session.
- Manual dependency reinstall, if needed:
  ```bash
  cd ~/.claude/skills/notebooklm
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python -m patchright install chrome
  ```

#### 🪟 Windows

Two things commonly go wrong the first time, even though `run.py` is supposed to handle setup automatically:

**1. `ModuleNotFoundError: No module named 'patchright'`**

This happens if the `.venv` folder was created (e.g. by an earlier partial run) but the dependency install step didn't finish. Fix it by installing straight into the existing venv:

```powershell
cd ~/.claude/skills/notebooklm
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m patchright install chrome
```

If patchright reports `"chrome" is already installed on the system!`, that's fine — it means Chrome is already available and no further action is needed.

**2. `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f510'`**

Windows' default terminal encoding (cp1252) can't print the emoji these scripts use for status output. Force UTF-8 for the session:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts/run.py auth_manager.py status
```

(Or on Git Bash: `PYTHONIOENCODING=utf-8 python scripts/run.py auth_manager.py status`)

Once authenticated, `auth_manager.py setup` opens a real Chrome window — log in manually there, exactly like on macOS/Linux.

#### 🐧 Linux

Generally works out of the box on any distro with Python 3.8+ and a desktop environment (a real browser window needs somewhere to render — this won't work headless on a server with no display, short of setting up `Xvfb` yourself). If Chrome fails to launch, check for missing system libraries with:

```bash
.venv/bin/python -m patchright install --with-deps chrome
```

`--with-deps` installs the OS-level packages Chrome needs (this may prompt for `sudo`).

---

## Disclaimer

This tool automates browser interactions with NotebookLM to make your workflow more efficient. However, a few friendly reminders:

**About browser automation:**
While I've built in humanization features (realistic typing speeds, natural delays, mouse movements) to make the automation behave more naturally, I can't guarantee Google won't detect or flag automated usage. I recommend using a dedicated Google account for automation rather than your primary account—think of it like web scraping: probably fine, but better safe than sorry!

**About CLI tools and AI agents:**
CLI tools like Claude Code, Codex, and similar AI-powered assistants are incredibly powerful, but they can make mistakes. Please use them with care and awareness:
- Always review changes before committing or deploying
- Test in safe environments first
- Keep backups of important work
- Remember: AI agents are assistants, not infallible oracles

I built this tool for myself because I was tired of the copy-paste dance between NotebookLM and my editor. I'm sharing it in the hope it helps others too, but I can't take responsibility for any issues, data loss, or account problems that might occur. Use at your own discretion and judgment.

That said, if you run into problems or have questions, feel free to open an issue on GitHub. I'm happy to help troubleshoot!

---

## Community & Contributing

This fork exists to make the project easier to pick up regardless of what OS you're on, and easier to contribute to:

- **Found a bug or have an idea?** Open an [issue](https://github.com/MetaNetMx/notebooklm-skill/issues/new/choose) — templates for bug reports and feature requests are set up to ask for exactly what's needed to help you fast.
- **Want to contribute code or docs?** See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and what makes a good PR. First-time contributors welcome — this is a small, readable codebase on purpose.
- **Community standards:** see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- **Security or account-safety concerns:** see [SECURITY.md](SECURITY.md) rather than filing a public issue.
- Every push and PR runs through [CI](https://github.com/MetaNetMx/notebooklm-skill/actions/workflows/ci.yml) that installs dependencies and validates all scripts on **Ubuntu, macOS, and Windows** — so "works on my machine" doesn't quietly turn into "breaks on yours."

---

## Credits

This skill is inspired by my [**NotebookLM MCP Server**](https://github.com/PleasePrompto/notebooklm-mcp) and provides an alternative implementation as a Claude Code Skill:
- Both use Patchright for browser automation (TypeScript for MCP, Python for Skill)
- Skill version runs directly in Claude Code without MCP protocol
- Stateless design optimized for skill architecture

If you need:
- **Persistent sessions** → Use the [MCP Server](https://github.com/PleasePrompto/notebooklm-mcp)
- **Multiple tool support** (Codex, Cursor) → Use the [MCP Server](https://github.com/PleasePrompto/notebooklm-mcp)
- **Quick Claude Code integration** → Use this skill

---

## The Bottom Line

**Without this skill**: NotebookLM in browser → Copy answer → Paste in Claude → Copy next question → Back to browser...

**With this skill**: Claude researches directly → Gets answers instantly → Writes correct code

Stop the copy-paste dance. Start getting accurate, grounded answers directly in Claude Code.

```bash
# Get started in 30 seconds
cd ~/.claude/skills
git clone https://github.com/MetaNetMx/notebooklm-skill notebooklm
# Open Claude Code: "What are my skills?"
```

---

<div align="center">

Built as a Claude Code Skill adaptation of my [NotebookLM MCP Server](https://github.com/PleasePrompto/notebooklm-mcp)

For source-grounded, document-based research directly in Claude Code

</div>
