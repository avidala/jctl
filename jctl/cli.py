"""Main CLI definition and command groups."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click
from rich.console import Console

from jctl import __version__
from jctl.commands import auth, config, job, pipeline
from jctl.utils.logging import setup_logging

_VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _no_color_requested() -> bool:
    """True if the user has asked us to drop ANSI colors.

    Honors `JCTL_NO_COLOR` (this tool's flag) and the widely-respected
    `NO_COLOR` convention (https://no-color.org). Any non-empty value
    counts as truthy.
    """
    return bool(os.environ.get("JCTL_NO_COLOR") or os.environ.get("NO_COLOR"))


console = Console(no_color=_no_color_requested())


@click.group()
@click.version_option(version=__version__, prog_name="jctl")
@click.option(
    "--profile",
    default=None,
    envvar="JCTL_PROFILE",
    help="Configuration profile to use (env: JCTL_PROFILE).",
)
@click.option("--debug", is_flag=True, help="Enable debug mode (shorthand for --log-level DEBUG).")
@click.option(
    "--log-level",
    type=click.Choice(_VALID_LOG_LEVELS, case_sensitive=False),
    default=None,
    envvar="JCTL_LOG_LEVEL",
    help="Logging verbosity (env: JCTL_LOG_LEVEL). Overrides --debug if both set.",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "yaml", "plain"]),
    default="table",
    envvar="JCTL_OUTPUT_FORMAT",
    help="Output format (env: JCTL_OUTPUT_FORMAT).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    profile: str | None,
    debug: bool,
    log_level: str | None,
    output: str,
) -> None:
    """jctl - Jenkins Control CLI.

    A flexible tool for managing Jenkins pipelines using API token authentication.
    """
    # --log-level takes precedence; --debug is a shorthand; otherwise INFO.
    effective_level = (log_level or ("DEBUG" if debug else "INFO")).upper()
    setup_logging(level=effective_level, debug=debug or effective_level == "DEBUG")

    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["debug"] = debug
    ctx.obj["log_level"] = effective_level
    ctx.obj["output"] = output
    ctx.obj["console"] = console


# Register command groups
cli.add_command(auth.auth)
cli.add_command(job.job)
cli.add_command(pipeline.pipeline)
cli.add_command(config.config)


# --- shell completion install helpers --------------------------------------
#
# Snippets the installer appends to the user's rc file. Each uses Click's
# built-in completion API (`_JCTL_COMPLETE=<shell>_source jctl`), so it
# works regardless of how jctl is installed (pipx, Homebrew, editable),
# with no hard-coded path to a `scripts/` file in this repo. The previous
# installer baked in `/Users/<dev>/.../scripts/jctl-completion.zsh`
# verbatim, which broke any time the repo moved or the user installed via
# Homebrew (where that path doesn't exist).

_COMPLETION_SNIPPETS = {
    "bash": '\n# jctl - Jenkins Control CLI completion\neval "$(_JCTL_COMPLETE=bash_source jctl)"\n',
    "zsh": '\n# jctl - Jenkins Control CLI completion\neval "$(_JCTL_COMPLETE=zsh_source jctl)"\n',
}
_COMPLETION_MARKER = "_JCTL_COMPLETE"


def _detect_shell() -> str | None:
    shell_env = os.environ.get("SHELL", "")
    for name in ("bash", "zsh", "fish"):
        if name in shell_env:
            return name
    return None


def _rc_file_for(shell: str) -> Path | None:
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc" if (home / ".bashrc").exists() else home / ".bash_profile"
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "fish":
        return home / ".config" / "fish" / "completions" / "jctl.fish"
    return None


def _is_already_installed(rc_path: Path) -> bool:
    return rc_path.exists() and _COMPLETION_MARKER in rc_path.read_text()


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]), required=False)
@click.option("--install", is_flag=True, help="Automatically install completion to shell config.")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt for --install.")
@click.option(
    "--dry-run",
    is_flag=True,
    help="With --install, show what would be added and exit without modifying any file.",
)
def completion(shell: str | None, install: bool, yes: bool, dry_run: bool) -> None:
    """Install shell completion for jctl.

    Examples:
        jctl completion --install --dry-run   # preview the rc-file change
        jctl completion --install             # install with confirmation
        jctl completion --install -y          # install non-interactively
        jctl completion zsh                   # print manual setup instructions
    """
    target = shell or _detect_shell()
    if target is None:
        console.print("[red]Error:[/red] Could not detect shell ($SHELL unset).")
        console.print("\nPlease specify your shell:")
        console.print("  jctl completion bash")
        console.print("  jctl completion zsh")
        console.print("  jctl completion fish")
        sys.exit(1)

    if install:
        _install_completion(target, yes=yes, dry_run=dry_run)
        return

    # Print manual instructions.
    console.print(f"[cyan]Shell completion for {target}[/cyan]\n")
    console.print("[bold]Quick install:[/bold]")
    console.print("  [cyan]jctl completion --install[/cyan]\n")
    console.print("[bold]Or manual setup:[/bold]\n")

    if target in _COMPLETION_SNIPPETS:
        rc = _rc_file_for(target)
        console.print(f"1. Append this to your {rc}:\n")
        console.print(f'   eval "$(_JCTL_COMPLETE={target}_source jctl)"')
        console.print(f"\n2. Reload your shell:\n   source {rc}")
    else:  # fish
        console.print("1. Run this command:\n")
        console.print("   _JCTL_COMPLETE=fish_source jctl > ~/.config/fish/completions/jctl.fish")
        console.print("\n2. Open a new fish shell.")

    console.print("\n[green]✓[/green] After installing you can Tab-complete:")
    console.print("  • Commands: [cyan]jctl pipeline <Tab>[/cyan]")
    console.print("  • Job names: [cyan]jctl pipeline run hamc<Tab>[/cyan]")
    console.print("  • Options:   [cyan]jctl pipeline run --<Tab>[/cyan]")


def _install_completion(shell: str, *, yes: bool, dry_run: bool) -> None:
    """Append a Click-driven completion snippet to the user's shell rc.

    Refuses to modify the rc file without confirmation (unless `--yes`).
    Idempotent: if a `_JCTL_COMPLETE` line is already present, just say so.
    Bash/zsh share the rc-file append flow; fish writes a generated
    completion script instead.
    """
    rc = _rc_file_for(shell)
    if rc is None:
        console.print(f"[red]Error:[/red] Unsupported shell: {shell}")
        sys.exit(1)

    if shell == "fish":
        rc.parent.mkdir(parents=True, exist_ok=True)
        if rc.exists() and not yes and not dry_run:
            console.print(f"[yellow]Note:[/yellow] {rc} already exists.")
            if not click.confirm("Overwrite?", default=False):
                console.print("Aborted.")
                return
        if dry_run:
            console.print(f"[cyan]Would write[/cyan] {rc}")
            console.print("  contents from: [cyan]_JCTL_COMPLETE=fish_source jctl[/cyan]")
            return
        import subprocess

        result = subprocess.run(
            ["jctl"],
            env={**os.environ, "_JCTL_COMPLETE": "fish_source"},
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            console.print(f"[red]Failed to generate fish completion:[/red] {result.stderr}")
            sys.exit(1)
        rc.write_text(result.stdout)
        console.print(f"[green]✓[/green] Wrote fish completion to {rc}")
        console.print("Open a new fish shell to activate.")
        return

    # bash / zsh: append the eval-snippet to the rc file.
    if _is_already_installed(rc):
        console.print(f"[green]✓[/green] Completion already installed in {rc} — nothing to do.")
        return

    snippet = _COMPLETION_SNIPPETS[shell]

    if dry_run:
        console.print(f"[cyan]Would append to[/cyan] {rc}:")
        for line in snippet.strip("\n").splitlines():
            console.print(f"  [dim]{line}[/dim]")
        console.print("\n[dim](dry-run — no changes made)[/dim]")
        return

    console.print(f"[yellow]About to modify[/yellow] {rc}")
    console.print("The following lines will be appended:\n")
    for line in snippet.strip("\n").splitlines():
        console.print(f"  [dim]{line}[/dim]")
    console.print()

    if not yes and not click.confirm("Proceed?", default=False):
        console.print("Aborted — no changes made.")
        return

    if not rc.exists():
        rc.parent.mkdir(parents=True, exist_ok=True)
        rc.touch()
    with rc.open("a") as f:
        f.write(snippet)
    console.print(f"[green]✓[/green] Completion installed in {rc}")
    console.print(f"To activate now: [cyan]source {rc}[/cyan]")


if __name__ == "__main__":
    cli(obj={})
