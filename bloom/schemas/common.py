"""Shared building blocks for the DTOs."""

from typing import Any

from pydantic import field_validator


def reject_null(*fields: str) -> Any:
    """Reject an explicit ``null`` on PATCH fields backed by a NOT NULL column.

    A PATCH DTO types every field as ``T | None`` so that omitting it means "leave
    unchanged". That makes an explicit ``"field": null`` indistinguishable from
    omission at the type level, and it would reach the database as a NOT NULL
    violation (a 500) instead of a validation error. Pydantic does not validate
    unset defaults, so this only fires when the key is actually present in the body.
    """

    def _check(value: Any) -> Any:
        if value is None:
            raise ValueError("must not be null; omit the field to leave it unchanged")
        return value

    return field_validator(*fields)(_check)
