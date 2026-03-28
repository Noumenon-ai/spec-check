"""Rich terminal table output formatter."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from spec_check.scanner import ScanResult

console = Console()

STATUS_ICONS = {
    "FOUND": "[bold green]FOUND[/]",
    "PARTIAL": "[yellow]PARTIAL[/]",
    "MISSING": "[bold red]MISSING[/]",
}


def print_result(result: ScanResult) -> None:
    """Print scan result as a rich terminal table."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]SPEC-CHECK[/] v1.0.0",
        border_style="cyan",
    ))
    console.print()
    console.print(f"  Scanning: [bold]{result.directory}[/] ({result.files_scanned} files)")
    console.print(f"  Spec features: [bold]{result.total_features}[/]")
    console.print()

    table = Table(border_style="dim", show_lines=False)
    table.add_column("Feature", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Evidence")

    for f in result.features:
        status = STATUS_ICONS.get(f.status, f.status)
        evidence = ", ".join(f.evidence[:2]) if f.evidence else ""
        # Shorten paths for display
        if evidence:
            parts = evidence.split("/")
            if len(parts) > 3:
                evidence = "/".join(parts[-3:])
        table.add_row(f.feature, status, evidence)

    console.print(table)
    console.print()

    # Completeness bar
    pct = result.completeness
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "[green]" + "█" * filled + "[/]" + "[dim]" + "░" * (bar_len - filled) + "[/]"
    color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
    console.print(f"  Completeness: {bar} [{color}]{pct}%[/{color}] ({result.found_count}/{result.total_features} features built)")
    console.print()

    if result.missing_count:
        missing = [f.feature for f in result.features if f.status == "MISSING"]
        console.print(f"  [red]Missing:[/] {', '.join(missing)}")
    if result.partial_count:
        partial = [f.feature for f in result.features if f.status == "PARTIAL"]
        console.print(f"  [yellow]Partial:[/] {', '.join(partial)}")
    console.print()
