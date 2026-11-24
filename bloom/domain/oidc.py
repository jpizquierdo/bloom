"""Pure rules for OpenID Connect logins: reading claims, mapping groups to roles, usernames."""

import re
from typing import Any

USERNAME_MAX_LENGTH = 32
_USERNAME_INVALID = re.compile(r"[^a-z0-9_.-]+")


def claim_at(claims: dict[str, Any], path: str) -> Any:
    """Read a possibly nested claim with dot notation (``realm_access.roles``); ``None`` if absent."""
    value: Any = claims
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def groups_from(claims: dict[str, Any], path: str) -> set[str]:
    """The groups found at ``path``, accepting a list or a single string."""
    value = claim_at(claims, path)
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {str(item) for item in value}
    return set()


def resolve_role(groups: set[str], admin_groups: set[str], allowed_groups: set[str], current_role: str) -> str | None:
    """The role an SSO login ends up with, or ``None`` when it must be refused.

    With ``admin_groups`` set the IdP is authoritative and the role is synced (promote and
    demote); without it the stored role is kept. Admins always pass ``allowed_groups``.
    """
    role = ("admin" if groups & admin_groups else "user") if admin_groups else current_role
    if allowed_groups and role != "admin" and not groups & allowed_groups:
        return None
    return role


def username_from_claims(preferred_username: str | None, email: str | None) -> str:
    """A valid Bloom username (``^[a-z0-9_.-]{3,32}$``) from the IdP's username or email."""
    local_part = email.split("@", 1)[0] if email else None
    for raw in (preferred_username, local_part):
        if raw:
            candidate = _USERNAME_INVALID.sub("-", raw.lower()).strip("-")[:USERNAME_MAX_LENGTH]
            if len(candidate) >= 3:
                return candidate
    return "user"


def with_suffix(username: str, n: int) -> str:
    """``username`` made unique with ``-n``, still within the length limit."""
    suffix = f"-{n}"
    return username[: USERNAME_MAX_LENGTH - len(suffix)] + suffix
