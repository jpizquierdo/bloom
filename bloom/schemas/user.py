"""Pydantic v2 DTOs for users and authentication tokens."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from bloom.schemas.common import reject_null

Role = Literal["admin", "user"]

# A login handle: unique (case-insensitive), lowercase letters/digits and . _ -.
_USERNAME_PATTERN = r"^[a-z0-9_.-]+$"


class UserCreate(BaseModel):
    """Payload for creating a user (admin-only). New users default to role 'user'."""

    email: EmailStr = Field(description="Login email (unique).", examples=["barista@example.com"])
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=_USERNAME_PATTERN,
        description="Login handle (unique). Lowercase letters, digits, and . _ - only.",
        examples=["barista"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plaintext password (8-128 chars); stored hashed.",
        examples=["s3cure-passw0rd"],
    )


class UserUpdate(BaseModel):
    """Admin-editable user fields: rename, promote/demote and activate/deactivate."""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=_USERNAME_PATTERN,
        description="New login handle (unique).",
        examples=["head-barista"],
    )
    role: Role | None = Field(default=None, description="New role.", examples=["admin"])
    is_active: bool | None = Field(default=None, description="Activate or deactivate the account.", examples=[False])

    _no_null = reject_null("username", "role", "is_active")


class AuthorRead(BaseModel):
    """Minimal public projection of a user, embedded as the author of a brew or tasting."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    username: str = Field(description="Author's handle.", examples=["barista"])


class UserRead(BaseModel):
    """Public representation of a user (never exposes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    email: str = Field(examples=["barista@example.com"])
    username: str = Field(examples=["barista"])
    role: str = Field(examples=["user"])
    is_active: bool = Field(examples=[True])
    created_at: datetime = Field(examples=["2026-07-05T09:30:00Z"])


class Token(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str = Field(description="JWT access token.", examples=["eyJhbGciOiJIUzI1Ni..."])
    token_type: str = Field(default="bearer", examples=["bearer"])
