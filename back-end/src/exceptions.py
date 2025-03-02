from fastapi import HTTPException, status


class InvalidCredentialsException(HTTPException):
    """Exception for invalid username or password."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )


class NetworkErrorException(HTTPException):
    """Exception for network issues."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Network Connection Error",
        )


class InternalServerException(HTTPException):
    """Exception for internal server errors."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
