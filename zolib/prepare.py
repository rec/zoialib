from pathlib import Path
from typer import Argument, Option, Typer
import re
import sys

from . import app

ZFILE_MATCH = re.compile(r"\d\d\d_zoia_(.*\.bin)").match
DRY_RUN = True


@app.command()
def prepare(*, dry_run: bool = DRY_RUN, force: bool=False) -> None:
    pass
