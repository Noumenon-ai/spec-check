"""Spec-Check CLI — command definitions."""

from typing import Optional

import typer
from rich.console import Console

from spec_check import __version__
from spec_check.formatters.json_fmt import format_json
from spec_check.formatters.table import print_result
from spec_check.parser import parse_spec
from spec_check.scanner import scan_project

app = typer.Typer(
    name="spec-check",
    help="Verify if AI-generated code matches your spec.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Spec text describing features"),
    spec_file: Optional[str] = typer.Option(None, "--spec-file", "-f", help="Path to spec file"),
    dir: str = typer.Option(".", "--dir", "-d", help="Project directory to scan"),
    auto: bool = typer.Option(False, "--auto", help="Auto-detect spec from README"),
    format: str = typer.Option("table", "--format", help="Output format: table or json"),
    strict: bool = typer.Option(False, "--strict", help="Exit code 1 if < 100%% complete"),
) -> None:
    """Check project completeness against a spec."""
    # A subcommand (e.g. `spec-check version`) handles its own work.
    if ctx.invoked_subcommand is not None:
        return

    # Get spec text
    spec_text = _resolve_spec(spec, spec_file, auto, dir)
    if not spec_text:
        console.print("  [red]No spec provided.[/]")
        console.print("  Use --spec 'features...' or --spec-file spec.md or --auto")
        raise typer.Exit(code=2)

    # Parse features
    features = parse_spec(spec_text)
    if not features:
        console.print("  [yellow]Could not parse any features from spec.[/]")
        console.print("  Try: --spec 'login page, signup page, dashboard'")
        raise typer.Exit(code=2)

    # Scan
    result = scan_project(dir, features)

    # Output
    if format == "json":
        console.print(format_json(result))
    else:
        print_result(result)

    # Strict mode
    if strict and result.completeness < 100.0:
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show spec-check version."""
    console.print(f"spec-check v{__version__}")


def _resolve_spec(
    spec: Optional[str],
    spec_file: Optional[str],
    auto: bool,
    directory: str,
) -> Optional[str]:
    """Resolve spec text from the various input methods."""
    if spec:
        return spec

    if spec_file:
        from pathlib import Path
        path = Path(spec_file)
        if path.exists():
            return path.read_text(encoding="utf-8")
        console.print(f"  [red]Spec file not found: {spec_file}[/]")
        return None

    if auto:
        from pathlib import Path
        readme = Path(directory) / "README.md"
        if readme.exists():
            return readme.read_text(encoding="utf-8")
        console.print("  [red]No README.md found for --auto mode.[/]")
        return None

    return None


if __name__ == "__main__":
    app()
