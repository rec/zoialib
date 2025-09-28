import sys
from collections import Counter
from pathlib import Path

from typer import Argument, Option

from . import app
from .file import expand_files, patch_name


@app.command(help="Rename ZOIA patch files to remove the slot number and marker string")
def rename(
    files: list[Path] = Argument(help="A list of files to be renamed"),
    dry_run: bool = Option(
        False,
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
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Print more information",
    ),
) -> None:
    verbose = verbose or dry_run
    try:
        zoia = _rename(files, force, verbose)
    except ValueError as e:
        sys.exit("\n".join(e.args))

    for old, new in zoia:
        if verbose:
            print(old, "->", new)
        if not dry_run:
            old.rename(new)
    print(f"{len(zoia)} file{(len(zoia) != 1) * 's'} renamed")


def _rename(files: list[Path], force: bool, verbose: bool) -> list[tuple[Path, Path]]:
    missing, zoia, not_zoia, already_exists = [], [], [], []
    for file in expand_files(files):
        try:
            base = patch_name(file)
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
    if multi := [k for k, v in Counter(t for s, t in zoia).items() if v > 2]:
        errors.append(f"One source writing to multiple targets: {multi}")
    if dupes := [k for k, v in Counter(s for s, t in zoia).items() if v > 2]:
        errors.append(f"Multiple sources writing to the same target: {dupes}")
    if not (errors or zoia):
        errors.append("No files to rename")

    if errors:
        raise ValueError("\nERROR: ".join(("", *errors)).strip())

    return zoia
