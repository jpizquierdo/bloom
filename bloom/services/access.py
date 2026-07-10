"""Ownership helpers shared across resource services."""

from bloom.db.models.user import User


def owns_or_admin(user: User, owner_id: int) -> bool:
    """Return True if ``user`` owns the resource (``owner_id``) or is an admin."""
    return user.role == "admin" or owner_id == user.id
