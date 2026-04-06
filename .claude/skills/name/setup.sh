#!/bin/bash
# Ensure Python dependencies are installed for the /name skill.
# Safe to run multiple times -- skips if already installed.

set -e

# Check if requests is importable
if python3 -c "import requests" 2>/dev/null; then
    exit 0
fi

echo "Installing Python dependencies for /name skill..."

# Try pip3 first
if command -v pip3 &>/dev/null; then
    pip3 install --break-system-packages requests beautifulsoup4 2>/dev/null || \
    pip3 install requests beautifulsoup4
    exit 0
fi

# Install pip if not available
if command -v sudo &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-pip
    pip3 install --break-system-packages requests beautifulsoup4 2>/dev/null || \
    pip3 install requests beautifulsoup4
else
    echo "ERROR: Cannot install pip without sudo. Please install python3-pip manually."
    exit 1
fi
