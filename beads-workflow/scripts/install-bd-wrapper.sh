#!/bin/sh
# install-bd-wrapper.sh — Install the bd PATH-shim wrapper to ~/.local/bin/bd
#
# This makes `bd lint --check=architecture-contracts` work in any shell,
# without needing to source bd-lint-extension.sh.
#
# Usage:
#   bash beads-workflow/scripts/install-bd-wrapper.sh
#
# Compatible with POSIX sh, bash, and zsh.

set -e

# Locate the install script's real directory
_SELF=$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || "$0")
_SCRIPT_DIR=$(dirname "$_SELF")
_WRAPPER="$_SCRIPT_DIR/bd-wrapper"

# Sanity check
if [ ! -f "$_WRAPPER" ]; then
    echo "ERROR: bd-wrapper not found at $_WRAPPER" >&2
    exit 1
fi

# Ensure ~/.local/bin exists
_TARGET_DIR="$HOME/.local/bin"
if [ ! -d "$_TARGET_DIR" ]; then
    echo "Creating $_TARGET_DIR ..."
    mkdir -p "$_TARGET_DIR"
fi

_TARGET="$_TARGET_DIR/bd"

# Handle existing target
if [ -e "$_TARGET" ] || [ -L "$_TARGET" ]; then
    _existing=$(readlink -f "$_TARGET" 2>/dev/null || realpath "$_TARGET" 2>/dev/null || echo "$_TARGET")
    _new=$(readlink -f "$_WRAPPER" 2>/dev/null || realpath "$_WRAPPER" 2>/dev/null || echo "$_WRAPPER")
    if [ "$_existing" = "$_new" ]; then
        echo "Already installed: $_TARGET -> $_WRAPPER (no change needed)"
    else
        echo "WARNING: $_TARGET already exists and points elsewhere ($_existing)."
        echo "Overwriting with symlink to $_WRAPPER ..."
        rm -f "$_TARGET"
        ln -s "$_WRAPPER" "$_TARGET"
        echo "Installed: $_TARGET -> $_WRAPPER"
    fi
else
    ln -s "$_WRAPPER" "$_TARGET"
    echo "Installed: $_TARGET -> $_WRAPPER"
fi

# Check if ~/.local/bin is in PATH
case ":$PATH:" in
    *":$_TARGET_DIR:"*)
        echo ""
        echo "PATH already includes $_TARGET_DIR — you're ready to go!"
        echo ""
        echo "  bd lint --check=architecture-contracts"
        ;;
    *)
        echo ""
        echo "IMPORTANT: $_TARGET_DIR is not in your PATH."
        echo "Add it by appending one of the following to your shell config:"
        echo ""
        echo "  For bash (~/.bashrc or ~/.bash_profile):"
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        echo "  For zsh (~/.zshrc):"
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        echo "  Then restart your shell or run: source ~/.bashrc  (or ~/.zshrc)"
        echo ""
        echo "After that, the following command will work without sourcing any shell extension:"
        echo ""
        echo "  bd lint --check=architecture-contracts"
        ;;
esac
