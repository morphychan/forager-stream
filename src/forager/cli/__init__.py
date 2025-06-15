"""
CLI subcommand group package initializer for forager-stream.

This defines the Typer app for nested CLI commands in `forager.cli`.
Each submodule (e.g., rss.py, config.py, api.py) should register its own commands.
"""

import typer
from forager.cli import rss as rss_commands
from forager.cli import config as config_commands
from forager.cli import api as api_commands

# Root CLI app
app = typer.Typer(
    name="forager",
    help="📡 forager-stream CLI — Modular information collection framework.",
    add_completion=True,
    no_args_is_help=True,
)

# Register command groups as subcommands
app.add_typer(
    rss_commands.app,
    name="rss",
    help="RSS feed operations and management.",
)

app.add_typer(
    config_commands.app,
    name="config",
    help="Configuration management operations.",
)

app.add_typer(
    api_commands.app,
    name="api",
    help="Run and manage the Forager API server.",
)
