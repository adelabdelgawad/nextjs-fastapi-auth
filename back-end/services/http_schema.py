from pydantic import BaseModel, ConfigDict
from typing import List


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    userId: int | None = None
    username: str | None = None
    fullName: str | None = None
    title: str | None = None
    email: str | None = None
    roles: List[str] | None = []

    model_config = ConfigDict(from_attributes=True)
