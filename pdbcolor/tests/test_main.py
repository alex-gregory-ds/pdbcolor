import json
import subprocess
import sys
from pathlib import Path

import pytest

from pdbcolor import Colorscheme


@pytest.fixture
def script_with_runtime_error(tmp_path: Path) -> Path:
    file_path = tmp_path / "file_with_runtime_error.py"
    file_path.write_text("raise RuntimeError('This is a runtime error.')")
    return file_path


def test_missing_file_prints_error_and_exits_1():
    """Check that invoking the debugger an a non-existent exits with code 1."""
    output = subprocess.run(
        [sys.executable, "-m", "pdb", "script_that_does_not_exist.py"],
        capture_output=True,
        text=True,
    )
    assert output.returncode == 1
    assert "does not exist" in output.stdout


def test_post_mortem_debugging_uses_pdbcolor(script_with_runtime_error: Path):
    """Check that post-mortem debugging uses pdbcolor and not pdb."""
    output = subprocess.run(
        [
            sys.executable,
            "-m",
            "pdbcolor",
            "-c",
            "continue",
            str(script_with_runtime_error),
        ],
        capture_output=True,
        text=True,
        timeout=5,  # Prevent hanging if the debugger doesn't exit as expected
    )
    assert output.returncode == 0
    assert "This is a runtime error." in output.stdout
    assert "(Pdb)" in output.stdout
    assert "Entering post mortem debugging" in output.stdout

    # Check that the output contains ANSI escape codes, which indicates that
    # colorization is working. This does not check for specific colors to keep
    # the test resilient to color scheme changes
    assert "\x1b" in output.stdout


def test_colorscheme_from_home_json(tmp_path: Path, monkeypatch):
    config_data = {
        "pdb": "red",
        "prompt": "blue",
        "breakpoint_": "yellow",
        "currentline": "green",
    }
    config_file = tmp_path / ".pdbcolor.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))

    scheme = Colorscheme.from_json_file()
    assert scheme.pdb == "red"
    assert scheme.prompt == "blue"
    assert scheme.breakpoint_ == "yellow"
    assert scheme.currentline == "green"


def test_colorscheme_invalid_color(tmp_path: Path, monkeypatch):
    """Check that an invalid color in the config file falls back to the default color."""
    config_data = {
        "pdb": "invalid_color",
        "prompt": "blue",
        "breakpoint_": "yellow",
        "currentline": "green",
    }
    config_file = tmp_path / ".pdbcolor.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.warns(UserWarning):
        scheme = Colorscheme.from_json_file()

    assert scheme.pdb == "purple"


def test_colorscheme_unknown_config_key(tmp_path: Path, monkeypatch):
    """Check that unknown keys in the config file are ignored with a warning."""
    config_data = {
        "pdb": "red",
        "prompt": "blue",
        "breakpoint_": "yellow",
        "currentline": "green",
        "unknown_key": "some_value",
    }
    config_file = tmp_path / ".pdbcolor.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.warns(UserWarning):
        scheme = Colorscheme.from_json_file()

    assert scheme.pdb == "red"
    assert scheme.prompt == "blue"
    assert scheme.breakpoint_ == "yellow"
    assert scheme.currentline == "green"
