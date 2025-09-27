from pathlib import Path
from typer import Argument, Option, Typer
import re
import sys
import tomlkit

from . import app, DRY_RUN, expand_files, ZFILE_MATCH


@app.command()
def prepare(
    files: list[Path],
    directory: Path = Path(),
    zlib: Path = Path("zlib.toml"),
    write_zlib: bool = True,
    dry_run: bool = DRY_RUN,
    force: bool = False,
    overwrite: bool = False,
) -> None:
    cfg = tomlkit.loads(zlib.read_text()) if zlib.exists() else tomlkit.TOMLDocument()
    for f in expand_files(files):
        pass
