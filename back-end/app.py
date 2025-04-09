import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyCookie
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

# --- Configuration and Constants ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_dev_key_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_INTERVAL_HOURS = 1  # How often refresh is allowed
MAX_TOKEN_LIFETIME_DAYS = 7
COOKIE_NAME = "access_token"
# --- Set secure flag based on environment ---
# Set SECURE_COOKIE=False for local HTTP development if needed
# In production (HTTPS), this should be True
SECURE_COOKIE = os.getenv("SECURE_COOKIE", "True").lower() == "true"


# --- Data Models ---
class UserPayload(BaseModel):
    userId: int
    username: str
    fullname: str
    title: str
    email: EmailStr
    roles: List[int]  # 1: admin, 2: user


class LoginRequest(BaseModel):
    username: str


# --- Hard-Coded User Store ---
users_db: Dict[str, UserPayload] = {
    "admin_user": UserPayload(
        userId=101,
        username="admin_user",
        fullname="Admin Von Admin",
        title="System Administrator",
        email="admin@example.com",
        roles=[1, 2],
    ),
    "regular_user": UserPayload(
        userId=202,
        username="regular_user",
        fullname="Reginald User",
        title="Standard User",
        email="user@example.com",
        roles=[2],
    ),
}


# --- JWT Utility Functions ---
def create_jwt_token(
    user: UserPayload, existing_max_exp: Optional[float] = None
) -> str:
    """Generates JWT. Optionally reuses existing max_exp for refresh."""
    now = datetime.now(timezone.utc)
    access_expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    # Use provided max_exp if refreshing, otherwise calculate new one
    max_expire_ts = existing_max_exp
    if max_expire_ts is None:
        max_expire = now + timedelta(days=MAX_TOKEN_LIFETIME_DAYS)
        # Ensure max_expire isn't accidentally shorter than access_expire
        effective_max_expire = max(access_expire, max_expire)
        max_expire_ts = effective_max_expire.timestamp()

    to_encode = {
        "sub": user.username,
        "iat": now,
        "exp": access_expire,
        "max_exp": max_expire_ts,  # Use consistent or new max_exp
        **user.model_dump(),
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> UserPayload:
    """Validates JWT: signature, standard expiry (exp), and max lifetime (max_exp)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
    )
    max_lifetime_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Maximum token lifetime exceeded. Please log in again.",
    )

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )  # Checks signature and 'exp'
        username: str = payload.get("sub")
        max_exp_ts: float = payload.get("max_exp")

        if username is None or max_exp_ts is None:
            print("Verification Error: Missing sub or max_exp claim.")
            raise credentials_exception

        # Verify max lifetime hasn't passed (redundant if exp is shorter, but good practice)
        if datetime.now(timezone.utc).timestamp() > max_exp_ts:
            print(
                f"Verification Error: Token max lifetime exceeded for user {username}"
            )
            raise max_lifetime_exception

        user_payload = UserPayload(**payload)

    except jwt.ExpiredSignatureError:
        print("Verification Info: Token signature/exp has expired.")
        raise token_expired_exception  # Raise specific exception for expired 'exp'
    except JWTError as e:
        print(f"Verification Error: JWTError - {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Verification Error: Unexpected - {type(e).__name__} - {e}")
        raise credentials_exception

    return user_payload


def attach_token_to_response(response: Response, token: str):
    """Attaches the JWT token as a secure, HttpOnly cookie."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        exp_timestamp = payload.get("exp")
        max_age = ACCESS_TOKEN_EXPIRE_HOURS * 60 * 60  # Default fallback
        if exp_timestamp:
            now = datetime.now(timezone.utc)
            expire_dt = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            max_age_seconds = int((expire_dt - now).total_seconds())
            max_age = max(0, max_age_seconds)  # Ensure non-negative

        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            secure=SECURE_COOKIE,  # Use configured value
            samesite="lax",
            max_age=max_age,
            path="/",
        )
        print(
            f"Cookie '{COOKIE_NAME}' attached. Max-Age: {max_age}s, Secure: {SECURE_COOKIE}"
        )
    except JWTError as e:
        print(
            f"Error attaching cookie: Failed to decode token to get exp - {e}"
        )
        # Optionally still try to set cookie with default max_age or handle error


# --- Cookie Scheme and Dependencies ---
cookie_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)


