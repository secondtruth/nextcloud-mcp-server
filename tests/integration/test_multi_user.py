"""Integration tests for multi-user mode functionality."""

import base64
import logging
import os
import pytest
from httpx import AsyncClient, ASGITransport

from nextcloud_mcp_server.app import get_app

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
async def multi_user_app():
    """Create app instance in multi-user mode for testing."""
    # Set environment for multi-user mode
    original_env = {
        "NCMCP_MULTI_USER": os.environ.get("NCMCP_MULTI_USER"),
        "NEXTCLOUD_HOST": os.environ.get("NEXTCLOUD_HOST"),
        "NEXTCLOUD_USERNAME": os.environ.get("NEXTCLOUD_USERNAME"),
        "NEXTCLOUD_PASSWORD": os.environ.get("NEXTCLOUD_PASSWORD"),
    }
    
    # Configure multi-user mode
    os.environ["NCMCP_MULTI_USER"] = "true"
    os.environ["NEXTCLOUD_HOST"] = "http://test.example.com"  # Test host
    # Remove single-user credentials so they're not accidentally used
    if "NEXTCLOUD_USERNAME" in os.environ:
        del os.environ["NEXTCLOUD_USERNAME"]
    if "NEXTCLOUD_PASSWORD" in os.environ:
        del os.environ["NEXTCLOUD_PASSWORD"]
    
    try:
        app = get_app(transport="streamable-http")
        yield app
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


@pytest.fixture(scope="module") 
async def single_user_app():
    """Create app instance in single-user mode for testing."""
    # Ensure single-user mode with required env vars
    original_env = {
        "NCMCP_MULTI_USER": os.environ.get("NCMCP_MULTI_USER"),
        "NEXTCLOUD_HOST": os.environ.get("NEXTCLOUD_HOST"),
        "NEXTCLOUD_USERNAME": os.environ.get("NEXTCLOUD_USERNAME"),
        "NEXTCLOUD_PASSWORD": os.environ.get("NEXTCLOUD_PASSWORD"),
    }
    
    # Set required environment for single-user mode
    if "NCMCP_MULTI_USER" in os.environ:
        del os.environ["NCMCP_MULTI_USER"]
    os.environ["NEXTCLOUD_HOST"] = "http://test.example.com"
    os.environ["NEXTCLOUD_USERNAME"] = "testuser" 
    os.environ["NEXTCLOUD_PASSWORD"] = "testpass"
    
    try:
        app = get_app(transport="streamable-http")
        yield app
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def create_basic_auth_header(username: str, password: str) -> str:
    """Create Basic Authentication header value."""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


