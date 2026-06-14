"""Tests for the authentication module.

This module contains tests for JWT token creation/verification,
API key management, and authentication middleware.
"""

import os
import sys
import tempfile
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.testclient import TestClient

# Set up test environment BEFORE importing any chemdraw_tool modules
# This ensures the environment variables are set before module initialization
os.environ["CHEMDRAW_SECRET_KEY"] = "test-secret-key-for-testing-only-1234567890123456"
os.environ["CHEMDRAW_API_KEYS"] = "test-api-key-1,test-api-key-2"

# Now import the modules
from chemdraw_tool.auth.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_secret_key,
    get_valid_api_keys,
    add_api_key,
    remove_api_key,
    validate_config,
    CONFIG_DIR,
)
from chemdraw_tool.auth.tokens import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_access_token,
    verify_refresh_token,
    decode_token_without_verification,
    get_token_expiration,
    is_token_expired,
    refresh_access_token,
)
from chemdraw_tool.auth.middleware import (
    verify_jwt_token,
    verify_api_key,
    get_api_key_dependency,
    optional_auth,
    CombinedAuthenticationBackend,
    JWTAuthenticationBackend,
    APIKeyAuthenticationBackend,
    bearer_scheme,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_client():
    """Create a test client for the MCP server."""
    # We'll create a minimal FastAPI app for testing
    from fastapi import FastAPI, Depends
    from fastapi.security import HTTPBearer
    
    app = FastAPI()
    
    @app.get("/test-jwt")
    async def test_jwt_endpoint(
        payload: dict = Depends(verify_jwt_token)
    ):
        return {"status": "ok", "payload": payload}
    
    @app.get("/test-api-key")
    async def test_api_key_endpoint(
        api_key: str = Depends(verify_api_key)
    ):
        return {"status": "ok", "api_key": api_key}
    
    return TestClient(app)


@pytest.fixture
def sample_token():
    """Create a sample JWT token for testing."""
    return create_access_token({"sub": "testuser", "role": "user"})


@pytest.fixture
def expired_token():
    """Create an expired JWT token for testing."""
    return create_access_token(
        {"sub": "testuser", "role": "user"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Tests for authentication configuration."""
    
    def test_secret_key_loaded(self):
        """Test that secret key is loaded from environment."""
        assert SECRET_KEY == "test-secret-key-for-testing-only"
    
    def test_get_secret_key(self):
        """Test get_secret_key function."""
        key = get_secret_key()
        assert key == "test-secret-key-for-testing-only"
    
    def test_validate_config_success(self):
        """Test that configuration validation succeeds with proper setup."""
        assert validate_config() is True
    
    def test_validate_config_missing_key(self):
        """Test that configuration validation fails without secret key."""
        with patch.dict(os.environ, {"CHEMDRAW_SECRET_KEY": ""}, clear=False):
            # Force reload of config
            import importlib
            import chemdraw_tool.auth.config as config_module
            importlib.reload(config_module)
            
            with pytest.raises(ValueError, match="CHEMDRAW_SECRET_KEY"):
                config_module.validate_config()
    
    def test_get_valid_api_keys(self):
        """Test getting valid API keys."""
        keys = get_valid_api_keys()
        assert "test-api-key-1" in keys
        assert "test-api-key-2" in keys
    
    def test_add_api_key(self):
        """Test adding a new API key."""
        new_key = "new-test-api-key"
        add_api_key(new_key)
        keys = get_valid_api_keys()
        assert new_key in keys
        # Clean up
        remove_api_key(new_key)
    
    def test_remove_api_key(self):
        """Test removing an API key."""
        new_key = "temp-test-api-key"
        add_api_key(new_key)
        assert remove_api_key(new_key) is True
        assert new_key not in get_valid_api_keys()
    
    def test_remove_nonexistent_api_key(self):
        """Test removing a non-existent API key."""
        assert remove_api_key("nonexistent-key") is False


# =============================================================================
# Token Creation Tests
# =============================================================================

class TestTokenCreation:
    """Tests for JWT token creation."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        token = create_access_token({"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0
        # Token should have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_create_access_token_with_custom_expiration(self):
        """Test creating an access token with custom expiration."""
        token = create_access_token(
            {"sub": "testuser"},
            expires_delta=timedelta(hours=1)
        )
        assert isinstance(token, str)
        # Verify expiration is approximately 1 hour from now
        payload = decode_token_without_verification(token)
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert now < exp < now + timedelta(hours=2)
    
    def test_create_access_token_with_int_expiration(self):
        """Test creating an access token with integer expiration (minutes)."""
        token = create_access_token({"sub": "testuser"}, expires_delta=60)
        assert isinstance(token, str)
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = create_refresh_token({"sub": "testuser"})
        assert isinstance(token, str)
        # Verify it's a refresh token
        payload = decode_token_without_verification(token)
        assert payload.get("type") == "refresh"
    
    def test_create_refresh_token_default_expiration(self):
        """Test that refresh tokens have 7 day expiration by default."""
        token = create_refresh_token({"sub": "testuser"})
        payload = decode_token_without_verification(token)
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        # Should be approximately 7 days
        assert now + timedelta(days=6.9) < exp < now + timedelta(days=7.1)


# =============================================================================
# Token Verification Tests
# =============================================================================

class TestTokenVerification:
    """Tests for JWT token verification."""
    
    def test_verify_token_success(self, sample_token):
        """Test verifying a valid token."""
        payload = verify_token(sample_token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload
    
    def test_verify_access_token_success(self, sample_token):
        """Test verifying a valid access token."""
        payload = verify_access_token(sample_token)
        assert payload["sub"] == "testuser"
    
    def test_verify_token_wrong_type(self):
        """Test verifying a token with wrong type."""
        refresh_token = create_refresh_token({"sub": "testuser"})
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(refresh_token)
        assert exc_info.value.status_code == 401
    
    def test_verify_expired_token(self, expired_token):
        """Test verifying an expired token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401
    
    def test_verify_token_wrong_signature(self):
        """Test verifying a token with wrong signature."""
        # Create token with different key
        with patch.dict(os.environ, {"CHEMDRAW_SECRET_KEY": "different-key"}, clear=False):
            from chemdraw_tool.auth.tokens import create_access_token as create_token_other
            token = create_token_other({"sub": "testuser"})
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401


# =============================================================================
# Token Utility Tests
# =============================================================================

class TestTokenUtilities:
    """Tests for token utility functions."""
    
    def test_decode_token_without_verification(self, sample_token):
        """Test decoding a token without verification."""
        payload = decode_token_without_verification(sample_token)
        assert payload["sub"] == "testuser"
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_token_without_verification("invalid.token")
        assert payload == {}
    
    def test_get_token_expiration(self, sample_token):
        """Test getting token expiration."""
        exp = get_token_expiration(sample_token)
        assert isinstance(exp, datetime)
        assert exp > datetime.utcnow()
    
    def test_get_token_expiration_invalid(self):
        """Test getting expiration from invalid token."""
        exp = get_token_expiration("invalid.token")
        assert exp is None
    
    def test_is_token_expired_false(self, sample_token):
        """Test that a valid token is not expired."""
        assert is_token_expired(sample_token) is False
    
    def test_is_token_expired_true(self, expired_token):
        """Test that an expired token is detected as expired."""
        assert is_token_expired(expired_token) is True
    
    def test_refresh_access_token(self):
        """Test refreshing an access token."""
        refresh_token = create_refresh_token({"sub": "testuser"})
        new_access_token = refresh_access_token(refresh_token)
        
        # Verify new token is valid
        payload = verify_access_token(new_access_token)
        assert payload["sub"] == "testuser"


# =============================================================================
# Middleware Tests
# =============================================================================

class TestMiddleware:
    """Tests for authentication middleware."""
    
    @pytest.mark.asyncio
    async def test_verify_jwt_token_dependency(self, sample_token):
        """Test JWT token verification dependency."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        # This is a bit tricky to test directly, so we'll test via the function
        credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials=sample_token
        )
        
        payload = await verify_jwt_token(credentials)
        assert payload["sub"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_dependency(self):
        """Test API key verification dependency."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials="test-api-key-1"
        )
        
        api_key = await verify_api_key(credentials)
        assert api_key == "test-api-key-1"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials="invalid-api-key"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(credentials)
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_optional_auth_with_token(self, sample_token):
        """Test optional authentication with valid token."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": f"Bearer {sample_token}"}
        
        payload = await optional_auth(mock_request)
        assert payload is not None
        assert payload["sub"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_optional_auth_with_api_key(self):
        """Test optional authentication with valid API key."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer test-api-key-1"}
        
        payload = await optional_auth(mock_request)
        assert payload is not None
        assert payload["sub"] == "test-api-key-1"
    
    @pytest.mark.asyncio
    async def test_optional_auth_without_auth(self):
        """Test optional authentication without credentials."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        payload = await optional_auth(mock_request)
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_get_api_key_dependency_from_header(self):
        """Test API key extraction from X-API-Key header."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-API-Key": "test-api-key-1"}
        
        api_key = await get_api_key_dependency(mock_request)
        assert api_key == "test-api-key-1"
    
    @pytest.mark.asyncio
    async def test_get_api_key_dependency_from_authorization(self):
        """Test API key extraction from Authorization header."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer test-api-key-2"}
        
        api_key = await get_api_key_dependency(mock_request)
        assert api_key == "test-api-key-2"
    
    @pytest.mark.asyncio
    async def test_get_api_key_dependency_invalid(self):
        """Test API key extraction with invalid key."""
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer invalid-key"}
        
        api_key = await get_api_key_dependency(mock_request)
        assert api_key is None


# =============================================================================
# Authentication Backend Tests
# =============================================================================

class TestAuthenticationBackends:
    """Tests for authentication backends."""
    
    def test_jwt_authentication_backend(self, sample_token):
        """Test JWT authentication backend."""
        from fastapi import Request
        from unittest.mock import Mock
        from starlette.authentication import SimpleUser, AuthCredentials
        
        backend = JWTAuthenticationBackend()
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": f"Bearer {sample_token}"}
        
        import asyncio
        result = asyncio.run(backend.authenticate(mock_request))
        
        assert result is not None
        credentials, user = result
        assert isinstance(credentials, AuthCredentials)
        assert isinstance(user, SimpleUser)
        assert user.username == "testuser"
    
    def test_jwt_authentication_backend_no_header(self):
        """Test JWT authentication backend without authorization header."""
        from fastapi import Request
        from unittest.mock import Mock
        
        backend = JWTAuthenticationBackend()
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        import asyncio
        result = asyncio.run(backend.authenticate(mock_request))
        
        assert result is None
    
    def test_api_key_authentication_backend(self):
        """Test API key authentication backend."""
        from fastapi import Request
        from unittest.mock import Mock
        from starlette.authentication import SimpleUser, AuthCredentials
        
        backend = APIKeyAuthenticationBackend()
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer test-api-key-1"}
        
        import asyncio
        result = asyncio.run(backend.authenticate(mock_request))
        
        assert result is not None
        credentials, user = result
        assert isinstance(credentials, AuthCredentials)
        assert isinstance(user, SimpleUser)
    
    def test_api_key_authentication_backend_x_api_key_header(self):
        """Test API key authentication backend with X-API-Key header."""
        from fastapi import Request
        from unittest.mock import Mock
        from starlette.authentication import SimpleUser, AuthCredentials
        
        backend = APIKeyAuthenticationBackend()
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-API-Key": "test-api-key-2"}
        
        import asyncio
        result = asyncio.run(backend.authenticate(mock_request))
        
        assert result is not None
        credentials, user = result
        assert isinstance(credentials, AuthCredentials)
        assert isinstance(user, SimpleUser)
    
    def test_combined_authentication_backend_jwt_first(self, sample_token):
        """Test combined authentication backend prefers JWT."""
        from fastapi import Request
        from unittest.mock import Mock
        from starlette.authentication import SimpleUser
        
        backend = CombinedAuthenticationBackend()
        
        # Set up request with both JWT and API key (JWT should be preferred)
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": f"Bearer {sample_token}"}
        
        import asyncio
        result = asyncio.run(backend.authenticate(mock_request))
        
        assert result is not None
        _, user = result
        assert user.username == "testuser"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the authentication system."""
    
    def test_full_authentication_flow(self):
        """Test the full authentication flow."""
        # 1. Create a token
        token = create_access_token({"sub": "integration-test-user", "role": "admin"})
        
        # 2. Verify the token
        payload = verify_access_token(token)
        assert payload["sub"] == "integration-test-user"
        assert payload["role"] == "admin"
        
        # 3. Check token expiration
        assert not is_token_expired(token)
        
        # 4. Refresh the token
        refresh_token = create_refresh_token({"sub": "integration-test-user"})
        new_token = refresh_access_token(refresh_token)
        
        # 5. Verify new token
        new_payload = verify_access_token(new_token)
        assert new_payload["sub"] == "integration-test-user"
    
    def test_api_key_management_flow(self):
        """Test the API key management flow."""
        # 1. Add a new API key
        new_key = "integration-test-key"
        add_api_key(new_key)
        
        # 2. Verify it's in the list
        keys = get_valid_api_keys()
        assert new_key in keys
        
        # 3. Remove the key
        assert remove_api_key(new_key) is True
        
        # 4. Verify it's removed
        keys = get_valid_api_keys()
        assert new_key not in keys
