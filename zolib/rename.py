from pathlib import Path
from typer import Argument, Option, Typer
import re
import sys

from . import app, expand_files, is_zoia_file
DRY_RUN = True


@app.command()
def rename(files: list[Path], *, dry_run: bool = DRY_RUN, force: bool=False) -> None:
    missing, zoia, not_zoia, already_exists = [], [], [], []
    for file in expand_files(files):
        if not is_zoia_file(f):
            not_zoia.append(f)
        elif not file.exists():
            missing.append(f)
        else:
            new_file = file.parent / m.group(1)
            if not force and new_file.exists():
                already_exists.append(new_file)
            else:
                zoia.append((file, new_file))

    if not_zoia:
        print(f"WARNING: not renaming: {not_zoia}", file=sys.stderr)

    errors = []
    if missing:
        errors.append(f"Missing: {missing}")
    if already_exists:
        errors.append(f"Cannot overwrite: {already_exists}. Use -f to replace")
    if not (errors or zoia):
        errors.append("No files to rename")

    if errors:
        sys.exit('\nERROR: '.join(("", *errors)).strip())

    for old, new in zoia:
        print(old, "->", new)
        if not dry_run:
            old.rename(new)
