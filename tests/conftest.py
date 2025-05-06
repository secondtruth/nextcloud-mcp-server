import pytest
import os
import logging
from nextcloud_mcp_server.client import NextcloudClient

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def nc_client() -> NextcloudClient:
    """
    Fixture to create a NextcloudClient instance for integration tests.
    """
    assert os.getenv("NEXTCLOUD_HOST"), "NEXTCLOUD_HOST env var not set"
    assert os.getenv("NEXTCLOUD_USERNAME"), "NEXTCLOUD_USERNAME env var not set"
    assert os.getenv("NEXTCLOUD_PASSWORD"), "NEXTCLOUD_PASSWORD env var not set"
    return NextcloudClient.from_env()
