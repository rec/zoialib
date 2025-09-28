import glob
import re
import typing as t
from pathlib import Path

from typer import Typer

ZFILE_MATCH = re.compile(r"(\d\d\d_zoia_)(.*\.bin)").match
LIBFILE_MATCH = re.compile(r".*\.bin").match
DRY_RUN = False


app = Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


def split_file(file: str | Path) -> tuple[str, str]:
    import sys

    s = Path(file).name
    if m := ZFILE_MATCH(s):
        g = m.groups()
    elif m := LIBFILE_MATCH(s):
        g = "", *m.groups()
    else:
        raise ValueError("Not a patch file")
    assert len(g) == 2, g
    return g


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
