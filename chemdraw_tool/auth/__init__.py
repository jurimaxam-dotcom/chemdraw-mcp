"""Authentication module for ChemDraw MCP Server.

This module provides authentication support for Mistral AI Vibe integration,
supporting both JWT tokens and API keys.
"""

from chemdraw_tool.auth.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_DB_PATH,
    validate_config,
    get_valid_api_keys,
)
from chemdraw_tool.auth.tokens import create_access_token, verify_token
from chemdraw_tool.auth.middleware import (
    verify_api_key,
    verify_jwt_token,
    get_api_key_dependency,
    optional_auth,
)

__all__ = [
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "USERS_DB_PATH",
    "validate_config",
    "get_valid_api_keys",
    "create_access_token",
    "verify_token",
    "verify_api_key",
    "verify_jwt_token",
    "get_api_key_dependency",
    "optional_auth",
]
