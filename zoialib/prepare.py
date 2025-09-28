import collections
import datetime
import shutil
import sys
import typing as t
from pathlib import Path

from typer import Argument, Option

from . import app
from .file import dump, expand_files, load, split_file

EMPTY_PATCH = Path(__file__).parents[1] / "zoia_empty.bin"
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
EMPTY = EMPTY_PATCH, ".bin"


@app.command(help="Copy patch files into a ZOIA patch directory")
def prepare(
    files: list[Path] = Argument(
        help="List of file names to prepare",
    ),
    dry_run: bool = Option(
        False,
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
        False,
        "--update-slots-file",
        "-u/-n",
        help="If true, update the slot list file with the slot assignments",
    ),
) -> None:
    verbose = verbose or dry_run
    cfg = load(slots_file)

    if not output.exists():
        if verbose:
            print("Making output directory", output)
        if not dry_run:
            output.mkdir(exist_ok=True, parents=True)

    copies = _prepare(cfg, files, output, slot_count, slots_file, update_slots_file)
    for source, target in copies:
        if verbose:
            print(f"Copying {source} to {target}")
        if not dry_run:
            shutil.copy(str(source), str(target))

    if update_slots_file and cfg:
        if verbose:
            print(f"Writing {slots_file}")
        if not dry_run:
            dump(cfg, slots_file)

    print(f"{len(copies)} file{(len(copies) != 1) * 's'} copied to {output}")


def _prepare(
    cfg: t.MutableMapping,
    files: list[Path],
    output: Path,
    slot_count: int,
    slots_file: Path,
    update_slots_file: bool,
) -> list[tuple[Path, Path]]:
    files = list(expand_files(files))
    slot_list = _compute_slot_list(cfg.get("slots", {}), files, slot_count)

    def copy(i: int, source: Path, base: str) -> tuple[Path, Path]:
        assert isinstance(base, str), base
        target = output / f"{i:03}_zoia_{base}"
        if update_slots_file and base:
            slot = cfg.setdefault("slots", {}).setdefault(f"{i:03}", [])
            if base not in slot:
                slot.append(base)
        return source, target

    return [copy(i, s, b) for i, (s, b) in enumerate(slot_list)]


def _compute_slot_list(
    slots: dict[str, t.Any],
    files: list[Path],
    slot_count: int,
) -> list[tuple[Path, str]]:
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

    errors: list[str] = []
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
        sys.exit("\nERROR: ".join(("", *errors)).strip())

    slot_list = [slot_assignments.get(i) for i in range(max_slot + 1)]

    todo_names = {base: f for f, base in todo}
    for i, s in enumerate(slot_list):
        if not todo_names:
            break
        if s:
            continue
        for sl in slots.get(f"{i:03}", ()):
            if (f := todo_names.pop(sl, _NO_PATH)) is not _NO_PATH:
                slot_list[i] = (f, sl)
                break

    names = [(f, b) for b, f in reversed(todo_names.items())]

    sl = [i or (names and names.pop()) or EMPTY for i in slot_list]
    while len(sl) > slot_count and sl[-1] == EMPTY:
        sl.pop()

    assert not names, (names, sl)
    return sl


_NO_PATH = Path()
