"""User account model (role-based, soft-deletable)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean import Bean


class User(Base):
    """An account with a role (``admin`` / ``user``); owns beans and brews.

    Users are never hard-deleted — ``is_active`` toggles access instead — so
    brew history is always preserved.
    """

    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user')", name="ck_user_role"),
        CheckConstraint("btrim(username) <> ''", name="ck_user_username_not_blank"),
        Index("uq_user_username_lower", text("lower(username)"), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # Login handle, unique case-insensitively. Set by an admin today; will be
    # supplied by the IdP (Keycloak/Authentik) once automated provisioning lands.
    username: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    # Bumped on every password change; a reset token issued before it is refused, which is
    # what makes a reset link single-use. Stamped from the app clock, the same one that
    # signs the tokens it is compared against — the server_default only backfills old rows.
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=func.now()
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'user'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    beans: Mapped[list[Bean]] = relationship(back_populates="owner")
