from typing import List, Optional
from datetime import datetime
import pytz
from sqlmodel import Field, Relationship, SQLModel

# Default timezone
cairo_tz = pytz.timezone("Africa/Cairo")


class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] | None = None

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="role"
    )
    permission_logs_admin: Optional["LogRolePermission"] = Relationship(
        back_populates="role"
    )


class Account(SQLModel, table=True):
    __tablename__ = "account"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(nullable=False, unique=True, max_length=64)
    full_name: Optional[str] | None = None
    password: Optional[str] | None = None
    title: Optional[str] | None = None
    is_domain_user: Optional[bool] | None = None
    is_super_admin: Optional[bool] | None = None

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="account"
    )


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permission"

    id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="role.id", nullable=False)
    account_id: int = Field(foreign_key="account.id", nullable=False)

    # Relationships
    role: Optional["Role"] = Relationship(back_populates="role_permissions")
    account: Optional["Account"] = Relationship(
        back_populates="role_permissions"
    )


class LogRolePermission(SQLModel, table=True):
    __tablename__ = "log_role_permission"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", nullable=False)
    role_id: int = Field(foreign_key="role.id", nullable=False)
    admin_id: int = Field(foreign_key="account.id", nullable=False)
    action: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(cairo_tz))

    # Relationships
    role: Optional["Role"] = Relationship(
        back_populates="permission_logs_admin"
    )
