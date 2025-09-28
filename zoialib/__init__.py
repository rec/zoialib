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
        if glob.has_magic(s := str(f)):
            yield from expand_files(Path().glob(s))
        elif f.suffix == ".txt":
            li = f.read_text().splitlines()
            yield from expand_files(
                Path(t) for s in li if (t := s.partition("#")[0].strip())
            )
        else:
            yield f
