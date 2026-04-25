from __future__ import annotations

import json
import linecache
import re
import rlcompleter
import sys
import warnings
from dataclasses import dataclass, fields
from pathlib import Path
from pdb import Pdb

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.formatters.terminal import TERMINAL_COLORS
from pygments.lexer import RegexLexer
from pygments.lexers import PythonLexer
from pygments.token import Comment, Generic, Name

ANSIColors = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "purple": 35,
    "cyan": 36,
    "white": 37,
    "Black": 40,
    "Red": 41,
    "Green": 42,
    "Yellow": 43,
    "Blue": 44,
    "Purple": 45,
    "Cyan": 46,
    "White": 47,
}


@dataclass
class Colorscheme:
    breakpoint_: str = "purple"
    currentline: str = "purple"
    line_prefix: str = "purple"
    eof: str = "green"
    path_prefix: str = "green"
    prompt: str = "purple"
    return_: str = "green"

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if value not in ANSIColors:
                raise ValueError(
                    f"Invalid color '{value}' for '{field.name}' in Colorscheme; must be one of: {', '.join(sorted(ANSIColors))}"
                )

    @classmethod
    def from_dict(cls, data: dict) -> Colorscheme:
        if not isinstance(data, dict):
            raise TypeError("Colorscheme data must be a dict")

        known_fields = {f.name for f in fields(cls)}
        unknown_fields = set(data) - known_fields
        if unknown_fields:
            warnings.warn(
                f"Ignoring unknown colorscheme keys: {', '.join(sorted(unknown_fields))}",
                UserWarning,
            )

        for field in set(data) & known_fields:
            colour = data[field]
            if colour not in ANSIColors:
                warnings.warn(
                    f"Invalid color '{colour}' for '{field}' in colorscheme data; must be one of: {', '.join(sorted(ANSIColors))}. Using default color.",
                    UserWarning,
                )

        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @classmethod
    def from_json_file(cls, path: Path | str | None = None) -> Colorscheme:
        if path is None:
            path = Path.home() / ".pdbcolor.json"
        expanded_path = Path(path).expanduser()

        if not expanded_path.exists():
            return cls()

        try:
            with open(expanded_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exception:
            warnings.warn(
                f"Could not load colorscheme from {expanded_path}: {exception}. Using default colors.",
                UserWarning,
            )
            return cls()

        try:
            return cls.from_dict(data)
        except (TypeError, ValueError) as exception:
            warnings.warn(
                f"Invalid colorscheme data in {expanded_path}: {exception}. Using default colors.",
                UserWarning,
            )
            return cls()


def ansi_highlight(text: str, color: str) -> str:
    """Highlight text using ANSI escape characters."""
    start = f"\001\x1b[{ANSIColors[color]}m\002"
    end = "\001\x1b[0m\002"
    return start + text + end


class PdbColor(Pdb):
    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        skip=None,
        nosigint=False,
        readrc=True,
        mode=None,
        backend=None,
        colorize=False,
    ):
        kwargs = {
            "completekey": completekey,
            "stdin": stdin,
            "stdout": stdout,
            "skip": skip,
            "nosigint": nosigint,
            "readrc": readrc,
            "mode": mode,
            "backend": backend,
            "colorize": colorize,
        }
        if sys.version_info < (3, 14):
            print("Success")
            # Remove arguments that are not supported in older Python versions
            kwargs.pop("mode")
            kwargs.pop("backend")
            kwargs.pop("colorize")

        super().__init__(**kwargs)
        self.colors = TERMINAL_COLORS.copy()
        self.colors[Comment] = ("green", "brightgreen")
        self.colorscheme = Colorscheme.from_json_file()

        self.python_lexer = PythonLexer()
        self.path_lexer = PathLexer()
        self.formatter = TerminalFormatter(colorscheme=self.colors)

        self.prompt_str = ansi_highlight(">>", self.colorscheme.prompt)
        self.breakpoint_str = ansi_highlight("B", self.colorscheme.breakpoint_)
        self.currentline_str = ansi_highlight("->", self.colorscheme.currentline)

        self.line_prefix_str = ansi_highlight("->", self.colorscheme.line_prefix)
        self.path_prefix_str = ansi_highlight("> ", self.colorscheme.path_prefix)

        self.eof_str = ansi_highlight("[EOF]", self.colorscheme.eof)
        self.return_str = ansi_highlight("--Return--", self.colorscheme.return_)

        self.code_tag = ":TAG:"
        self.stack_tag = ":STACK:"

    def highlight_code(self, lines: list[str]) -> list[str]:
        """Highlight code and 'tag' to end of each line for easy identification.

        Parameters
        ----------
        lines: list[str]
            Lines of python code.

        Returns
        -------
        list[str]
            Highlighted lines of code.
        """
        # Find the index of the first non-whitespace character
        first = 0
        for i, line in enumerate(lines):
            if not line.isspace():
                first = i
                break

        # Find the index of the last non-whitespace character
        last = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if not lines[i].isspace():
                last = i
                break

        # Pygment's highlight function strips newlines at the start and end.
        # These lines are important so we add them back in later
        highlighted: str = highlight(
            "".join(lines[first : last + 1]), self.python_lexer, self.formatter
        ).splitlines(keepends=True)

        # Add tag to the end of each line to allow code lines to be more easily
        # identified
        highlighted = [line + self.code_tag for line in highlighted]

        return lines[:first] + highlighted + lines[last + 1 :]

    def _print_lines(self, lines: list[str], start: int, breaks=(), frame=None):
        """Print a range of lines.

        Parameters
        ----------
        lines: list[str]
            List of lines to print.
        start: int
            The line number of the first line in 'lines'
        """
        if len(lines) == 0:
            super()._print_lines(lines, start, breaks, frame)
            return

        # Highlight all lines to improve the highlighting accuracy. Highlighting
        # just a few lines can lead to mistakes
        filename = self.curframe.f_code.co_filename
        all_lines = linecache.getlines(filename, self.curframe.f_globals)
        highlighted = self.highlight_code(all_lines)

        # Line numbers start at 0 or 1 depending on the python version. The
        # following helps to ensure line number begins at 1.
        if lines[0] == all_lines[start]:
            # The lines numbers start at 0, force then to start at 1
            super()._print_lines(
                highlighted[start : start + len(lines)], start + 1, breaks, frame
            )
        else:
            # The lines numbers start at 1
            super()._print_lines(
                highlighted[start - 1 : start + len(lines)], start, breaks, frame
            )

    def is_code(self, msg: str) -> bool:
        return msg.endswith(self.code_tag)

    def is_stack(self, msg: str) -> bool:
        return msg.endswith(self.stack_tag)

    def highlight_stack(self, msg: str) -> str:
        """Highlight stack message.

        Stack messages usually contain two lines. The first is the path and the
        second is the current line. For example:

        > /home/documents/pdbcolor/main.py(11)<module>()
        -> if __name__ == "__main__"

        Sometimes, stack messages only contain the current line. This function
        handles both cases.

        Parameters
        ----------
        msg : str
            A stack message.

        Returns
        -------
        str
            Highlighted stack message.
        """
        prefix = self.path_prefix_str if msg[0] == ">" else "  "
        lines = msg.rstrip(self.stack_tag).split("\n")
        if len(lines) == 1:
            path = lines[0]
            current_line = ""
        elif len(lines) == 2:
            path, current_line = lines
            current_line = f"{self.line_prefix_str} {current_line[3:]}"
            path = highlight(path[2:], self.path_lexer, self.formatter)
        else:
            raise RuntimeError("Stacks should have exactly one or two lines.")
        return prefix + path + current_line

    def message(self, msg: str):
        """Highlight and print message to stdout."""
        if self.is_code(msg):
            msg = self.highlight_line_numbers_and_pdb_chars(msg.rstrip(self.code_tag))
        elif self.is_stack(msg):
            msg = self.highlight_stack(msg.rstrip(self.stack_tag))
        elif msg == "--Return--":
            msg = self.return_str
        elif msg == "[EOF]":
            msg = self.eof_str
        super().message(msg.rstrip())

    def highlight_line_numbers_and_pdb_chars(self, code_line: str) -> str:
        """Highlight line numbers and pdb characters in line of code.

        For example, in the following line ' 11  ->  for i in range(10):', The
        line number and current line character '->' will be highlighted.

        Parameters
        ----------
        code_line: str
            Line of code to be highlighted.

        Returns
        -------
        str
            Highlighted line.
        """
        line_number = re.search(r"\d+", code_line)
        if not line_number:
            return code_line

        start, end = line_number.span()
        line_number = ansi_highlight(code_line[start:end], "yellow")

        new_msg = code_line[:start] + line_number
        if code_line[end + 2 : end + 4] == "->":
            new_msg += " " + self.currentline_str + " " + code_line[end + 4 :]
        elif code_line[end + 2] == "B":
            new_msg += " " + self.breakpoint_char + "  " + code_line[end + 4 :]
        else:
            new_msg += code_line[end:]
        return new_msg

    def format_stack_entry(self, frame_lineno, lprefix=": "):
        # Add tag to the end of stack entries to make them easier to identify later
        return super().format_stack_entry(frame_lineno, lprefix) + self.stack_tag

    def onecmd(self, line: str):
        """Override onecmd to handle ? for docstrings.

        Users can append ? to an expression to see its docstring.
        For example: "hello".upper()?
        """
        line = line.strip()
        if line.endswith("?"):
            expression = line[:-1].strip()
            return self.show_docstring(expression)
        else:
            return super().onecmd(line)

    def show_docstring(self, expression: str):
        """Show docstring for an expression.

        Parameters
        ----------
        expression : str
            The expression to evaluate and get docstring for.
        """
        try:
            if not self.curframe:
                self.message("No active frame")
                return None

            # Evaluate the expression in the current frame
            object_ = eval(expression, self.curframe.f_globals, self.curframe.f_locals)

            docstring = object_.__doc__ if hasattr(object_, "__doc__") else None

            if docstring:
                docstring = docstring.strip()
                self.message(docstring)
            else:
                self.message(f"No docstring for '{expression}'")
        except Exception as e:
            self.message(f"Error evaluating '{expression}': {e}")


# Enable tab completion
PdbColor.complete = rlcompleter.Completer().complete


class PathLexer(RegexLexer):
    name = "Path"
    alias = ["path"]
    filenames = ["*"]

    tokens = {
        "root": [
            (r"[^/()]+", Name.Attribute),  # Match everything but '/'
            (r"->", Generic.Subheading),  # Match '/'
            (r"[/()<>]", Generic.Subheading),  # Match '/'
        ]
    }


def set_trace(frame=None):
    debugger = PdbColor()

    # The arguments here are copied from the PDB implementation of 'set_trace'
    debugger.set_trace(sys._getframe().f_back)
