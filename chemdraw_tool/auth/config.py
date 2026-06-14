"""Authentication configuration for ChemDraw MCP Server.

This module handles all authentication-related configuration including
secret keys, algorithms, and paths for the Mistral AI Vibe integration.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWT Configuration
# ---------------------------------------------------------------------------

# Secret key for signing JWT tokens.
# Generate with: openssl rand -hex 32
# Can be set via CHEMDRAW_SECRET_KEY environment variable
_SECRET_KEY_ENV = os.environ.get("CHEMDRAW_SECRET_KEY", "")

# If not set in environment, try to read from file
_SECRET_KEY_FILE = Path.home() / ".chemdraw-mcp" / "secret_key.txt"

# For testing purposes, allow a default key
if _SECRET_KEY_ENV:
    SECRET_KEY: str = _SECRET_KEY_ENV
elif _SECRET_KEY_FILE.exists():
    try:
        SECRET_KEY = _SECRET_KEY_FILE.read_text(encoding="utf-8").strip()
        logger.info("Loaded SECRET_KEY from %s", _SECRET_KEY_FILE)
    except (IOError, OSError) as e:
        logger.warning("Could not read SECRET_KEY from %s: %s", _SECRET_KEY_FILE, e)
        SECRET_KEY = ""
else:
    # For development/testing, use a default key if none is configured
    # In production, this should always be set via environment variable
    SECRET_KEY = ""

# JWT signing algorithm
ALGORITHM: str = "HS256"

# Token expiration time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("CHEMDRAW_TOKEN_EXPIRE_MINUTES", "30")
)

# ---------------------------------------------------------------------------
# API Keys Configuration
# ---------------------------------------------------------------------------

# Comma-separated list of valid API keys
# Can be set via CHEMDRAW_API_KEYS environment variable
_API_KEYS_ENV = os.environ.get("CHEMDRAW_API_KEYS", "")

if _API_KEYS_ENV:
    VALID_API_KEYS: list[str] = [k.strip() for k in _API_KEYS_ENV.split(",") if k.strip()]
else:
    VALID_API_KEYS: list[str] = []

# Path to API keys file (one key per line)
API_KEYS_FILE = Path.home() / ".chemdraw-mcp" / "api_keys.txt"

if API_KEYS_FILE.exists():
    try:
        with open(API_KEYS_FILE, encoding="utf-8") as f:
            file_keys = [line.strip() for line in f if line.strip()]
        VALID_API_KEYS.extend(file_keys)
        logger.info("Loaded %d API keys from %s", len(file_keys), API_KEYS_FILE)
    except (IOError, OSError) as e:
        logger.warning("Could not read API keys from %s: %s", API_KEYS_FILE, e)

# ---------------------------------------------------------------------------
# Storage Paths
# ---------------------------------------------------------------------------

# Directory for ChemDraw MCP configuration
CONFIG_DIR = Path.home() / ".chemdraw-mcp"

# Path to users database (for future user management)
USERS_DB_PATH = CONFIG_DIR / "users.json"

# Output directory for generated files (can be overridden)
OUTPUT_DIR = Path(os.environ.get("CHEMDRAW_OUTPUT_DIR", str(Path.home() / "ChemDraw-Output")))

# ---------------------------------------------------------------------------
# OAuth2 Configuration (for future use)
# ---------------------------------------------------------------------------

OAUTH_CALLBACK_URL: Optional[str] = os.environ.get("CHEMDRAW_OAUTH_CALLBACK")

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_config() -> bool:
    """Validate that the authentication configuration is complete.
    
    Returns:
        bool: True if configuration is valid, False otherwise.
        
    Raises:
        ValueError: If required configuration is missing.
    """
    if not SECRET_KEY:
        raise ValueError(
            "CHEMDRAW_SECRET_KEY environment variable is required. "
            "Generate with: openssl rand -hex 32. "
            "Or create file at " + str(_SECRET_KEY_FILE)
        )
    
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    return True


def get_secret_key() -> str:
    """Get the secret key, validating it exists."""
    if not SECRET_KEY:
        raise RuntimeError(
            "Secret key not configured. "
            "Set CHEMDRAW_SECRET_KEY environment variable or create "
            + str(_SECRET_KEY_FILE)
        )
    return SECRET_KEY


def get_valid_api_keys() -> list[str]:
    """Get the list of valid API keys."""
    return VALID_API_KEYS.copy()


def add_api_key(key: str) -> None:
    """Add a new API key to the valid keys list."""
    if key not in VALID_API_KEYS:
        VALID_API_KEYS.append(key)
        # Save to file
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        API_KEYS_FILE.write_text(
            "\n".join(VALID_API_KEYS) + "\n",
            encoding="utf-8"
        )
        logger.info("Added new API key")


def remove_api_key(key: str) -> bool:
    """Remove an API key from the valid keys list.
    
    Returns:
        bool: True if key was found and removed, False otherwise.
    """
    if key in VALID_API_KEYS:
        VALID_API_KEYS.remove(key)
        # Save to file
        API_KEYS_FILE.write_text(
            "\n".join(VALID_API_KEYS) + "\n",
            encoding="utf-8"
        )
        logger.info("Removed API key")
        return True
    return False
