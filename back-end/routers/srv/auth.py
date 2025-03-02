import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from db.models import Account, Role, RolePermission
import bcrypt

# Configure logging
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


async def validate_user_name_and_password(
    session: AsyncSession, username: str, password: str
) -> Optional[Account]:
    """
    Fetch an account by username and validate the provided password.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        username (str): The username to search for.
        password (str): The plaintext password to verify.

    Returns:
        Optional[Account]: The found account instance if authenticated, otherwise None.
    """
    statement = select(Account).where(Account.username == username)
    result = await session.execute(statement)
    account = result.scalar_one_or_none()

    if account:
        # Use the stored hashed password directly.
        if bcrypt.checkpw(
            password.encode("utf-8"), account.password.encode("utf-8")
        ):
            logger.info(f"User '{username}' authenticated successfully.")
            return account
        else:
            logger.warning(
                f"Authentication failed for user '{username}': invalid password."
            )
    else:
        logger.warning(
            f"Authentication failed: no account found for user '{username}'."
        )

    return None


async def read_user_by_id(
    session: AsyncSession, user_id: int
) -> Optional[Account]:
    """
    Fetch an account by user_id.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        user_id (int): The int to search for.

    Returns:
        Optional[Account]: The found account instance or None.
    """
    statement = select(Account).where(Account.id == user_id)
    result = await session.execute(statement)
    account = result.scalar_one_or_none()

    if account:
        logger.info(f"User '{user_id}' found in database.")
    else:
        logger.warning(f"User '{user_id}' not found in database.")

    return account


async def create_or_update_user(
    session: AsyncSession, username: str, full_name: str, title: str
) -> Account:
    """
    Create or update a user account, ensuring the correct role assignment.

    If the account exists, update its full name and title.
    If not, create a new account with the given details.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        username (str): The username of the account.
        full_name (str): The full name of the user.
        title (str): The job title of the user.

    Returns:
        Account: The created or updated account instance.
    """
    statement = select(Account).where(Account.username == username)
    result = await session.execute(statement)
    account = result.scalar_one_or_none()

    if account:
        account.full_name = full_name
        account.title = title
        message = f"Updated user '{username}' in database."
    else:
        account = Account(
            username=username,
            full_name=full_name,
            title=title,
            is_domain_user=True,
        )
        session.add(account)
        message = f"Created new user '{username}' in database."

    await session.commit()
    await session.refresh(account)

    logger.info(message)

    # Assign default role (Role ID: 1) if it's a new user
    role_message = await ensure_user_has_role(session, account.id, 2, username)
    logger.info(role_message)

    return account


async def ensure_user_has_role(
    session: AsyncSession, account_id: int, role_id: int, username: str
):
    """
    Ensure the user has a specific role assigned.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        account_id (int): The account ID of the user.
        role_id (int): The role ID to be assigned.
        username (str): The username associated with the account.

    Returns:
        str: Message indicating role assignment result.
    """
    statement = select(RolePermission).where(
        RolePermission.account_id == account_id,
        RolePermission.role_id == role_id,
    )
    result = await session.execute(statement)
    existing_role = result.scalar_one_or_none()

    if existing_role:
        logger.info(
            f"Role ID {role_id} already assigned to user '{username}'."
        )
        return f"Role already assigned to user '{username}'."

    role_permission = RolePermission(role_id=role_id, account_id=account_id)
    session.add(role_permission)
    await session.commit()

    logger.info(f"Assigned Role ID {role_id} to user '{username}'.")
    return f"Role successfully assigned to user '{username}'."


async def read_roles(
    session: AsyncSession, account_id: Optional[int] = None
) -> List[str]:
    """
    Fetch the list of role names assigned to an account.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        account_id (int): The account ID to fetch roles for.

    Returns:
        List[str]: A list of role names associated with the given account.
    """
    if account_id:
        statement = (
            select(Role.name)
            .join(RolePermission, Role.id == RolePermission.role_id)
            .where(RolePermission.account_id == account_id)
        )
    else:
        statement = select(Role.name)

    results = await session.execute(statement)
    roles = results.scalars().all()

    if roles:
        logger.info(f"User ID {account_id} has roles: {roles}")
    else:
        logger.warning(f"User ID {account_id} has no assigned roles.")

    return roles
