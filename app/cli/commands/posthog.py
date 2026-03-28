"""PostHog integration CLI commands."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.cli.client import api

app = typer.Typer()
console = Console()


@app.command()
def connect(
    api_key: str = typer.Argument(..., help="PostHog personal API key (phx_...)"),
    project_id: str = typer.Argument(..., help="PostHog project ID"),
    api_host: str = typer.Option(
        "https://us.i.posthog.com", "--host", "-h", help="PostHog API host"
    ),
):
    """Connect to a PostHog instance."""
    console.print("Connecting to PostHog...")
    resp = api(
        "POST",
        "/api/v1/posthog/connect",
        json={"api_key": api_key, "project_id": project_id, "api_host": api_host},
    )
    data = resp.json()
    console.print(f"[green]Connected![/green] Project: {data.get('project_name', data['project_id'])}")


@app.command()
def status():
    """Check PostHog connection status."""
    resp = api("GET", "/api/v1/posthog/status")
    data = resp.json()
    if data["connected"]:
        console.print(f"[green]Connected[/green] to {data.get('project_name', 'Unknown')} ({data['project_id']})")
        console.print(f"  Host: {data['api_host']}")
    else:
        console.print("[dim]Not connected. Use: tpt posthog connect <api_key> <project_id>[/dim]")


@app.command()
def disconnect():
    """Disconnect from PostHog."""
    api("DELETE", "/api/v1/posthog/connect")
    console.print("[green]Disconnected from PostHog[/green]")


@app.command("events")
def query_events(
    distinct_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user distinct_id"),
    event: Optional[str] = typer.Option(None, "--event", "-e", help="Filter by event name"),
    after: Optional[str] = typer.Option(None, "--after", help="ISO 8601 — events after"),
    before: Optional[str] = typer.Option(None, "--before", help="ISO 8601 — events before"),
    limit: int = typer.Option(20, "--limit", "-l"),
):
    """Query events from PostHog."""
    params = {"limit": limit}
    if distinct_id:
        params["distinct_id"] = distinct_id
    if event:
        params["event"] = event
    if after:
        params["after"] = after
    if before:
        params["before"] = before

    resp = api("GET", "/api/v1/posthog/events", params=params)
    events = resp.json()

    if not events:
        console.print("[dim]No events found[/dim]")
        return

    table = Table(title=f"PostHog Events ({len(events)})")
    table.add_column("Timestamp", style="dim")
    table.add_column("User")
    table.add_column("Event", style="bold")
    table.add_column("Properties")

    for e in events:
        props = ""
        if e.get("properties"):
            # Show a few key properties
            skip = {"$lib", "$lib_version", "$geoip_continent_code"}
            filtered = {k: v for k, v in e["properties"].items() if k not in skip}
            props = json.dumps(filtered, separators=(",", ":"))
            if len(props) > 50:
                props = props[:47] + "..."

        table.add_row(
            e["timestamp"][:19] if e.get("timestamp") else "--",
            e.get("distinct_id", "--"),
            e.get("event", "--"),
            props,
        )

    console.print(table)


@app.command("persons")
def query_persons(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name, email, or ID"),
    distinct_id: Optional[str] = typer.Option(None, "--user", "-u", help="Exact distinct_id match"),
    limit: int = typer.Option(20, "--limit", "-l"),
):
    """Query persons from PostHog."""
    params = {"limit": limit}
    if search:
        params["search"] = search
    if distinct_id:
        params["distinct_id"] = distinct_id

    resp = api("GET", "/api/v1/posthog/persons", params=params)
    persons = resp.json()

    if not persons:
        console.print("[dim]No persons found[/dim]")
        return

    table = Table(title=f"PostHog Persons ({len(persons)})")
    table.add_column("Distinct IDs", style="bold")
    table.add_column("Email")
    table.add_column("Properties")

    for p in persons:
        ids = ", ".join(p.get("distinct_ids", [])[:2])
        email = p.get("properties", {}).get("email", "--")
        prop_count = str(len(p.get("properties", {})))
        table.add_row(ids, email, f"{prop_count} props")

    console.print(table)


@app.command()
def sync(
    limit: int = typer.Option(100, "--limit", "-l", help="Max persons to sync"),
):
    """Sync PostHog persons into local personas."""
    console.print("Syncing PostHog persons to personas...")
    resp = api("POST", "/api/v1/posthog/sync", params={"limit": limit})
    result = resp.json()

    console.print(f"[green]Synced {result['synced']} persons[/green] from {result['source']}")
    console.print(f"  Created: {result['created']} new personas")
    console.print(f"  Updated: {result['updated']} existing personas")


@app.command("event-types")
def event_definitions():
    """List all event types in PostHog."""
    resp = api("GET", "/api/v1/posthog/event-definitions")
    definitions = resp.json()

    if not definitions:
        console.print("[dim]No event definitions found[/dim]")
        return

    table = Table(title=f"PostHog Event Types ({len(definitions)})")
    table.add_column("Event Name", style="bold")
    table.add_column("30-day Volume", style="dim")

    for d in definitions:
        vol = str(d.get("volume_30_day", "--"))
        table.add_row(d.get("name", "?"), vol)

    console.print(table)
