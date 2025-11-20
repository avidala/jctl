#!/usr/bin/env python3
"""Post-install script to set up shell completion for jctl."""

import os
from pathlib import Path


def get_shell() -> str:
    """Detect user's shell."""
    shell = os.environ.get("SHELL", "")
    if "bash" in shell:
        return "bash"
    elif "zsh" in shell:
        return "zsh"
    elif "fish" in shell:
        return "fish"
    return ""


def get_completion_file() -> Path:
    """Get path to the completion file."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    return script_dir / "jctl-completion.zsh"


def get_shell_rc_file(shell: str) -> Path | None:
    """Get the shell RC file path."""
    home = Path.home()
    if shell == "bash":
        # Try .bashrc first, then .bash_profile
        bashrc = home / ".bashrc"
        if bashrc.exists():
            return bashrc
        return home / ".bash_profile"
    elif shell == "zsh":
        return home / ".zshrc"
    elif shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    return None


def is_completion_installed(rc_file: Path, completion_file: Path) -> bool:
    """Check if completion is already installed in the RC file."""
    if not rc_file.exists():
        return False

    content = rc_file.read_text()
    return str(completion_file) in content or "jctl-completion" in content


def install_completion_zsh(rc_file: Path, completion_file: Path) -> bool:
    """Install completion for zsh."""
    completion_setup = f"""
# jctl - Jenkins Control CLI completion
source {completion_file}
"""

    if is_completion_installed(rc_file, completion_file):
        return False  # Already installed

    # Append to RC file
    with rc_file.open("a") as f:
        f.write(completion_setup)

    return True


def install_completion_bash(rc_file: Path, completion_file: Path) -> bool:
    """Install completion for bash."""
    # For bash, we'll use Click's built-in completion
    completion_setup = """
# jctl - Jenkins Control CLI completion
eval "$(_JCTL_COMPLETE=bash_source jctl)"
"""

    if is_completion_installed(rc_file, completion_file):
        return False  # Already installed

    # Append to RC file
    with rc_file.open("a") as f:
        f.write(completion_setup)

    return True


def install_completion_fish() -> bool:
    """Install completion for fish."""
    fish_config = Path.home() / ".config" / "fish" / "completions"
    fish_config.mkdir(parents=True, exist_ok=True)

    fish_completion_file = fish_config / "jctl.fish"

    if fish_completion_file.exists():
        return False  # Already installed

    # Generate fish completion
    os.system(f"_JCTL_COMPLETE=fish_source jctl > {fish_completion_file}")

    return True


def setup_completion() -> None:
    """Set up shell completion for jctl."""
    shell = get_shell()

    if not shell:
        print("⚠️  Could not detect your shell. Skipping completion setup.")
        print("   Run 'jctl completion' to manually set up completion.")
        return

    completion_file = get_completion_file()

    if not completion_file.exists() and shell != "bash":
        print(f"⚠️  Completion file not found: {completion_file}")
        print("   Skipping completion setup.")
        return

    rc_file = get_shell_rc_file(shell)

    if not rc_file:
        print(f"⚠️  Could not find shell RC file for {shell}")
        print("   Run 'jctl completion' to manually set up completion.")
        return

    try:
        installed = False

        if shell == "zsh":
            installed = install_completion_zsh(rc_file, completion_file)
        elif shell == "bash":
            installed = install_completion_bash(rc_file, completion_file)
        elif shell == "fish":
            installed = install_completion_fish()

        if installed:
            print(f"✅ Shell completion installed for {shell}!")
            print(f"   Added to: {rc_file}")
            print()
            print("   To activate completion, run:")
            print(f"   source {rc_file}")
            print()
            print("   Or restart your shell:")
            print("   exec $SHELL")
        else:
            print(f"✅ Shell completion already installed for {shell}")

    except Exception as e:
        print(f"⚠️  Failed to install completion: {e}")
        print("   Run 'jctl completion' to manually set up completion.")


if __name__ == "__main__":
    setup_completion()
