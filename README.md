# PDB Color

Add some color to the python debugger.

Using PDB:

![Code example using PDB](https://raw.githubusercontent.com/alex-gregory-ds/pdbcolor/main/images/before.png)

Using PDB Color:

![Code example using PDB](https://raw.githubusercontent.com/alex-gregory-ds/pdbcolor/main/images/after.png)

## Installation

Install with `pip`.

```shell
pip install pdbcolor
```

## Setup

To use PDB Color, you must set the `PYTHONBREAKPOINT` environment variable to
`pdbcolor.set_trace`. You can do this by setting `PYTHONBREAKPOINT` before your
python command. For example:

```shell
PYTHONBREAKPOINT=pdbcolor.set_trace python3 main.py
```

For convenience, add an alias for the prefix above to your terminal
configuration file (e.g. `.bashrc` or `.zshrc`). For example:

```shell
alias pdc='PYTHONBREAKPOINT=pdbcolor.set_trace'
```

This allows you to use PDB Color as follows:

```shell
pdc python3 main.py
```

You can avoid the prefix entirely by setting the `PYTHONBREAKPOINT` variable in
every terminal session. You can do this in your `.bashrc` with the following:

```shell
export PYTHONBREAKPOINT=pdbcolor.set_trace
```

This can cause unusual behaviour especially when working with `pytest`, so it
is generally recommended to use the `pdc` alias.

## Autocomplete

PDB Color also has autocompletion by default which can be triggered using the
TAB key. For example:

```python
$ python3 main.py
> /home/alex/documents/pdbcolor/main.py(9)<module>()
-> y = 2
(Pdb) str.
str.capitalize(    str.isalpha(       str.ljust(         str.rpartition(
str.casefold(      str.isascii(       str.lower(         str.rsplit(
str.center(        str.isdecimal(     str.lstrip(        str.rstrip(
str.count(         str.isdigit(       str.maketrans(     str.split(
str.encode(        str.isidentifier(  str.mro()          str.splitlines(
str.endswith(      str.islower(       str.partition(     str.startswith(
str.expandtabs(    str.isnumeric(     str.removeprefix(  str.strip(
str.find(          str.isprintable(   str.removesuffix(  str.swapcase(
str.format(        str.isspace(       str.replace(       str.title(
str.format_map(    str.istitle(       str.rfind(         str.translate(
str.index(         str.isupper(       str.rindex(        str.upper(
str.isalnum(       str.join(          str.rjust(         str.zfill(
(Pdb) str.
```

## Post-mortem debugging

PDB can can be triggered post-mortem (after an exception has been raised) with
the following command:

```shell
python3 -m pdb -c continue main.py
```

PDB Color can be used instead by replacing `pdb` with `pdbcolor`.

```shell
python3 -m pdbcolor -c continue main.py
```

## Pytest

To use PDB Color with pytest, use `--pdbcls=pdbcolor:PdbColor`. For example:

```shell
python3 -m pytest --pdbcls=pdbcolor:PdbColor
```

This drops you into PDB Color when a breakpoint is reached.

If you get a pytest OS error such as:

```shell
OSError: pytest: reading from stdin while output is captured!  Consider using `-s`.
```

Using the `-s` flag stops the error but, for those interested, the error is
usually caused by setting `PYTHONBREAKPOINT=pdbcolor.set_trace`. Changing this
back to its default value should stop the error without needing the `-s` flag.
For example:

```shell
PYTHONBREAKPOINT=pdb.set_trace python3 -m pytest --pdbcls=pdbcolor:PdbColor
```
