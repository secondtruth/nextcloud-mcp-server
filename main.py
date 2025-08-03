import asyncio
import logging

from nextcloud_mcp_server.client import NextcloudClient

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

client = NextcloudClient.from_env()


async def main():
    addressbooks = await client.contacts.list_addressbooks()
    # print(addressbooks)

    for addressbook in addressbooks:
        contacts = await client.contacts.list_contacts(addressbook=addressbook["name"])
        for contact in contacts:
            logger.info(
                "Contact etag: %s, details: %s", contact["getetag"], contact["contact"]
            )


if __name__ == "__main__":
    asyncio.run(main())
