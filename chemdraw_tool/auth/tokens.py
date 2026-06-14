"""JWT token management for ChemDraw MCP Server authentication.

This module provides functions for creating, verifying, and managing
JWT tokens for authentication with Mistral AI Vibe.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import jwt
from fastapi import HTTPException, status

from chemdraw_tool.auth.config import (
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_secret_key,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token Creation
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[Union[timedelta, int]] = None,
) -> str:
    """Create a JWT access token with the given data.
    
    Args:
        data: Dictionary containing the token payload (e.g., {"sub": "username"}).
        expires_delta: Optional timedelta or number of minutes until expiration.
                      If None, uses ACCESS_TOKEN_EXPIRE_MINUTES from config.
    
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta is None:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    elif isinstance(expires_delta, int):
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + expires_delta
    
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    to_encode["type"] = "access"
    
    secret_key = get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    
    logger.debug("Created access token for subject: %s", data.get("sub", "unknown"))
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[Union[timedelta, int]] = None,
) -> str:
    """Create a JWT refresh token with the given data.
    
    Args:
        data: Dictionary containing the token payload.
        expires_delta: Optional timedelta or number of days until expiration.
                      Defaults to 7 days if None.
    
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    
    # Set expiration (default: 7 days)
    if expires_delta is None:
        expire = datetime.utcnow() + timedelta(days=7)
    elif isinstance(expires_delta, int):
        expire = datetime.utcnow() + timedelta(days=expires_delta)
    else:
        expire = datetime.utcnow() + expires_delta
    
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    to_encode["type"] = "refresh"
    
    secret_key = get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    
    logger.debug("Created refresh token for subject: %s", data.get("sub", "unknown"))
    return encoded_jwt


# ---------------------------------------------------------------------------
# Token Verification
# ---------------------------------------------------------------------------

def verify_token(
    token: str,
    expected_type: Optional[str] = None,
) -> dict:
    """Verify a JWT token and return its payload.
    
    Args:
        token: The JWT token to verify.
        expected_type: Optional expected token type ("access" or "refresh").
    
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid, expired, or of wrong type.
    """
    secret_key = get_secret_key()
    
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": True, "verify_iat": False}
        )
        
        # Check token type if specified
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected: {expected_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug("Verified token for subject: %s", payload.get("sub", "unknown"))
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Unexpected error verifying token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying token",
        )


def verify_access_token(token: str) -> dict:
    """Verify that a token is a valid access token.
    
    Args:
        token: The JWT token to verify.
    
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or not an access token.
    """
    return verify_token(token, expected_type="access")


def verify_refresh_token(token: str) -> dict:
    """Verify that a token is a valid refresh token.
    
    Args:
        token: The JWT token to verify.
    
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or not a refresh token.
    """
    return verify_token(token, expected_type="refresh")


# ---------------------------------------------------------------------------
# Token Utilities
# ---------------------------------------------------------------------------

def decode_token_without_verification(token: str) -> dict:
    """Decode a JWT token without verifying its signature.
    
    WARNING: This is only for debugging/logging purposes.
    Never use this for authentication decisions.
    
    Args:
        token: The JWT token to decode.
    
    Returns:
        dict: The decoded token payload.
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.DecodeError:
        return {}


def get_token_expiration(token: str) -> Optional[datetime]:
    """Get the expiration datetime of a token without full verification.
    
    Args:
        token: The JWT token.
    
    Returns:
        datetime: The expiration datetime, or None if not available.
    """
    payload = decode_token_without_verification(token)
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        return datetime.fromtimestamp(exp_timestamp)
    return None


def is_token_expired(token: str) -> bool:
    """Check if a token is expired without full verification.
    
    Args:
        token: The JWT token.
    
    Returns:
        bool: True if the token is expired, False otherwise.
    """
    exp_time = get_token_expiration(token)
    if exp_time is None:
        return True  # If no expiration, consider it expired for safety
    return datetime.utcnow() > exp_time


def refresh_access_token(refresh_token: str) -> str:
    """Use a refresh token to create a new access token.
    
    Args:
        refresh_token: A valid refresh token.
    
    Returns:
        str: A new access token.
        
    Raises:
        HTTPException: If the refresh token is invalid.
    """
    payload = verify_refresh_token(refresh_token)
    # Remove token type and expiration from payload
    payload_copy = {k: v for k, v in payload.items() if k not in ["exp", "iat", "type"]}
    return create_access_token(payload_copy)
