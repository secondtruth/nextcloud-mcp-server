"""CardDAV client for NextCloud contacts operations."""

import logging
from .base import BaseNextcloudClient
import xml.etree.ElementTree as ET
from pythonvCard4.vcard import Contact

logger = logging.getLogger(__name__)


class ContactsClient(BaseNextcloudClient):
    """Client for NextCloud CardDAV contact operations."""

    def _get_carddav_base_path(self) -> str:
        """Helper to get the base CardDAV path for contacts."""
        return f"/remote.php/dav/addressbooks/users/{self.username}"

    async def list_addressbooks(self):
        """List all available addressbooks for the user."""

        carddav_path = self._get_carddav_base_path()

        propfind_body = """<?xml version="1.0" encoding="utf-8"?>
        <d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
            <d:prop>
                <d:displayname/>
                <d:getctag />
            </d:prop>
        </d:propfind>"""

        headers = {
            # "Depth": "0",
            "Content-Type": "application/xml",
            "Accept": "application/xml",
        }

        response = await self._make_request(
            "PROPFIND", carddav_path, content=propfind_body, headers=headers
        )

        ns = {"d": "DAV:"}

        # logger.info(response.content)
        root = ET.fromstring(response.content)
        addressbooks = []
        for response_elem in root.findall(".//d:response", ns):
            href = response_elem.find(".//d:href", ns)
            if href is None:
                continue

            href_text = href.text or ""
            if not href_text.endswith("/"):
                continue  # Skip non-addressbook resources

            # Extract addressbook name from href
            addressbook_name = href_text.rstrip("/").split("/")[-1]
            if not addressbook_name or addressbook_name == self.username:
                continue

            # Get properties
            propstat = response_elem.find(".//d:propstat", ns)
            if propstat is None:
                continue

            prop = propstat.find(".//d:prop", ns)
            if prop is None:
                continue

            displayname_elem = prop.find(".//d:displayname", ns)
            displayname = (
                displayname_elem.text
                if displayname_elem is not None
                else addressbook_name
            )

            getctag_elem = prop.find(".//d:getctag", ns)
            getctag = getctag_elem.text if getctag_elem is not None else None

            addressbooks.append(
                {
                    "name": addressbook_name,
                    "display_name": displayname,
                    "getctag": getctag,
                }
            )

        logger.debug(f"Found {len(addressbooks)} addressbooks")
        return addressbooks

    async def create_addressbook(self, *, name: str, display_name: str):
        """Create a new addressbook."""
        carddav_path = self._get_carddav_base_path()
        url = f"{carddav_path}/{name}/"

        prop_body = f"""<?xml version="1.0" encoding="utf-8"?>
        <d:mkcol xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
            <d:set>
                <d:prop>
                    <d:resourcetype>
                        <d:collection/>
                        <c:addressbook/>
                    </d:resourcetype>
                    <d:displayname>{display_name}</d:displayname>
                </d:prop>
            </d:set>
        </d:mkcol>"""

        headers = {
            "Content-Type": "application/xml",
        }

        await self._make_request("MKCOL", url, content=prop_body, headers=headers)

    async def delete_addressbook(self, *, name: str):
        """Delete an addressbook."""
        carddav_path = self._get_carddav_base_path()
        url = f"{carddav_path}/{name}/"
        await self._make_request("DELETE", url)

    async def create_contact(self, *, addressbook: str, uid: str, contact_data: dict):
        """Create a new contact."""
        carddav_path = self._get_carddav_base_path()
        url = f"{carddav_path}/{addressbook}/{uid}.vcf"

        contact = Contact(fn=contact_data.get("fn"), uid=uid)
        if "email" in contact_data:
            contact.email = [{"value": contact_data["email"], "type": ["HOME"]}]
        if "tel" in contact_data:
            contact.tel = [{"value": contact_data["tel"], "type": ["HOME"]}]

        vcard = contact.to_vcard()

        headers = {
            "Content-Type": "text/vcard; charset=utf-8",
            "If-None-Match": "*",
        }

        await self._make_request("PUT", url, content=vcard, headers=headers)

    async def delete_contact(self, *, addressbook: str, uid: str):
        """Delete a contact."""
        carddav_path = self._get_carddav_base_path()
        url = f"{carddav_path}/{addressbook}/{uid}.vcf"
        await self._make_request("DELETE", url)

    async def list_contacts(self, *, addressbook: str):
        """List all available contacts for addressbook."""

        carddav_path = self._get_carddav_base_path()

        report_body = """<?xml version="1.0" encoding="utf-8"?>
        <card:addressbook-query xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
            <d:prop>
                <d:getetag />
                <card:address-data />
            </d:prop>
        </card:addressbook-query>"""

        headers = {
            "Depth": "1",
            "Content-Type": "application/xml",
            "Accept": "application/xml",
        }

        response = await self._make_request(
            "REPORT",
            f"{carddav_path}/{addressbook}",
            content=report_body,
            headers=headers,
        )

        ns = {"d": "DAV:", "card": "urn:ietf:params:xml:ns:carddav"}

        # logger.info(response.text)
        root = ET.fromstring(response.content)
        contacts = []
        for response_elem in root.findall(".//d:response", ns):
            href = response_elem.find(".//d:href", ns)
            if href is None:
                logger.info("Skip missing href")
                continue

            href_text = href.text or ""
            # logger.info("Href text: %s", href_text)
            # if not href_text.endswith("/"):
            # logger.info("# Skip non-addressbook resources")
            # continue

            # Extract vcard id from href
            vcard_id = href_text.rstrip("/").split("/")[-1]
            if not vcard_id:
                logger.info("Skip missing vcard_id")
                continue
            vcard_id = vcard_id.replace(".vcf", "")

            # Get properties
            propstat = response_elem.find(".//d:propstat", ns)
            if propstat is None:
                logger.info("Skip missing propstat")
                continue

            prop = propstat.find(".//d:prop", ns)
            if prop is None:
                logger.info("Skip missing prop")
                continue

            getetag_elem = prop.find(".//d:getetag", ns)
            getetag = getetag_elem.text if getetag_elem is not None else None

            addressdata_elem = prop.find(".//card:address-data", ns)
            addressdata = (
                addressdata_elem.text if addressdata_elem is not None else None
            )
            if addressdata is None:
                logger.info("Skip missing addressdata")
                continue

            contact = Contact.from_vcard(addressdata)

            contacts.append(
                {
                    "vcard_id": vcard_id,
                    "getetag": getetag,
                    "contact": {
                        "fullname": contact.fn,
                        "nickname": contact.nickname,
                        "birthday": contact.bday,
                        "email": contact.email,
                    },
                    "addressdata": addressdata,
                }
            )

        logger.debug(f"Found {len(contacts)} contacts")
        return contacts
