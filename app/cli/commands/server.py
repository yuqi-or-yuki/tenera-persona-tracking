"""Start the FastAPI server."""

import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
):
    """Start the persona tracking server."""
    import uvicorn

    typer.echo(f"Starting server at http://{host}:{port}")
    typer.echo(f"API docs at http://{host}:{port}/docs")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
