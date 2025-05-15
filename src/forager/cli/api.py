"""
CLI subcommands related to API server operations.
"""
import os
import typer
import uvicorn
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="api",
    help="Run and manage the Forager API server.",
    no_args_is_help=True,
)

@app.command("start")
def start(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind the server to.",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the server to.",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development.",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes.",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Logging level (debug, info, warning, error, critical).",
    ),
    database_url: Optional[str] = typer.Option(
        None,
        "--db",
        help="Database URL. If not provided, uses the default SQLite database.",
    ),
) -> None:
    """
    Start the Forager API server.
    
    This command launches the FastAPI application with Uvicorn server.
    """
    # Print startup message
    typer.echo(f"[API] Starting Forager API server on {host}:{port}")
    
    # Set environment variables if provided
    if database_url:
        os.environ["DATABASE_URL"] = database_url
        typer.echo(f"[API] Using custom database URL: {database_url}")
    
    # Configure server
    typer.echo(f"[API] Workers: {workers}, Reload: {reload}, Log level: {log_level}")
    
    # Start the API server
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level=log_level.lower(),
        )
    except Exception as e:
        typer.echo(f"[ERROR] Failed to start API server: {e}")
        raise typer.Exit(code=1)

@app.command("routes")
def list_routes() -> None:
    """
    List all available API routes.
    
    This is a utility command that prints out all registered routes in the API.
    """
    try:
        # Dynamically import the app to avoid circular imports
        from api.main import app as api_app
        
        typer.echo("[API] Available routes:")
        
        # Sort routes for better readability
        routes = sorted(
            [
                f"{route.path} [{', '.join(route.methods)}]"
                for route in api_app.routes
            ]
        )
        
        for route in routes:
            typer.echo(f"  {route}")
            
    except ImportError as e:
        typer.echo(f"[ERROR] Failed to import API app: {e}")
        raise typer.Exit(code=1) 