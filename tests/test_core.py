import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from ask_question import validate_notebook_url
from config import BROWSER_ARGS


def test_accepts_notebooklm_notebook_url():
    url = "https://notebooklm.google.com/notebook/example-id"
    assert validate_notebook_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://notebooklm.google.com/notebook/example-id",
        "https://evil.example/notebook/example-id",
        "https://notebooklm.google.com/",
        "https://notebooklm.google.com/notebook/",
    ],
)
def test_rejects_untrusted_or_incomplete_urls(url):
    with pytest.raises(ValueError):
        validate_notebook_url(url)


def test_chrome_sandbox_is_enabled_by_default():
    assert "--no-sandbox" not in BROWSER_ARGS


def test_installer_module_loads():
    path = SCRIPTS / "install_skill.py"
    spec = importlib.util.spec_from_file_location("install_skill", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.default_root("claude").name == "skills"
    assert module.default_root("codex").name == "skills"


def test_browser_backend_is_supported():
    from browser_api import BROWSER_BACKEND

    assert BROWSER_BACKEND in {"patchright", "playwright"}


def test_wrapper_accepts_current_python_runtime():
    import run

    assert run.environment_works(Path(sys.executable))


def test_auth_parser_exposes_ensure_command():
    from auth_manager import build_parser

    args = build_parser().parse_args(["ensure", "--timeout", "15"])
    assert args.command == "ensure"
    assert args.timeout == 15


def test_saved_state_requires_google_session_cookie(tmp_path, monkeypatch):
    import auth_manager

    state_file = tmp_path / "state.json"
    auth_info_file = tmp_path / "auth_info.json"
    browser_state_dir = tmp_path / "browser_state"
    browser_state_dir.mkdir()
    monkeypatch.setattr(auth_manager, "STATE_FILE", state_file)
    monkeypatch.setattr(auth_manager, "AUTH_INFO_FILE", auth_info_file)
    monkeypatch.setattr(auth_manager, "BROWSER_STATE_DIR", browser_state_dir)
    monkeypatch.setattr(auth_manager, "DATA_DIR", tmp_path)

    manager = auth_manager.AuthManager()
    state_file.write_text('{"cookies": [{"name": "NID"}]}', encoding="utf-8")
    assert manager.is_authenticated() is False
    state_file.write_text('{"cookies": [{"name": "SID"}]}', encoding="utf-8")
    assert manager.is_authenticated() is True
