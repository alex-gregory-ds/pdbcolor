import subprocess
import sys
from pathlib import Path

import pytest


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
