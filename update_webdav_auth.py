#!/usr/bin/env python
import sys
import os
import base64
from nextcloud_mcp_server.client import NextcloudClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webdav_auth():
    """
    Test function to verify WebDAV authentication and compare with current implementation.
    """
    # Create client using standard method
    client = NextcloudClient.from_env()
    print("Client authentication type:", type(client._client.auth).__name__)
    
    # Get WebDAV base path
    username = os.environ["NEXTCLOUD_USERNAME"]
    password = os.environ["NEXTCLOUD_PASSWORD"]
    webdav_base = client._get_webdav_base_path()
    
    # Test path for Notes directory
    notes_path = f"{webdav_base}/Notes"
    print(f"Testing WebDAV access to: {notes_path}")
    
    # 1. Test with existing client auth
    try:
        print("\nTest 1: Using existing client authentication")
        response = client._client.request("PROPFIND", notes_path, headers={"Depth": "0"})
        print(f"Status code: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error: {response.text}")
        else:
            print("Success! Current auth method works")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # 2. Test with explicit Authorization header
    try:
        print("\nTest 2: Using explicit Authorization header")
        # Create base64 encoded credentials
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_auth = base64_bytes.decode('ascii')
        
        # Make request with explicit Authorization header
        headers = {
            "Depth": "0",
            "Authorization": f"Basic {base64_auth}"
        }
        
        # Use client without auth to test explicit header
        response = client._client.request(
            "PROPFIND", 
            notes_path, 
            headers=headers,
            auth=None  # Override client auth
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error: {response.text}")
        else:
            print("Success! Explicit authorization header works")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(test_webdav_auth())
