"""Main CLI definition and command groups."""

import os
import sys

import click
from rich.console import Console

from jctl import __version__
from jctl.commands import auth, config, job, pipeline
from jctl.utils.logging import setup_logging

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="jctl")
@click.option("--profile", default=None, help="Configuration profile to use")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--output",
    type=click.Choice(["table", "json", "yaml", "plain"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(ctx: click.Context, profile: str | None, debug: bool, output: str) -> None:
    """jctl - Jenkins Control CLI.

    A flexible tool for managing Jenkins pipelines with Okta SSO authentication.
    """
    # Setup logging based on debug flag
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(level=log_level, debug=debug)

    # Ensure ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["profile"] = profile
    ctx.obj["debug"] = debug
    ctx.obj["output"] = output
    ctx.obj["console"] = console


# Register command groups
cli.add_command(auth.auth)
cli.add_command(job.job)
cli.add_command(pipeline.pipeline)
cli.add_command(config.config)


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]), required=False)
@click.option("--install", is_flag=True, help="Automatically install completion to shell config")
def completion(shell: str | None, install: bool) -> None:
    """Install shell completion for jctl.

    Examples:
        jctl completion --install    # Auto-install completion
        jctl completion bash         # Show bash completion script
        jctl completion zsh          # Show zsh completion script
        jctl completion              # Auto-detect shell and show instructions
    """
    # Handle --install flag
    if install:
        # Run the automated setup script
        import subprocess
        from pathlib import Path

        script_path = Path(__file__).parent.parent / "scripts" / "setup-completion.py"
        result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
        console.print(result.stdout)
        if result.returncode != 0 and result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
        return

    # Auto-detect shell if not provided
    if shell is None:
        shell_env = os.environ.get("SHELL", "")
        if "bash" in shell_env:
            shell = "bash"
        elif "zsh" in shell_env:
            shell = "zsh"
        elif "fish" in shell_env:
            shell = "fish"
        else:
            console.print("[red]Error:[/red] Could not detect shell")
            console.print("\nPlease specify your shell:")
            console.print("  jctl completion bash")
            console.print("  jctl completion zsh")
            console.print("  jctl completion fish")
            sys.exit(1)

    console.print(f"[cyan]Shell completion for {shell}[/cyan]\n")

    console.print("[bold]Quick install:[/bold]")
    console.print("  [cyan]jctl completion --install[/cyan]")
    console.print("\n[bold]Or manual setup:[/bold]\n")

    if shell == "bash":
        console.print("1. Add this to your ~/.bashrc:\n")
        console.print('   eval "$(_JCTL_COMPLETE=bash_source jctl)"')
        console.print("\n2. Reload your shell:\n")
        console.print("   source ~/.bashrc")

    elif shell == "zsh":
        console.print("1. Add this to your ~/.zshrc:\n")
        console.print('   eval "$(_JCTL_COMPLETE=zsh_source jctl)"')
        console.print("\n2. Reload your shell:\n")
        console.print("   source ~/.zshrc")

    elif shell == "fish":
        console.print("1. Run this command:\n")
        console.print("   _JCTL_COMPLETE=fish_source jctl > ~/.config/fish/completions/jctl.fish")
        console.print("\n2. Reload your shell:\n")
        console.print("   source ~/.config/fish/config.fish")

    console.print("\n[green]✓[/green] After installing, you can use Tab to auto-complete:")
    console.print("  • Command names: [cyan]jctl pipeline <Tab>[/cyan]")
    console.print("  • Job/pipeline names: [cyan]jctl pipeline run managed-<Tab>[/cyan]")
    console.print("  • Options: [cyan]jctl pipeline run --<Tab>[/cyan]")


if __name__ == "__main__":
    cli(obj={})
