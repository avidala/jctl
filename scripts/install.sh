#!/usr/bin/env bash
# Install script for jctl

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WRAPPER_SCRIPT="$SCRIPT_DIR/jctl-wrapper.sh"

echo "jctl Installation Script"
echo "========================"
echo

# Detect shell
SHELL_NAME=$(basename "$SHELL")
case "$SHELL_NAME" in
    bash)
        RC_FILE="$HOME/.bashrc"
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    *)
        echo "Unknown shell: $SHELL_NAME"
        echo "Please add this alias manually to your shell RC file:"
        echo "  alias jctl='$WRAPPER_SCRIPT'"
        exit 1
        ;;
esac

echo "Detected shell: $SHELL_NAME"
echo "RC file: $RC_FILE"
echo

# Check if alias already exists
if grep -q "alias jctl=" "$RC_FILE" 2>/dev/null; then
    echo "⚠️  jctl alias already exists in $RC_FILE"
    read -p "Do you want to replace it? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi
    # Remove old alias
    sed -i.bak '/alias jctl=/d' "$RC_FILE"
fi

# Add alias to RC file
echo "" >> "$RC_FILE"
echo "# jctl - Jenkins Control CLI" >> "$RC_FILE"
echo "alias jctl='$WRAPPER_SCRIPT'" >> "$RC_FILE"

echo "✓ Added jctl alias to $RC_FILE"
echo
echo "To use jctl immediately in this terminal, run:"
echo "  source $RC_FILE"
echo
echo "Or open a new terminal window."
echo
echo "Test it with: jctl --help"
