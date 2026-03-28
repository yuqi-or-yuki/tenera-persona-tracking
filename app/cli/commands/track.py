"""Event tracking command."""

import json
from typing import Optional

import typer
from rich.console import Console

from app.cli.client import api

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def track(
    distinct_id: str = typer.Argument(..., help="Persona distinct_id to track against"),
    event_type: str = typer.Argument(..., help="Event type (e.g. page_view, purchase)"),
    properties: Optional[str] = typer.Option(
        None, "--props", "-p", help='JSON properties (e.g. \'{"page": "/pricing"}\')'
    ),
):
    """Track an event for a persona. Auto-creates the persona if it doesn't exist."""
    body = {"event_type": event_type}
    if properties:
        try:
            body["properties"] = json.loads(properties)
        except json.JSONDecodeError:
            console.print(f"[red]Invalid JSON:[/red] {properties}")
            raise typer.Exit(1)

    resp = api("POST", "/api/v1/track", params={"distinct_id": distinct_id}, json=body)
    event = resp.json()
    console.print(
        f"[green]Tracked[/green] [bold]{event_type}[/bold] "
        f"[dim]for {distinct_id} at {event['timestamp'][:19]}[/dim]"
    )