async def get_token_data_for_refresh(request: Request) -> tuple[str, dict]:
    """Dependency specifically for refresh: gets token, decodes basic claims without full verification."""
    token = request.cookies.get(COOKIE_NAME)
    print(
        f"Refresh: Attempting to get cookie '{COOKIE_NAME}'. Found: {'Yes' if token else 'No'}"
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token cookie for refresh",
        )

    try:
        # Decode only signature initially to get claims needed for refresh checks
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
        if (
            not payload.get("sub")
            or not payload.get("iat")
            or not payload.get("max_exp")
        ):
            print(
                "Refresh Error: Initial decode missing sub, iat, or max_exp."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token structure for refresh",
            )
        return token, payload
    except JWTError as e:
        print(f"Refresh Error: Initial JWT decode failed - {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )


async def get_current_user(token: str = Depends(cookie_scheme)) -> UserPayload:
    """Dependency for protected routes: extracts cookie and fully verifies token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return verify_jwt_token(token)  # Use standard verification


async def get_current_admin_user(
    current_user: UserPayload = Depends(get_current_user),
) -> UserPayload:
    """Dependency ensuring user has admin role."""
    if 1 not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )
    return current_user


# --- FastAPI Application Setup ---
app = FastAPI(title="Secure Auth API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.post("/login")
async def login(login_data: LoginRequest, response: Response):
    user = users_db.get(login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
        )
    token = create_jwt_token(user)
    attach_token_to_response(response, token)
    print(f"Login successful for: {user.username}")
    return {"message": "Login successful"}

@app.post("/refresh")
async def refresh_token(
    response: Response,
    token_data: tuple[str, dict] = Depends(get_token_data_for_refresh),
):
    """Refreshes token if conditions met (within max lifetime, and after the refresh interval)."""
    token, payload = token_data
    username: str = payload["sub"]
    max_exp_ts: float = payload["max_exp"]
    issued_at_ts: float = payload["iat"]

    print(
        f"Refresh: Processing for user '{username}'. MaxExpTS: {max_exp_ts}, IatTS: {issued_at_ts}"
    )

    now_ts = datetime.now(timezone.utc).timestamp()

    # 1. Check maximum lifetime
    if now_ts > max_exp_ts:
        print(f"Refresh Denied: Max lifetime exceeded for {username}.")
        raise HTTPException(
            status_code=401,
            detail="Maximum session lifetime exceeded. Please log in again.",
        )

    # 2. Check refresh interval (next allowed refresh time)
    refresh_allowed_at_ts = issued_at_ts + timedelta(hours=REFRESH_INTERVAL_HOURS).total_seconds()
    if now_ts < refresh_allowed_at_ts:
        print(
            f"Refresh Info: Interval not met for {username}. Now: {now_ts}, Allowed after: {refresh_allowed_at_ts}"
        )
        return {
            "message": "Refresh interval not met, try again later.",
            "refresh_success": False,
            "next_refresh_allowed_at": refresh_allowed_at_ts,
        }

    # 3. Full verification of the original token to ensure it was not tampered with
    try:
        verify_jwt_token(token)
        print(
            f"Refresh Info: Original token for {username} is still valid, but refresh interval met. Issuing new token."
        )
    except HTTPException as e:
        if e.status_code == 401 and "expired" in e.detail.lower():
            print(
                f"Refresh Info: Original token for {username} has expired (expected). Proceeding."
            )
        else:
            print(
                f"Refresh Denied: Unexpected validation error on original token: {e.detail} ({e.status_code})"
            )
            raise e

    # 4. Issue new token
    user = users_db.get(username)
    if not user:
        print(f"Refresh Error: User '{username}' disappeared from DB.")
        raise HTTPException(status_code=500, detail="Internal inconsistency")

    new_token = create_jwt_token(user, existing_max_exp=max_exp_ts)
    attach_token_to_response(response, new_token)
    print(f"Refresh Successful: New token issued for {username}")
    return {"message": "Token refreshed successfully", "refresh_success": True}

@app.get("/protected/page1", response_model=UserPayload)
async def read_protected_page1(
    current_user: UserPayload = Depends(get_current_user),
):
    return current_user


@app.get("/protected/page2", response_model=UserPayload)
async def read_protected_page2(
    admin_user: UserPayload = Depends(get_current_admin_user),
):
    return admin_user


@app.post("/logout")
async def logout(response: Response):
    print("Logout: Clearing cookie.")
    response.delete_cookie(
        key=COOKIE_NAME,
        secure=SECURE_COOKIE,  # Match settings
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"message": "Logout successful"}


@app.get("/")
async def root():
    return {"message": "Welcome to the Secure Auth API"}
