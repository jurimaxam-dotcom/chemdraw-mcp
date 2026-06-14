"""Authentication middleware for ChemDraw MCP Server.

This module provides FastAPI/Starlette middleware and dependencies
for authenticating requests to the MCP server.
"""

import logging
import os
from typing import Callable, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.authentication import AuthCredentials, AuthenticationBackend, SimpleUser

from chemdraw_tool.auth.config import get_valid_api_keys
from chemdraw_tool.auth.tokens import verify_access_token, verify_token

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security Schemes
# ---------------------------------------------------------------------------

# Bearer token security scheme
bearer_scheme = HTTPBearer()

# API key header scheme (for simple API key authentication)
api_key_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# Authentication Backends
# ---------------------------------------------------------------------------

class JWTAuthenticationBackend(AuthenticationBackend):
    """Authentication backend for JWT tokens."""
    
    async def authenticate(
        self,
        request: Request,
    ) -> Optional[tuple[AuthCredentials, SimpleUser]]:
        """Authenticate a request using JWT token."""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.debug("No Authorization header found")
            return None
        
        # Check for Bearer token
        if not auth_header.lower().startswith("bearer "):
            logger.debug("Authorization header is not Bearer token")
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            payload = verify_token(token)
            user_id = payload.get("sub", "anonymous")
            user = SimpleUser(user_id)
            credentials = AuthCredentials(["authenticated"])
            logger.debug("Authenticated user: %s", user_id)
            return (credentials, user)
        except HTTPException:
            logger.warning("JWT authentication failed")
            return None
        except Exception as e:
            logger.error("Error during JWT authentication: %s", e)
            return None


class APIKeyAuthenticationBackend(AuthenticationBackend):
    """Authentication backend for API keys."""
    
    def __init__(self):
        self.valid_keys = get_valid_api_keys()
    
    async def authenticate(
        self,
        request: Request,
    ) -> Optional[tuple[AuthCredentials, SimpleUser]]:
        """Authenticate a request using API key."""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # Also check X-API-Key header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                auth_header = f"Bearer {api_key}"
            else:
                logger.debug("No Authorization or X-API-Key header found")
                return None
        
        # Check for Bearer token
        if not auth_header.lower().startswith("bearer "):
            logger.debug("Authorization header is not Bearer token")
            return None
        
        api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        if api_key in self.valid_keys:
            user = SimpleUser(api_key)  # Using API key as user ID
            credentials = AuthCredentials(["api_key"])
            logger.debug("Authenticated with API key")
            return (credentials, user)
        
        logger.warning("Invalid API key attempted")
        return None


# ---------------------------------------------------------------------------
# Dependency Functions
# ---------------------------------------------------------------------------

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency that verifies a JWT token and returns its payload.
    
    Args:
        credentials: HTTPAuthorizationCredentials from FastAPI.
    
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid.
    """
    token = credentials.credentials
    return verify_token(token)


async def verify_access_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency that verifies a JWT access token and returns its payload.
    
    Args:
        credentials: HTTPAuthorizationCredentials from FastAPI.
    
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or not an access token.
    """
    token = credentials.credentials
    return verify_access_token(token)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Dependency that verifies an API key.
    
    Args:
        credentials: HTTPAuthorizationCredentials from FastAPI.
    
    Returns:
        str: The API key.
        
    Raises:
        HTTPException: If the API key is invalid.
    """
    api_key = credentials.credentials
    valid_keys = get_valid_api_keys()
    
    if api_key not in valid_keys:
        logger.warning("Invalid API key: %s", api_key[:8] + "..." if len(api_key) > 8 else api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("Valid API key used")
    return api_key


async def get_api_key_dependency(
    request: Request,
) -> Optional[str]:
    """Dependency that extracts and validates API key from various headers.
    
    Checks in order:
    1. X-API-Key header
    2. Authorization: Bearer header
    
    Args:
        request: FastAPI Request object.
    
    Returns:
        str: The API key if valid, None otherwise.
    """
    # Check X-API-Key header first
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            api_key = auth_header[7:]
    
    if not api_key:
        return None
    
    valid_keys = get_valid_api_keys()
    
    if api_key in valid_keys:
        return api_key
    
    return None


async def optional_auth(
    request: Request,
) -> Optional[dict]:
    """Dependency for optional authentication.
    
    Tries to authenticate but doesn't fail if authentication is missing.
    
    Args:
        request: FastAPI Request object.
    
    Returns:
        dict: Token payload if authenticated, None otherwise.
    """
    try:
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        if not auth_header.lower().startswith("bearer "):
            return None
        
        token = auth_header[7:]
        
        # Try JWT first
        try:
            return verify_token(token)
        except HTTPException:
            # Try as API key
            valid_keys = get_valid_api_keys()
            if token in valid_keys:
                return {"sub": token, "type": "api_key"}
        
        return None
        
    except Exception as e:
        logger.debug("Optional auth failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Combined Authentication
# ---------------------------------------------------------------------------

class CombinedAuthenticationBackend(AuthenticationBackend):
    """Authentication backend that tries multiple methods."""
    
    def __init__(self):
        self.jwt_backend = JWTAuthenticationBackend()
        self.api_key_backend = APIKeyAuthenticationBackend()
    
    async def authenticate(
        self,
        request: Request,
    ) -> Optional[tuple[AuthCredentials, SimpleUser]]:
        """Try JWT authentication first, then API key."""
        # Try JWT first
        result = await self.jwt_backend.authenticate(request)
        if result:
            return result
        
        # Try API key
        return await self.api_key_backend.authenticate(request)


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def create_auth_dependency(
    auth_type: str = "jwt",
    optional: bool = False,
) -> Callable:
    """Factory function to create authentication dependencies.
    
    Args:
        auth_type: Type of authentication ("jwt", "api_key", "combined").
        optional: If True, authentication is optional.
    
    Returns:
        Callable: A FastAPI dependency function.
    """
    if optional:
        return optional_auth
    
    if auth_type == "jwt":
        return verify_access_jwt_token
    elif auth_type == "api_key":
        return verify_api_key
    else:  # combined
        async def combined_dependency(
            credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        ) -> dict:
            token = credentials.credentials
            
            # Try JWT first
            try:
                return verify_token(token)
            except HTTPException:
                pass
            
            # Try as API key
            valid_keys = get_valid_api_keys()
            if token in valid_keys:
                return {"sub": token, "type": "api_key"}
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return combined_dependency