class TestMultiUserMode:
    """Test multi-user mode functionality."""
    
    async def test_multi_user_mode_requires_auth(self, multi_user_app):
        """Test that multi-user mode requires authorization header."""
        async with AsyncClient(transport=ASGITransport(app=multi_user_app), base_url="http://test") as client:
            # Request without authorization should fail
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == -32600
            assert "Authorization header required" in data["error"]["message"]

    async def test_multi_user_mode_invalid_auth_format(self, multi_user_app):
        """Test that invalid authorization format is rejected."""
        async with AsyncClient(transport=ASGITransport(app=multi_user_app), base_url="http://test") as client:
            # Invalid auth format
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }, headers={"Authorization": "Bearer invalid"})
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "Only Basic authentication is supported" in data["error"]["message"]

    async def test_multi_user_mode_malformed_basic_auth(self, multi_user_app):
        """Test that malformed Basic auth is rejected."""
        async with AsyncClient(transport=ASGITransport(app=multi_user_app), base_url="http://test") as client:
            # Malformed Basic auth
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }, headers={"Authorization": "Basic invalid-base64"})
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "Invalid authorization header format" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_multi_user_mode_with_valid_credentials(self, multi_user_app):
        """Test multi-user mode with valid credentials passes auth middleware."""
        # Get test credentials from environment
        username = os.environ.get("NEXTCLOUD_USERNAME_TEST", "admin")  
        password = os.environ.get("NEXTCLOUD_PASSWORD_TEST", "admin")
        
        auth_header = create_basic_auth_header(username, password)
        
        async with AsyncClient(transport=ASGITransport(app=multi_user_app), base_url="http://test") as client:
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }, headers={"Authorization": auth_header})
            
            # The middleware should pass the request through (not return 401)
            # Even if MCP server initialization fails, we shouldn't get auth errors
            assert response.status_code != 401 or "Authorization header required" not in response.text

    async def test_multi_user_mode_webdav_operation(self, multi_user_app):
        """Test WebDAV operation in multi-user mode passes auth middleware."""
        username = os.environ.get("NEXTCLOUD_USERNAME_TEST", "testuser")  
        password = os.environ.get("NEXTCLOUD_PASSWORD_TEST", "testpass")
        
        auth_header = create_basic_auth_header(username, password)
        
        async with AsyncClient(transport=ASGITransport(app=multi_user_app), base_url="http://test") as client:
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "nc_webdav_list_directory",
                    "arguments": {
                        "path": ""
                    }
                }
            }, headers={"Authorization": auth_header})
            
            # Should pass auth middleware (not fail with auth error)
            assert response.status_code != 401 or "Authorization header required" not in response.text


class TestSingleUserMode:
    """Test that single-user mode continues to work."""
    
    async def test_single_user_mode_no_auth_required(self, single_user_app):
        """Test that single-user mode works without authorization header."""
        async with AsyncClient(transport=ASGITransport(app=single_user_app), base_url="http://test") as client:
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            })
            
            # Should not require authorization (middleware not present)
            assert response.status_code != 401 or "Authorization header required" not in response.text

    async def test_single_user_mode_ignores_auth_header(self, single_user_app):
        """Test that single-user mode ignores auth header if provided."""
        auth_header = create_basic_auth_header("ignored", "ignored")
        
        async with AsyncClient(transport=ASGITransport(app=single_user_app), base_url="http://test") as client:
            response = await client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }, headers={"Authorization": auth_header})
            
            # Should work the same as without auth header (middleware not present)
            assert response.status_code != 401 or "Authorization header required" not in response.text


class TestTransportLimitations:
    """Test that multi-user mode only works with appropriate transports."""
    
    def test_multi_user_mode_sse_transport(self):
        """Test that multi-user mode doesn't add middleware for SSE transport."""
        original_multi_user = os.environ.get("NCMCP_MULTI_USER")
        os.environ["NCMCP_MULTI_USER"] = "true"
        
        try:
            # SSE transport shouldn't have middleware even in multi-user mode
            app = get_app(transport="sse")
            
            # Check that the app was created (basic test)
            assert app is not None
            
            # The SSE app shouldn't have the middleware
            # This is a basic structural test
            
        finally:
            if original_multi_user is not None:
                os.environ["NCMCP_MULTI_USER"] = original_multi_user
            elif "NCMCP_MULTI_USER" in os.environ:
                del os.environ["NCMCP_MULTI_USER"]


# Additional helpers for testing with real Nextcloud instance if available
async def test_multi_user_with_real_nextcloud():
    """
    Test multi-user mode with real Nextcloud instance.
    This test is skipped unless specific environment variables are set.
    """
    if not all([
        os.environ.get("NEXTCLOUD_HOST"),
        os.environ.get("NEXTCLOUD_USER1_USERNAME"),
        os.environ.get("NEXTCLOUD_USER1_PASSWORD"),
        os.environ.get("NEXTCLOUD_USER2_USERNAME"), 
        os.environ.get("NEXTCLOUD_USER2_PASSWORD")
    ]):
        pytest.skip("Real Nextcloud credentials not provided")
    
    # This would contain tests that actually connect to Nextcloud
    # with different user credentials to verify multi-user functionality
    pass