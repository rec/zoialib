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
TIMESTAMP = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

"""
TODO:

* rewrite zlib.toml
* write some tests
* add typer Arguments and Options
* write documentation

"""


@app.command()
def prepare(
    files: list[Path] = Argument(
        help="List of file names to prepare",
    ),
    output: Path = Option(
        Path(f"zoia-{TIMESTAMP}"),
        "--output",
        "-o",
        help="Directory to write patch files to",
    ),
    slots_file: Path = Option(
        Path("slots_file.toml"),
        "--slots-file",
        "-s",
        help="Set the file used to store slot lists",
    ),
    write_slots_file: bool = Option(
        True,
        "--write-slots-file",
        "-w/-n",
        help="If true, overwrite the slots file ",
    ),
    dry_run: bool = Option(
        DRY_RUN,
        "--dry-run",
        "-d",
        help="Print commands, don't execute them",
    ),
    slot_count: int = Option(
        0,
        "--slot-count",
        "-s",
        help="How many slots to fill. If zero, fill to the last slot",
    ),
) -> None:
    files = list(expand_files(files))
    if slots_file.exists():
        cfg = tomlkit.loads(slots_file.read_text())
    else:
        cfg = tomlkit.TOMLDocument()

    if not output.exists():
        print("Making output:", output)
    if not dry_run:
        output.mkdir(exist_ok=True, parents=True)
    for source, target in _compute_slot_list(cfg.setdefault("slots", {}), files, slot_count):
        print(f"Copying {source} to {output}/{target}")
        if not dry_run:
            shutil.copy(str(source), str(output / target))


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
        for s in slots.get(str(i), ()):
            if name := todo_names.pop(s, None):
                slot_list[i] = (s, name)
                break

    names = [(f, b) for b, f in reversed(todo_names.items())]
    slot_list = [i or (names and names.pop()) or (EMPTY_PATCH, ".bin") for i in slot_list]
    assert not names, names

    while len(slot_list) > slot_count and not slot_list[-1]:
        slot_list.pop()

    return [(f, f"{i:03}_zoia_{base}") for i, (f, base) in enumerate(slot_list)]
