#!/bin/sh
# Installs haunted-terminal into ~/.ghost and wires it into ~/.zshrc.
# Yes, the ghost will warn you about piping this into sh. It is right to.
set -eu
SRC=${GHOST_SRC:-https://haunted-terminal.onrender.com}
DEST="$HOME/.ghost"

mkdir -p "$DEST"
curl -fsSL "$SRC/ghost" -o "$DEST/ghost"
curl -fsSL "$SRC/ghost.zsh" -o "$DEST/ghost.zsh"
chmod +x "$DEST/ghost"

LINE="source \"$DEST/ghost.zsh\""
grep -qxF "$LINE" "$HOME/.zshrc" 2>/dev/null || echo "$LINE" >> "$HOME/.zshrc"

echo "The ghost has moved in. Start Gemma, then open a new terminal:"
echo "  llama-server -hf ggml-org/gemma-4-E2B-it-GGUF --port 8080"
