from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from proxykit.checker import ProxyChecker
from proxykit.exporters import export_alive_list, export_csv, export_json
from proxykit.models import ProxyType
from proxykit.session import ScrapingSession, build_rotator_from_specs

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="ProxyKit — validate proxies, score anonymity, and rotate for scraping.",
)
console = Console()


def _print_results(results, *, alive_only: bool = False) -> None:
    table = Table(title="ProxyKit Results", show_lines=False)
    table.add_column("Proxy", style="cyan")
    table.add_column("Alive", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Anonymity")
    table.add_column("Score", justify="right")
    table.add_column("Exit IP")
    table.add_column("Error")

    shown = 0
    for item in results:
        if alive_only and not item.alive:
            continue
        shown += 1
        table.add_row(
            str(item.proxy),
            "[green]yes[/green]" if item.alive else "[red]no[/red]",
            f"{item.latency_ms:.0f} ms" if item.latency_ms is not None else "-",
            item.anonymity.value,
            f"{item.score:.1f}",
            item.exit_ip or "-",
            (item.error or "-")[:48],
        )

    console.print(table)
    alive = sum(1 for r in results if r.alive)
    console.print(f"[bold]Checked:[/bold] {len(results)}  [bold]Alive:[/bold] {alive}  [bold]Shown:[/bold] {shown}")


@app.command("check")
def check(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Proxy list file"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Per-proxy timeout seconds"),
    concurrency: int = typer.Option(50, "--concurrency", "-c", help="Max concurrent checks"),
    proxy_type: ProxyType = typer.Option(ProxyType.HTTP, "--type", help="Default proxy type"),
    judge: str = typer.Option("https://httpbin.org/get", "--judge", help="Judge / echo URL"),
    alive_only: bool = typer.Option(False, "--alive-only", help="Show only working proxies"),
    json_out: Optional[Path] = typer.Option(None, "--json", help="Write JSON results"),
    csv_out: Optional[Path] = typer.Option(None, "--csv", help="Write CSV results"),
    alive_out: Optional[Path] = typer.Option(None, "--alive", help="Write alive proxy URLs"),
) -> None:
    """Validate proxies and score latency + anonymity."""
    checker = ProxyChecker(timeout=timeout, concurrency=concurrency, judge_url=judge)
    proxies = checker.load_proxies(file, default_type=proxy_type)
    if not proxies:
        console.print("[red]No valid proxies found in file.[/red]")
        raise typer.Exit(code=1)

    console.print(f"Checking [bold]{len(proxies)}[/bold] proxies...")
    results = checker.check(proxies)
    _print_results(results, alive_only=alive_only)

    if json_out:
        export_json(results, json_out)
        console.print(f"Wrote JSON → {json_out}")
    if csv_out:
        export_csv(results, csv_out)
        console.print(f"Wrote CSV → {csv_out}")
    if alive_out:
        export_alive_list(results, alive_out)
        console.print(f"Wrote alive list → {alive_out}")


@app.command("fetch")
def fetch(
    url: str = typer.Argument(..., help="URL to request through rotating proxies"),
    file: Path = typer.Option(..., "--file", "-f", exists=True, help="Proxy list file"),
    strategy: str = typer.Option("round_robin", "--strategy", help="round_robin or random"),
    retries: int = typer.Option(3, "--retries", "-r"),
    timeout: float = typer.Option(15.0, "--timeout", "-t"),
) -> None:
    """Fetch a URL using proxy rotation + retries."""
    proxies = ProxyChecker.load_proxies(file)
    if not proxies:
        console.print("[red]No valid proxies found.[/red]")
        raise typer.Exit(code=1)

    rotator = build_rotator_from_specs(proxies, strategy=strategy)
    session = ScrapingSession(rotator, timeout=timeout, max_retries=retries)
    response = session.get_sync(url)
    console.print(f"[green]Status:[/green] {response.status_code}")
    console.print(f"[green]Bytes:[/green] {len(response.content)}")
    preview = response.text[:500].replace("\n", " ")
    console.print(f"[green]Preview:[/green] {preview}")


if __name__ == "__main__":
    app()
