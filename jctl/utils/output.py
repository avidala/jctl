"""Output formatting utilities."""

import json
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table


class OutputFormatter:
    """Format output in various formats."""

    def __init__(self, console: Console | None = None):
        """Initialize formatter.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()

    def format(self, data: Any, format: str = "table") -> None:  # noqa: A002
        """Format and print data.

        Args:
            data: Data to format
            format: Output format (table, json, yaml, plain)
        """
        if format == "json":
            self.format_json(data)
        elif format == "yaml":
            self.format_yaml(data)
        elif format == "plain":
            self.format_plain(data)
        else:
            self.format_table(data)

    def format_json(self, data: Any) -> None:
        """Format as JSON.

        Args:
            data: Data to format
        """
        self.console.print_json(json.dumps(data, indent=2))

    def format_yaml(self, data: Any) -> None:
        """Format as YAML.

        Args:
            data: Data to format
        """
        output = yaml.dump(data, default_flow_style=False, sort_keys=False)
        self.console.print(output)

    def format_plain(self, data: Any, prefix: str = "") -> None:
        """Format as plain text.

        Nested dicts and lists are flattened with dot/index notation so the
        output is always grep/awk friendly (no embedded Python `repr` blobs).
        """
        if isinstance(data, dict):
            for key, value in data.items():
                full = key if not prefix else f"{prefix}.{key}"
                if isinstance(value, dict):
                    self.format_plain(value, prefix=full)
                elif isinstance(value, (list, tuple)):
                    self._format_plain_list(value, prefix=full)
                else:
                    self.console.print(f"{full}={value}", highlight=False)
        elif isinstance(data, (list, tuple)):
            if not prefix:
                for item in data:
                    self.console.print(item, highlight=False)
            else:
                self._format_plain_list(data, prefix=prefix)
        else:
            self.console.print(str(data), highlight=False)

    def _format_plain_list(self, items: Any, prefix: str) -> None:
        """Flatten a list value, recursing into dict elements with [i] indices."""
        if all(not isinstance(v, (dict, list, tuple)) for v in items):
            joined = ",".join(str(v) for v in items)
            self.console.print(f"{prefix}={joined}", highlight=False)
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                self.format_plain(item, prefix=f"{prefix}[{i}]")
            elif isinstance(item, (list, tuple)):
                self._format_plain_list(item, prefix=f"{prefix}[{i}]")
            else:
                self.console.print(f"{prefix}[{i}]={item}", highlight=False)

    def format_table(self, data: Any) -> None:
        """Format as table.

        Args:
            data: Data to format (should be list of dicts)
        """
        if not data:
            self.console.print("[dim]No data[/dim]")
            return

        if isinstance(data, dict):
            # Single dict - format as key-value pairs
            table = Table(show_header=True)
            table.add_column("Key", style="cyan")
            table.add_column("Value")

            for key, value in data.items():
                table.add_row(str(key), str(value))

            self.console.print(table)

        elif isinstance(data, list) and len(data) > 0:
            # List of dicts - format as table
            if not isinstance(data[0], dict):
                # List of simple values
                table = Table(show_header=False)
                table.add_column("Value")
                for item in data:
                    table.add_row(str(item))
                self.console.print(table)
                return

            # Get all keys from all dicts
            keys = set()
            for item in data:
                if isinstance(item, dict):
                    keys.update(item.keys())

            keys_list = sorted(keys)

            table = Table(show_header=True)
            for key in keys_list:
                table.add_column(str(key).upper(), style="cyan" if key == keys_list[0] else None)

            for item in data:
                row = [str(item.get(key, "")) for key in keys_list]
                table.add_row(*row)

            self.console.print(table)
        else:
            self.console.print(str(data))

    def print_status(self, status: str, message: str) -> None:
        """Print status message with icon.

        Args:
            status: Status type (success, error, warning, info)
            message: Message to print
        """
        icons = {
            "success": "[green]✓[/green]",
            "error": "[red]✗[/red]",
            "warning": "[yellow]⚠[/yellow]",
            "info": "[cyan]ℹ[/cyan]",
        }

        icon = icons.get(status, "")
        self.console.print(f"{icon} {message}")

    def print_validations(self, validations: list[tuple[str, bool, str | None]]) -> None:
        """Print validation results.

        Args:
            validations: List of (check_name, passed, error_message) tuples
        """
        for check_name, passed, error_msg in validations:
            if passed:
                self.console.print(f"[green]✓[/green] {check_name}")
            else:
                self.console.print(f"[red]✗[/red] {check_name}")
                if error_msg:
                    self.console.print(f"  [dim]{error_msg}[/dim]")


def format_duration(milliseconds: int) -> str:
    """Format duration in milliseconds to human-readable string.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    if milliseconds < 0:
        return "N/A"

    seconds = milliseconds // 1000
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    seconds = seconds % 60

    if minutes < 60:
        if seconds > 0:
            return f"{minutes}m {seconds}s"
        return f"{minutes}m"

    hours = minutes // 60
    minutes = minutes % 60

    if hours < 24:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

    days = hours // 24
    hours = hours % 24

    if hours > 0:
        return f"{days}d {hours}h"
    return f"{days}d"
