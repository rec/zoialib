from typer import Typer

app = Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
