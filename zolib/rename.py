from pathlib import Path
from typer import Argument, Option, Typer
import re
import sys

from . import app, DRY_RUN, expand_files, split_file


@app.command()
def rename(
    files: list[Path],
    dry_run: bool = Option(
        DRY_RUN,
        "--dry-run",
        "-d",
        help="Print commands, don't execute them",
    ),
    force: bool = Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
) -> None:
    missing, zoia, not_zoia, already_exists = [], [], [], []
    for file in expand_files(files):
        try:
            prefix, base = split_file(file)
        except ValueError:
            not_zoia.append(file)
            continue
        if not file.exists():
            missing.append(file)
        else:
            new_file = file.parent / base
            if not force and new_file.exists():
                already_exists.append(new_file)
            else:
                zoia.append((file, new_file))

    if not_zoia:
        print(f"WARNING: not zoia files: {not_zoia}", file=sys.stderr)

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
