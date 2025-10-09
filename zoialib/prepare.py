import datetime
import shutil
import sys
import typing as t
from collections import Counter
from pathlib import Path

from typer import Argument, Option

from . import app
from .file import dump, expand_files, load, patch_name

EMPTY_PATCH = Path(__file__).parents[1] / "zoia_empty.bin"
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


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

    def copy(i: int, source: Path) -> tuple[Path, Path]:
        base = patch_name(source)
        target = output / f"{i:03}_zoia_{base}"
        if update_slots_file and base:
            slot = cfg.setdefault("slots", {}).setdefault(f"{i:03}", [])
            if base not in slot:
                slot.append(base)
        return source, target

    return [copy(i, p) for i, p in enumerate(slot_list)]


def _compute_slot_list(
    slots: dict[str, t.Any],
    paths: list[Path],
    slot_count: int,
) -> list[Path]:
    slot_assignments = {}
    bad, bad_slots, collisions = [], [], []
    max_slot = max(len(paths), slot_count) - 1

    class PathIndexes(t.NamedTuple):
        path: Path
        file_indexes: list[int]

    todo_indexes: dict[str, PathIndexes] = {}
    for i, p in enumerate(paths):
        body, _, slot_str = p.name.partition(":")  # : indicates slot
        try:
            base = patch_name(Path(body))
        except ValueError:
            bad.append(p)
            continue
        if not slot_str:
            todo_indexes.setdefault(base, PathIndexes(p, [])).file_indexes.append(i)
            continue
        try:
            slot = int(slot_str, 10)
        except Exception:
            bad_slots.append(p)
            continue
        max_slot = max(slot, max_slot)
        if slot in slot_assignments:
            collisions.append(slot)
        else:
            slot_assignments[slot] = p

    errors: list[str] = []
    def join(it: t.Sequence[t.Any]) -> str:
        return ", ".join(str(i) for i in it)

    if bad:
        errors.append(f"Not a zoia file: {join(bad)}")
    if bad_slots:
        errors.append(f"Bad slot identifier: {join(bad_slots)}")
    if collisions:
        errors.append(f"Slot numbers must be distinct: {join(collisions)}")
    if errors:
        sys.exit("\nERROR: ".join(("", *errors)).strip())

    for v in todo_indexes.values():
        v[1].reverse()

    slot_list = [slot_assignments.get(i) for i in range(max_slot + 1)]

    for i, s in enumerate(slot_list):
        if not todo_indexes:
            break
        if s:
            continue
        for slot in slots.get(f"{i:03}", ()):
            if f_indexes := todo_indexes.get(slot):
                f, indexes = f_indexes
                slot_list[i] = f
                indexes.pop()
                if not indexes:
                    todo_indexes.pop(slot)
                break

    it = sorted((i, v.path) for v in todo_indexes.values() for i in v.file_indexes)
    names = [i[1] for i in reversed(it)]

    result = [p or (names and names.pop()) or EMPTY_PATCH for p in slot_list]
    if len(result) < slot_count:
        result.extend(EMPTY_PATCH for _ in range(slot_count - len(result)))
    else:
        while len(result) > slot_count and result[-1] == EMPTY_PATCH:
            result.pop()

    assert not names, (names, result)
    assert all(isinstance(i, Path) for i in result)
    return result
