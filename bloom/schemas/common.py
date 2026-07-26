"""Shared building blocks for the DTOs."""

from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, Field, field_validator

from bloom.domain.naming import normalize_name


class Message(BaseModel):
    """A human-readable outcome, for endpoints with nothing else to return."""

    message: str = Field(examples=["If that email is registered, a reset link is on its way."])


def _clean_name(value: str) -> str:
    name = normalize_name(value)
    if not name:
        raise ValueError("must not be blank")
    return name


# Names that are matched case-insensitively (roasters) or compared for duplicates
# (beans): normalized on the way in so spacing never decides whether two rows differ.
CleanName = Annotated[str, AfterValidator(_clean_name)]


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
