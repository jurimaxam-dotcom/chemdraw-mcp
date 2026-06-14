#!/usr/bin/env bash
# ChemDraw MCP Server Installer for Mistral AI Vibe
# 
# This script sets up the ChemDraw MCP server to work with Mistral AI Vibe
# with mandatory authentication.
#
# Usage: ./install_vibe.sh
#
# Requirements:
# - bash
# - curl (for uv installation)
# - openssl (for generating secret keys)
#
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "=========================================="
echo "ChemDraw MCP Server for Mistral AI Vibe"
echo "=========================================="
echo "Project: $PROJECT_DIR"
echo ""

# --- 1. Install uv (Python package manager) ---
echo "[1/5] Installing uv..."
if ! command -v uv >/dev/null 2>&1; then
  echo "  → uv not found, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    echo "  ✗ Failed to install uv. Please install manually from https://docs.astral.sh/uv/"
    exit 1
  fi
fi
echo "  ✓ uv: $(command -v uv)"
echo ""

# --- 2. Install Python dependencies ---
echo "[2/5] Installing Python dependencies..."
uv sync --quiet
echo "  ✓ Dependencies installed"
echo ""

# --- 3. Generate authentication configuration ---
echo "[3/5] Setting up authentication..."
CONFIG_DIR="$HOME/.chemdraw-mcp"
mkdir -p "$CONFIG_DIR"

# Generate secret key if not exists
SECRET_KEY_FILE="$CONFIG_DIR/secret_key.txt"
if [ ! -f "$SECRET_KEY_FILE" ]; then
  echo "  → Generating new secret key..."
  openssl rand -hex 32 > "$SECRET_KEY_FILE"
  chmod 600 "$SECRET_KEY_FILE"
  echo "  ✓ Secret key generated at $SECRET_KEY_FILE"
else
  echo "  ✓ Secret key already exists at $SECRET_KEY_FILE"
fi

# Generate a sample API key
API_KEYS_FILE="$CONFIG_DIR/api_keys.txt"
if [ ! -f "$API_KEYS_FILE" ]; then
  echo "  → Generating sample API key..."
  SAMPLE_API_KEY=$(openssl rand -hex 16)
  echo "$SAMPLE_API_KEY" > "$API_KEYS_FILE"
  chmod 600 "$API_KEYS_FILE"
  echo "  ✓ Sample API key generated at $API_KEYS_FILE"
  echo "  📋 API Key: $SAMPLE_API_KEY"
else
  echo "  ✓ API keys file already exists at $API_KEYS_FILE"
fi
echo ""

# --- 4. Display configuration ---
echo "[4/5] Configuration Summary"
echo "=========================================="
echo "Secret Key File: $SECRET_KEY_FILE"
echo "API Keys File:   $API_KEYS_FILE"
echo ""
echo "Environment Variables to Set:"
echo "------------------------------------------"
echo "export CHEMDRAW_SECRET_KEY=\"$(cat $SECRET_KEY_FILE)\""
echo "export CHEMDRAW_API_KEYS=\"$(cat $API_KEYS_FILE)\""
echo ""
echo "Or add to your shell profile (~/.bashrc or ~/.zshrc):"
echo "------------------------------------------"
echo "echo 'export CHEMDRAW_SECRET_KEY=\"$(cat $SECRET_KEY_FILE)\"' >> ~/.bashrc"
echo "echo 'export CHEMDRAW_API_KEYS=\"$(cat $API_KEYS_FILE)\"' >> ~/.bashrc"
echo ""

# --- 5. Vibe Configuration ---
echo "[5/5] Vibe Configuration"
echo "=========================================="
echo "Add the following to your Vibe configuration:"
echo ""
echo "mcpServers:"
echo "  chemdraw:"
echo "    command: uv"
echo "    args: [--directory, $PROJECT_DIR, run, chemdraw-tool-server]"
echo "    env:"
echo "      CHEMDRAW_SECRET_KEY: \"$(cat $SECRET_KEY_FILE)\""
echo "      CHEMDRAW_API_KEYS: \"$(cat $API_KEYS_FILE)\""
echo ""
echo "Or use environment variables directly in your shell."
echo ""

# --- Test ---
echo "=========================================="
echo "Testing installation..."
echo ""

# Test that the server can be imported
if uv run python -c "from chemdraw_tool.auth import create_access_token; print('✓ Auth module works')" 2>/dev/null; then
  echo "  ✓ Authentication module works"
else
  echo "  ✗ Authentication module test failed"
fi

# Test token creation
SECRET=$(cat "$SECRET_KEY_FILE")
if uv run python -c "
import os
os.environ['CHEMDRAW_SECRET_KEY'] = '$SECRET'
from chemdraw_tool.auth import create_access_token, verify_token
token = create_access_token({'sub': 'test'})
print('✓ Token creation works')
" 2>/dev/null; then
  echo "  ✓ Token creation works"
else
  echo "  ✗ Token creation test failed"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Set environment variables (see above)"
echo "2. Configure Vibe with the MCP server settings"
echo "3. Restart Vibe"
echo "4. Create a token: create_auth_token(subject=\"your-user-id\")"
echo "5. Use the token in requests: Authorization: Bearer <token>"
echo ""
echo "To start the server manually:"
echo "  uv run chemdraw-tool-server"
echo ""
