"""Middleware for multi-user authentication support."""

import base64
import logging
from typing import Callable, Awaitable

from httpx import BasicAuth
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)


class MultiUserAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle per-request authentication in multi-user mode."""
    
    def __init__(self, app, nextcloud_host: str):
        super().__init__(app)
        self.nextcloud_host = nextcloud_host
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and attach per-request NextcloudClient if needed."""
        
        # Check if Authorization header is present
        auth_header = request.headers.get("authorization")
        if not auth_header:
            # Return 401 with JSON error response for MCP compatibility
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": -32600,
                        "message": "Authorization header required in multi-user mode"
                    }
                }
            )
        
        # Parse Basic Authentication
        if not auth_header.startswith("Basic "):
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": -32600,
                        "message": "Only Basic authentication is supported"
                    }
                }
            )
        
        try:
            # Extract credentials
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            
            # Create per-request client
            nc_client = NextcloudClient(
                base_url=self.nextcloud_host,
                username=username,
                auth=BasicAuth(username, password)
            )
            
            # Attach client to request state
            request.state.nc_client = nc_client
            
            # Log request without credentials
            logger.debug(
                "Multi-user request: %s %s for user: %s",
                request.method,
                request.url.path,
                username
            )
            
            try:
                # Process request
                response = await call_next(request)
                return response
            finally:
                # Always cleanup the client
                await nc_client.close()
                
        except (ValueError, UnicodeDecodeError):
            # Malformed authorization header
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": -32600,
                        "message": "Invalid authorization header format"
                    }
                }
            )
        except Exception as e:
            # Handle any other errors (e.g., Nextcloud authentication failure)
            logger.error(f"Authentication error: {e}")
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": -32600,
                        "message": "Authentication failed"
                    }
                }
            )


def redact_auth_headers(headers):
    """Redact authorization headers for logging."""
    safe_headers = dict(headers)
    if "authorization" in safe_headers:
        safe_headers["authorization"] = "[REDACTED]"
    return safe_headers