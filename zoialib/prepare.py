import collections
import datetime
import typing as t
from pathlib import Path
from typer import Argument, Option, Typer
import re
import shutil
import sys
import tomlkit

from . import app, DRY_RUN, expand_files, split_file

EMPTY_PATCH = Path(__file__).parents[1] / 'zoia_empty.bin'
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


@app.command()
def prepare(
    files: list[Path] = Argument(
        help="List of file names to prepare",
    ),
    dry_run: bool = Option(
        DRY_RUN,
        "--dry-run",
        "-d",
        help="Print commands, don't execute them",
    ),
    output: Path = Option(
        Path(f"zoia-{TIMESTAMP}"),
        "--output",
        "-o",
        help="Directory to write patch files to",
    ),
    slot_count: int = Option(
        0,
        "--slot-count",
        "-s",
        help="How many slots to fill. If zero, fill to the last slot",
    ),
    slots_file: Path = Option(
        Path("slots_file.toml"),
        "--slots-file",
        "-f",
        help="Set the file used to store slot lists",
    ),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Print more information",
    ),
    update_slots_file: bool = Option(
        True,
        "--update-slots-file",
        "-w/-n",
        help="If true, update the slot list file with the slot assignments",
    ),
) -> None:
    verbose = verbose or dry_run
    files = list(expand_files(files))
    if slots_file.exists():
        cfg = tomlkit.loads(slots_file.read_text())
    else:
        cfg = tomlkit.TOMLDocument()

    if not output.exists():
        if verbose:
            print("Making output directory", output)
        if not dry_run:
            output.mkdir(exist_ok=True, parents=True)

    slot_list = _compute_slot_list(cfg.get("slots", {}), files, slot_count)
    for i, (source, base) in enumerate(slot_list):
        assert isinstance(base, str), base
        target = output / f"{i:03}_zoia_{base}"
        if verbose:
            print(f"Copying {source} to {target}")
        if not dry_run:
            if write_slots_file and base:
                slot = cfg.setdefault("slots", {}).setdefault(f"{i:03}", [])
                if base not in slot:
                    slot.append(base)

            shutil.copy(str(source), str(target))

    if write_slots_file and not dry_run and cfg:
        slots_file.write_text(cfg.as_string())
    print(f"{len(slot_list)} file{(len(slot_list) != 1) * 's'} copied to {output}")


def _compute_slot_list(
    slots: dict[str, t.Any],
    files: list[Path],
    slot_count: int,
):
    slot_assignments = {}
    todo, bad, bad_slots, collisions = [], [], [], []
    max_slot = max(len(files), slot_count) - 1
    for f in files:
        body, _, slot_str = f.name.partition(":")  # : indicates slot
        try:
            base = split_file(body)[1]
        except ValueError:
            bad.append(f)
            continue
        if not slot_str:
            todo.append((f, base))
            continue
        try:
            slot = int(slot_str, 10)
        except Exception:
            bad_slots.append(f)
            continue
        max_slot = max(slot, max_slot)
        if slot in slot_assignments:
            collisions.append(slot)
        else:
            slot_assignments[slot] = (f, base)

    errors = []
    if bad:
        errors.append(f"Not zoia: {bad}")
    if bad_slots:
        errors.append(f"Bad slot identifier: {bad_slots}")
    if collisions:
        errors.append(f"Slot numbers must be distinct: {collisions}")
    d = collections.Counter(base for f, base in todo)
    if dupes := [k for k, v in d.items() if v > 2]:
        errors.append(f"Duplicates: {dupes}")
    if errors:
        sys.exit('\nERROR: '.join(("", *errors)).strip())

    slot_list = [slot_assignments.get(i) for i in range(max_slot + 1)]

    todo_names = {base: f for f, base in todo}
    for i, s in enumerate(slot_list):
        if not todo_names:
            break
        if s:
            continue
        for sl in slots.get(f"{i:03}", ()):
            if f := todo_names.pop(sl, None):
                slot_list[i] = (f, sl)
                break

    names = [(f, b) for b, f in reversed(todo_names.items())]
    slot_list = [i or (names and names.pop()) or (EMPTY_PATCH, ".bin") for i in slot_list]
    assert not names, names

    while len(slot_list) > slot_count and not slot_list[-1]:
        slot_list.pop()

    return slot_list
