"""Main entry point for jctl CLI."""

import sys

from jctl.cli import cli


def main() -> int:
    """Run the CLI application."""
    try:
        cli(obj={})
        return 0
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
