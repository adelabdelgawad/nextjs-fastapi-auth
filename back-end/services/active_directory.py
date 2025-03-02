import asyncio
import os
import logging
from typing import List, Optional, Union

import bonsai
from bonsai.errors import AuthenticationError, LDAPError
from dotenv import load_dotenv
from src.schemas import DomainUser  # Ensure this path is correct

# Logger configuration
logger = logging.getLogger(__name__)

# Fix Windows event loop issue
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# LDAP Environment variables
LDAP_URL: str = os.getenv("LDAP_URL", "")
LDAP_USER: str = os.getenv("LDAP_USER", "")
LDAP_PASSWORD: str = os.getenv("LDAP_PASSWORD", "")

# Organization Units (OUs) to search
SEARCH_BASES: List[str] = [
    "OU=Users,OU=SMH,OU=Andalusia,DC=andalusia,DC=loc",
    "OU=Users,OU=ARC,OU=Andalusia,DC=andalusia,DC=loc",
    "OU=Users,OU=ANC,OU=Andalusia,DC=andalusia,DC=loc",
]


async def search_ldap(
    ou: str, username: Optional[str] = None
) -> Union[List[DomainUser], Optional[DomainUser]]:
    """
    Search LDAP for a user or list of users in a specific Organizational Unit (OU).

    Args:
        ou (str): The Organizational Unit (OU) to search within.
        username (Optional[str]): The username (sAMAccountName) to search for (optional).

    Returns:
        Union[List[DomainUser], Optional[DomainUser]]:
        - A `DomainUser` object if searching for a single user.
        - A list of `DomainUser` objects if searching for all users in an OU.
        - `None` if no results found.
    """
    client = bonsai.LDAPClient(LDAP_URL)
    client.set_credentials("SIMPLE", user=LDAP_USER, password=LDAP_PASSWORD)

    try:
        async with client.connect(is_async=True) as conn:
            logger.info(f"Connected to LDAP: {LDAP_URL}")

            attributes: List[str] = ["sAMAccountName", "displayName", "title"]

            if username:
                search_filter = f"(sAMAccountName={username})"
                result = await conn.search(ou, 2, search_filter, attributes)

                if not result:
                    logger.warning(f"User '{username}' not found in {ou}.")
                    return None

                return DomainUser(
                    id=0,  # Temporary ID, will be set later
                    username=result.get("sAMAccountName", ["N/A"])[0],
                    fullName=result.get("displayName", ["N/A"])[0],
                    title=result.get("title", ["N/A"])[0],
                )

            # Search for all active users
            search_filter = "(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
            results = await conn.search(ou, 2, search_filter, attributes)

            if not results:
                logger.warning(f"No users found in {ou}.")
                return []

            logger.info(f"Found {len(results)} users in {ou}")

            return [
                DomainUser(
                    id=0,  # Temporary ID, will be set later
                    username=entry.get("sAMAccountName", ["N/A"])[0],
                    fullName=entry.get("displayName", ["N/A"])[0],
                    title=entry.get("title", ["N/A"])[0],
                )
                for entry in results
            ]

    except LDAPError as e:
        logger.error(f"LDAP error during search in {ou}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during LDAP search in {ou}: {e}")
    return None


async def authenticate_and_get_user(
    username: str, password: str
) -> Optional[DomainUser]:
    """
    Authenticate a user against LDAP and return a DomainUser object if successful.

    Args:
        username (str): The username (sAMAccountName) to validate.
        password (str): The password for authentication.

    Returns:
        Optional[DomainUser]: The authenticated DomainUser object if valid credentials, else None.
    """
    if not username or not password:
        logger.warning("Username or password not provided.")
        return None

    user_dn = f"{username}@andalusia.loc"  # Adjust based on domain format

    client = bonsai.LDAPClient(LDAP_URL)
    client.set_credentials("SIMPLE", user=user_dn, password=password)

    try:
        async with client.connect(is_async=True, timeout=5) as conn:
            logger.info(f"User {username} authenticated successfully.")

            # Search the entire Andalusia organizational unit
            base_dn = "OU=Andalusia,DC=andalusia,DC=loc"
            search_filter = f"(sAMAccountName={username})"
            attributes = ["sAMAccountName", "displayName", "title"]

            # Perform a search in the entire OU=Andalusia
            results = await conn.search(base_dn, 2, search_filter, attributes)

            if not results:
                logger.warning(
                    f"Authenticated user {username} not found in LDAP records."
                )
                return None

            # Extract the first user found
            entry = results[0]
            return DomainUser(
                id=0,  # Temporary ID
                username=entry.get("sAMAccountName", ["N/A"])[0],
                fullName=entry.get("displayName", ["N/A"])[0],
                title=entry.get("title", ["N/A"])[0],
            )

    except AuthenticationError:
        logger.warning(f"Authentication failed for user {username}.")
        return None

    except LDAPError as e:
        logger.error(f"LDAP error during authentication for {username}: {e}")
        return None

    except Exception as e:
        logger.error(
            f"Unexpected error during authentication for {username}: {e}"
        )
        return None

    return None


async def read_domain_users() -> List[DomainUser]:
    """
    Perform parallel searches on multiple Organizational Units (OUs) to fetch domain users.

    Returns:
        List[DomainUser]: A list of all users from all specified OUs.
    """
    tasks = [search_ldap(ou) for ou in SEARCH_BASES]
    results = await asyncio.gather(*tasks)

    # Flatten and filter out any None results
    all_users: List[DomainUser] = [
        user for sublist in results if sublist for user in sublist
    ]

    # Assign unique IDs
    for i, user in enumerate(all_users, start=1):
        user.id = i

    logger.info(f"Total domain users retrieved: {len(all_users)}")
    return all_users
