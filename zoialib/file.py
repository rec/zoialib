import glob
import io
import json
import re
import typing as t
from functools import cache
from pathlib import Path

import tomlkit
import yaml

ZFILE_MATCH = re.compile(r"\d\d\d_zoia_(.*\.bin)").match
LIBFILE_MATCH = re.compile(r".*\.bin").match
DRY_RUN = False
_LOAD: dict[str, t.Callable[[io.TextIOWrapper], t.MutableMapping[str, t.Any]]] = {
    ".toml": tomlkit.load,
    ".yaml": yaml.safe_load,
    ".json": json.load,
}
_DUMP: dict[str, t.Callable[[t.MutableMapping[str, t.Any], io.TextIOWrapper], None]] = {
    ".toml": tomlkit.dump,
    ".yaml": yaml.safe_dump,
    ".json": json.dump,
}


def load(p: Path) -> t.MutableMapping[str, t.Any]:
    if not p.exists():
        return tomlkit.TOMLDocument() if p.suffix == ".toml" else {}
    if not (load := _LOAD.get(p.suffix)):
        raise ValueError(f"Do not understand suffix {p.suffix} in file {p}")
    with p.open() as fp:
        return load(fp)


def dump(data: t.MutableMapping[str, t.Any], p: Path) -> None:
    if not (dump := _DUMP.get(p.suffix)):
        raise ValueError(f"Do not understand suffix {p.suffix} in file {p}")
    with p.open("w") as fp:
        dump(data, fp)


@cache
def patch_name(file: Path) -> str:
    if m := ZFILE_MATCH(file.name) or LIBFILE_MATCH(file.name):
        return m.groups()[0]
    else:
        raise ValueError("Not a patch file")


def expand_files(files: t.Iterable[Path]) -> t.Iterator[Path]:
    for f in files:
        base, sep, slot_index = (s := str(f)).partition(":")
        f_base = Path(base)
        if glob.has_magic(s):
            if sep:
                raise ValueError(f"Globs cannot have slot indexes: {s}")
            yield from expand_files(Path().glob(s))
        elif f_base.suffix == ".txt":
            if sep:
                raise ValueError(f"Text files cannot have slot indexes: {s}")
            li = f.read_text().splitlines()
            yield from expand_files(
                Path(t) for s in li if (t := s.partition("#")[0].strip())
            )
        else:
            yield f
