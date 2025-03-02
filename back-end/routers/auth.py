import logging
from fastapi import APIRouter
from src.dependencies import SessionDep
from services.http_schema import LoginRequest, LoginResponse
from routers.srv.auth import (
    validate_user_name_and_password,
    create_or_update_user,
    read_roles,
)
from services.active_directory import authenticate_and_get_user
from src.exceptions import InvalidCredentialsException, InternalServerException

# Configure the logger for this module
logger = logging.getLogger(__name__)
router = APIRouter()


async def authenticate_admin(
    session: SessionDep, username: str, password: str
):
    """
    Authenticate an admin user using internal validation.

    Args:
        session (SessionDep): Database session dependency.
        username (str): The username (expected to be 'admin').
        password (str): The provided password.

    Raises:
        InvalidCredentialsException: If the credentials are incorrect.

    Returns:
        user: The authenticated admin user.
    """
    user = await validate_user_name_and_password(session, username, password)
    if not user:
        logger.warning("Admin authentication failed for user: %s", username)
        raise InvalidCredentialsException()
    return user


async def authenticate_ad_and_update(
    session: SessionDep, username: str, password: str
):
    """
    Authenticate a user via Active Directory and create or update their record in the database.

    Args:
        session (SessionDep): Database session dependency.
        username (str): The provided username.
        password (str): The provided password.

    Raises:
        InvalidCredentialsException: If Active Directory authentication fails.
        InternalServerException: If user creation or update fails.

    Returns:
        user: The authenticated and updated user record.
    """
    windows_account = await authenticate_and_get_user(username, password)
    if not windows_account:
        logger.warning(
            "Active Directory authentication failed for user: %s", username
        )
        raise InvalidCredentialsException()

    user = await create_or_update_user(
        session,
        windows_account.username,
        windows_account.fullName,
        windows_account.title,
    )
    if not user:
        logger.error(
            "Failed to create or update user record for: %s", username
        )
        raise InternalServerException()

    return user


async def get_user_roles(session: SessionDep, user) -> list:
    """
    Retrieve user roles based on admin status.

    Args:
        session (SessionDep): Database session dependency.
        user: The authenticated user object.

    Returns:
        list: A list of roles associated with the user.
    """
    if user.is_super_admin:
        roles = await read_roles(session)
    else:
        roles = await read_roles(session, user.id)
    return roles


@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    session: SessionDep, form_data: LoginRequest
) -> LoginResponse:
    """
    Authenticate the user and return user data.

    Args:
        session (SessionDep): Database session dependency.
        form_data (LoginRequest): Login credentials (username and password).

    Raises:
        InvalidCredentialsException: If the credentials are incorrect.
        InternalServerException: If an unexpected error occurs.

    Returns:
        LoginResponse: Authenticated user's data.
    """
    logger.info(
        "Login attempt for user: %s",
        form_data.username if form_data else "unknown",
    )
    try:
        if not form_data or not form_data.username or not form_data.password:
            logger.warning("Missing username or password in login attempt")
            raise InvalidCredentialsException()

        username = form_data.username
        password = form_data.password

        if username == "admin":
            user = await authenticate_admin(session, username, password)
        else:
            user = await authenticate_ad_and_update(
                session, username, password
            )

        roles = await get_user_roles(session, user)
        logger.info(
            "User %s authenticated successfully with roles: %s",
            username,
            roles,
        )

        response = LoginResponse(
            userId=user.id,
            username=user.username,
            email=f"{user.username}@andalusiagroup.net",
            fullName=user.full_name,
            title=user.title,
            roles=roles,
        )
        return response

    except InvalidCredentialsException as e:
        logger.error(
            "Invalid credentials provided for user: %s", form_data.username
        )
        raise e

    except Exception as e:
        logger.exception(
            "An unexpected error occurred during login for user: %s",
            form_data.username,
        )
        raise InternalServerException()
