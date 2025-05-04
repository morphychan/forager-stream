"""
CLI subcommand group package initializer for forager-stream.

This defines the Typer app for nested CLI commands in `forager.cli`.
Each submodule (e.g., input.py, run.py) should register its own commands.
"""

import typer
from forager.cli import input as input_commands

# Root CLI app
app = typer.Typer(
    name="forager",
    help="📡 forager-stream CLI — Modular information collection framework.",
    add_completion=True,
    no_args_is_help=True,
)

# Register command groups as subcommands
app.add_typer(
    input_commands.app,
    name="input",
    help="Run or test specific input plugins (e.g., RSS, API).",
)
