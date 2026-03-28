"""Event timeline viewing command."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.cli.client import api

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def events(
    distinct_id: str = typer.Argument(..., help="Persona distinct_id"),
    limit: int = typer.Option(20, "--limit", "-l"),
    event_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by event type"),
):
    """View the event timeline for a persona."""
    resp = api("GET", "/api/v1/personas", params={"search": distinct_id, "limit": 1})
    results = resp.json()["results"]
    if not results:
        console.print(f"[red]Persona '{distinct_id}' not found[/red]")
        raise typer.Exit(1)

    persona_id = results[0]["id"]
    params = {"limit": limit}
    if event_type:
        params["event_type"] = event_type

    resp = api("GET", f"/api/v1/personas/{persona_id}/events", params=params)
    event_list = resp.json()

    if not event_list:
        console.print(f"[dim]No events for {distinct_id}[/dim]")
        return

    table = Table(title=f"Events for {distinct_id}")
    table.add_column("Timestamp", style="dim")
    table.add_column("Event Type", style="bold")
    table.add_column("Properties")

    for e in event_list:
        props = ""
        if e.get("properties"):
            props = json.dumps(e["properties"], separators=(",", ":"))
            if len(props) > 60:
                props = props[:57] + "..."
        table.add_row(e["timestamp"][:19], e["event_type"], props)

    console.print(table)
