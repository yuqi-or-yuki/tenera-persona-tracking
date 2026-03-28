"""Clustering CLI commands."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.cli.client import api

app = typer.Typer()
console = Console()


@app.command()
def run(
    algorithm: str = typer.Option("kmeans", "--algo", "-a", help="kmeans, hdbscan, or kprototypes"),
    n_clusters: Optional[int] = typer.Option(None, "--k", help="Number of clusters (auto if omitted)"),
):
    """Run clustering on all personas."""
    body = {"algorithm": algorithm}
    if n_clusters is not None:
        body["params"] = {"n_clusters": n_clusters}

    console.print(f"Running [bold]{algorithm}[/bold] clustering...")
    resp = api("POST", "/api/v1/clusters/run", json=body)
    result = resp.json()

    console.print(f"[green]Done![/green] {result['num_clusters']} clusters from {result['num_personas']} personas")
    console.print(f"  Run ID: {result['run_id']}")

    metrics = result.get("metrics", {})
    if metrics:
        console.print(f"  Silhouette:       {metrics.get('silhouette_score', 'N/A')}")
        console.print(f"  Calinski-Harabasz: {metrics.get('calinski_harabasz', 'N/A')}")
        console.print(f"  Davies-Bouldin:    {metrics.get('davies_bouldin', 'N/A')}")

    # Show cluster names
    names = result.get("cluster_names", {})
    if names:
        console.print("\n  [bold]Clusters:[/bold]")
        for label, name in sorted(names.items(), key=lambda x: int(x[0])):
            console.print(f"    [{label}] {name}")


@app.command()
def results(
    run_id: Optional[str] = typer.Argument(None, help="Run ID (latest if omitted)"),
):
    """Show clustering results."""
    if run_id:
        resp = api("GET", f"/api/v1/clusters/runs/{run_id}")
    else:
        resp = api("GET", "/api/v1/clusters/latest")

    data = resp.json()

    console.print(f"[bold]{data['algorithm']}[/bold] | {data['num_clusters']} clusters | {data['num_personas']} personas")
    console.print(f"  Created: {data['created_at'][:19]}")
    if data.get("silhouette_score"):
        console.print(f"  Silhouette: {data['silhouette_score']}")

    # Group assignments by cluster
    clusters = {}
    for a in data.get("assignments", []):
        label = a["cluster_label"]
        if label not in clusters:
            clusters[label] = {"name": a.get("cluster_name", f"Cluster {label}"), "members": []}
        clusters[label]["members"].append(a)

    for label in sorted(clusters.keys()):
        group = clusters[label]
        console.print(f"\n  [bold blue]{group['name']}[/bold blue] ({len(group['members'])} personas)")
        for m in group["members"]:
            name = m.get("persona_name") or ""
            console.print(f"    {m.get('distinct_id', '?')}  {name}")


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """List past clustering runs."""
    resp = api("GET", "/api/v1/clusters/runs", params={"limit": limit})
    runs = resp.json()

    if not runs:
        console.print("[dim]No clustering runs yet[/dim]")
        return

    table = Table(title="Clustering Runs")
    table.add_column("Time", style="dim")
    table.add_column("Algorithm", style="bold")
    table.add_column("Clusters")
    table.add_column("Personas")
    table.add_column("Silhouette")

    for r in runs:
        table.add_row(
            r["created_at"][:16],
            r["algorithm"],
            str(r["num_clusters"]),
            str(r["num_personas"]),
            r.get("silhouette_score") or "--",
        )

    console.print(table)


@app.command()
def schedule(
    cron: Optional[str] = typer.Argument(None, help="Cron expression (e.g. '0 2 * * *')"),
    algorithm: str = typer.Option("kmeans", "--algo", "-a"),
    disable: bool = typer.Option(False, "--disable", "-d", help="Disable the schedule"),
):
    """Set or view the clustering cron schedule."""
    if disable:
        resp = api("DELETE", "/api/v1/clusters/schedule")
        console.print("[yellow]Schedule disabled[/yellow]")
        return

    if cron is None:
        resp = api("GET", "/api/v1/clusters/schedule")
        config = resp.json()
        if config.get("enabled"):
            console.print(f"[green]Enabled[/green]  cron: {config['cron']}  algo: {config['algorithm']}")
        else:
            console.print("[dim]No schedule configured[/dim]")
        return

    resp = api("POST", "/api/v1/clusters/schedule", json={"cron": cron, "algorithm": algorithm})
    config = resp.json()
    console.print(f"[green]Schedule set:[/green] {config['cron']} ({config['algorithm']})")
