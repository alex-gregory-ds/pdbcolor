"""This module serves as the entry point for the pdbcolor package when invoked
as a script. For example when pdbcolor is invoked as follows:

    python -m pdbcolor main.py
"""

if __name__ == "__main__":
    import pdb

    from pdbcolor import PdbColor

    # The `main` function creates an instance of `pdb.Pdb` and starts the
    # debugging session. By pointing `pdb.Pdb` to `PdbColor`, we ensure that the
    # colorized version of the debugger is used.
    pdb.Pdb = PdbColor
    pdb.main()
