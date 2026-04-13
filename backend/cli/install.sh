#!/bin/bash

# CodeQuality Gate CLI Installer

echo "Installing CodeQuality Gate CLI..."

# Make the CLI executable
chmod +x /app/backend/cli/quality_gate.py

# Create symlink in /usr/local/bin
sudo ln -sf /app/backend/cli/quality_gate.py /usr/local/bin/quality-gate

echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  quality-gate scan <path>                    # Scan files or directory"
echo "  quality-gate scan-pr <repo> <pr_number>     # Scan GitHub PR"
echo ""
echo "Examples:"
echo "  quality-gate scan ./src"
echo "  quality-gate scan ./app.js ./utils.js"
echo "  quality-gate scan-pr facebook/react 12345"
echo ""