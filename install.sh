#!/bin/bash
# Mini-Git Global Installation Script

MINIGIT_DIR="/home/fyzanshaik/workspace/github.com/fyzanshaik/mini-git"
INSTALL_DIR="$HOME/.local/bin"

echo "Installing Mini-Git globally..."

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy the minigit executable
cp "$MINIGIT_DIR/minigit" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/minigit"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "Adding $INSTALL_DIR to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
    echo "Please run: source ~/.bashrc (or restart your terminal)"
fi

echo "✅ Mini-Git installed successfully!"
echo "You can now use 'minigit' from any directory"
