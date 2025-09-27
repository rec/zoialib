from typer import Typer
import re
import typing as t
from pathlib import Path


ZFILE_MATCH = re.compile(r"(\d\d\d_zoia_)(.*\.bin)").match
LIBFILE_MATCH = re.compile(r".*\.bin)").match


app = Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


def split_file(file: str | Path) -> tuple[str, str]:
    s = str(file)
    if m := ZFILE_MATCH(s):
        return m.groups()
    if m := LIBFILE_MATCH(s):
        return "", *m.groups()
   raise ValueError("Not a patch file")


def is_zoia_file(file: str | Path) -> bool:
    try:
        split_file(file)
    except ValueError:
        return False
    return True


def expand_files(files: t.Iterable[Path]) -> t.Iterator[Path]:
    for f in files:
        if f.suffix == ".txt":
            li = f.read_text().splitlines()
            yield from expand_files(t for s in li if (t := s.partition("#")[0].strip()))
