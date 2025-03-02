from datetime import datetime, timedelta, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
ALGORITHM = "HS256"
TOKEN_RENEW_THRESHOLD_MINUTES = 15
ACCESS_TOKEN_EXPIRE_MINUTES = 20


class TokenRenewalMiddleware(BaseHTTPMiddleware):
    """
    Middleware to renew JWT token if it's close to expiration.
    """

    async def dispatch(self, request: Request, call_next):
        # Extract token from cookies
        token = request.cookies.get("access_token")
        if not token:
            return await call_next(request)

        try:
            # Decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            now = datetime.now(timezone.utc)

            # Check if the token is close to expiration
            time_remaining = (exp - now).total_seconds() / 60
            if time_remaining <= TOKEN_RENEW_THRESHOLD_MINUTES:
                # Generate a new token with extended expiration
                new_exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                payload["exp"] = int(new_exp.timestamp())
                new_token = jwt.encode(
                    payload, SECRET_KEY, algorithm=ALGORITHM)

                # Add the new token to the response cookies
                response = await call_next(request)
                response.set_cookie(
                    key="access_token",
                    value=new_token,
                    httponly=True,
                    secure=True,  # Adjust based on environment
                    samesite="Lax",
                    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                )
                return response

        except jwt.ExpiredSignatureError:
            # If the token is expired, return an unauthorized response
            return JSONResponse(
                {"detail": "Token expired. Please log in again."},
                status_code=401,
            )
        except JWTError:
            # For other token errors, proceed without modifying the request
            pass

        return await call_next(request)
