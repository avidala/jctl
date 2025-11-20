"""Custom password prompt that shows asterisks."""

import sys
import termios
import tty


def password_prompt(prompt: str = "Password: ", mask: str = "*") -> str:
    """Prompt for password with asterisk masking.

    Args:
        prompt: The prompt text to display
        mask: Character to show for each typed character (default: *)

    Returns:
        The entered password string
    """
    try:
        # Try to use termios for character-by-character input (Unix/Mac)
        return _password_prompt_termios(prompt, mask)
    except (ImportError, AttributeError, termios.error):
        # Fall back to getpass on Windows or if termios fails
        import getpass

        return getpass.getpass(prompt)


def _password_prompt_termios(prompt: str, mask: str) -> str:
    """Password prompt using termios (shows asterisks on Unix/Mac).

    Args:
        prompt: The prompt text to display
        mask: Character to show for each typed character

    Returns:
        The entered password string
    """
    # Print prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()

    password = []

    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        # Set terminal to raw mode (read character by character)
        tty.setraw(fd)

        while True:
            # Read one character
            char = sys.stdin.read(1)

            # Check for Enter/Return
            if char in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                break

            # Check for Backspace/Delete
            elif char in ("\x7f", "\x08"):
                if password:
                    password.pop()
                    # Move cursor back, print space, move back again
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()

            # Check for Ctrl+C
            elif char == "\x03":
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise KeyboardInterrupt

            # Regular character
            elif char >= " ":
                password.append(char)
                sys.stdout.write(mask)
                sys.stdout.flush()

    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(password)


def password_prompt_rich(prompt: str = "Password", default: str = "") -> str:
    """Password prompt compatible with Rich console output.

    Args:
        prompt: The prompt text to display
        default: Default value (not used for passwords but kept for compatibility)

    Returns:
        The entered password string
    """
    from rich.console import Console

    console = Console()
    console.print(f"[cyan]{prompt}:[/cyan] ", end="")

    return password_prompt("", mask="*")
