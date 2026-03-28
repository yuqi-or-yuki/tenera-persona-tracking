"""HTTP client for talking to the FastAPI server from the CLI."""

import os
import sys

import httpx
from rich.console import Console

console = Console()

DEFAULT_BASE_URL = "http://localhost:8000"


def _get_api_key() -> str:
    key = os.environ.get("TPT_API_KEY")
    if key:
        return key

    # Try reading from .env in cwd
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    console.print("[red]No API key found.[/red] Set TPT_API_KEY or add API_KEY to .env")
    sys.exit(1)


def _get_base_url() -> str:
    return os.environ.get("TPT_BASE_URL", DEFAULT_BASE_URL)


def api(method: str, path: str, **kwargs) -> httpx.Response:
    """Make an authenticated request to the persona tracking server."""
    url = f"{_get_base_url()}{path}"
    headers = {"X-API-Key": _get_api_key()}

    try:
        resp = httpx.request(method, url, headers=headers, timeout=30, **kwargs)
    except httpx.ConnectError:
        console.print(
            f"[red]Cannot connect to server at {_get_base_url()}[/red]\n"
            "Start the server first: [bold]tpt serve[/bold]"
        )
        sys.exit(1)

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        console.print(f"[red]Error {resp.status_code}:[/red] {detail}")
        sys.exit(1)

    return resp
