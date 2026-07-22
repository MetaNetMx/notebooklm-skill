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
