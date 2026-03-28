"""Entity management commands."""

import typer
from rich.console import Console
from rich.table import Table

from app.cli.client import api

app = typer.Typer()
console = Console()


def _resolve_persona_id(distinct_id: str) -> str:
    """Look up a persona by distinct_id and return its internal ID."""
    resp = api("GET", "/api/v1/personas", params={"search": distinct_id, "limit": 1})
    results = resp.json()["results"]
    if not results:
        console.print(f"[red]Persona '{distinct_id}' not found[/red]")
        raise typer.Exit(1)
    return results[0]["id"]


@app.command("set")
def set_entity(
    distinct_id: str = typer.Argument(..., help="Persona distinct_id"),
    key: str = typer.Argument(..., help="Entity key"),
    value: str = typer.Argument(..., help="Entity value"),
):
    """Set a key-value entity on a persona. Overwrites if key exists."""
    persona_id = _resolve_persona_id(distinct_id)
    resp = api("POST", f"/api/v1/personas/{persona_id}/entities", json=[{"key": key, "value": value}])
    console.print(f"[green]Set[/green] {key} = {value} [dim]on {distinct_id}[/dim]")


@app.command("list")
def list_entities(
    distinct_id: str = typer.Argument(..., help="Persona distinct_id"),
):
    """List all entities for a persona."""
    persona_id = _resolve_persona_id(distinct_id)
    resp = api("GET", f"/api/v1/personas/{persona_id}/entities")
    entities = resp.json()

    if not entities:
        console.print(f"[dim]No entities on {distinct_id}[/dim]")
        return

    table = Table(title=f"Entities for {distinct_id}")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_column("Updated", style="dim")

    for e in entities:
        table.add_row(e["key"], e["value"], e["updated_at"][:19])

    console.print(table)


@app.command()
def delete(
    distinct_id: str = typer.Argument(..., help="Persona distinct_id"),
    key: str = typer.Argument(..., help="Entity key to remove"),
):
    """Remove an entity from a persona."""
    persona_id = _resolve_persona_id(distinct_id)
    api("DELETE", f"/api/v1/personas/{persona_id}/entities/{key}")
    console.print(f"[green]Removed[/green] {key} [dim]from {distinct_id}[/dim]")
