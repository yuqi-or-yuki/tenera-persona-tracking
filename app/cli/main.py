"""CLI entry point: `tpt` command."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.cli.client import api
from app.cli.commands.cluster import app as cluster_app
from app.cli.commands.entity import app as entity_app
from app.cli.commands.persona import app as persona_app
from app.cli.commands.posthog import app as posthog_app
from app.cli.commands.server import app as server_app

cli = typer.Typer(
    name="tpt",
    help="Tenera Persona Tracking -- CLI-first persona analytics engine.",
    no_args_is_help=True,
)

cli.add_typer(persona_app, name="persona", help="Manage personas")
cli.add_typer(entity_app, name="entity", help="Manage entities on personas")
cli.add_typer(cluster_app, name="cluster", help="Clustering and cohort analysis")
cli.add_typer(posthog_app, name="posthog", help="PostHog integration")
cli.add_typer(server_app, name="serve", help="Start the server")

console = Console()


@cli.command()
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


@cli.command()
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


if __name__ == "__main__":
    cli()
