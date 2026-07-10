"""Pydantic v2 DTOs for users and authentication tokens."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "user"]


class UserCreate(BaseModel):
    """Payload for creating a user (admin-only). New users default to role 'user'."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Admin-editable user fields: promote/demote and activate/deactivate."""

    role: Role | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    """Public representation of a user (never exposes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str
    token_type: str = "bearer"
