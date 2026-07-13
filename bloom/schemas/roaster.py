"""Pydantic DTOs for roasters."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from bloom.domain.naming import normalize_name


def _clean_name(value: str) -> str:
    name = normalize_name(value)
    if not name:
        raise ValueError("must not be blank")
    return name


RoasterName = Annotated[str, AfterValidator(_clean_name)]


class RoasterBase(BaseModel):
    country: str | None = Field(default=None, description="Country the roaster is based in.", examples=["Spain"])
    city: str | None = Field(default=None, description="City the roaster is based in.", examples=["Barcelona"])
    website: str | None = Field(default=None, description="Website.", examples=["https://nomadcoffee.es"])
    notes: str | None = Field(default=None, description="Your own notes.", examples=["Great subscriptions"])


class RoasterCreate(RoasterBase):
    name: RoasterName = Field(description="Roaster name (unique, case-insensitive).", examples=["Nomad Coffee"])


class RoasterUpdate(RoasterBase):
    """All fields optional; only provided fields are applied (PATCH semantics)."""

    name: RoasterName | None = Field(
        default=None,
        description="Rename the roaster — every bean referencing it follows.",
        examples=["Nomad Coffee Roasters"],
    )


class RoasterRead(RoasterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    name: str = Field(examples=["Nomad Coffee"])
    created_at: datetime = Field(examples=["2026-07-12T18:00:00Z"])


class RoasterMerge(BaseModel):
    source_id: int = Field(
        description="Roaster to merge away: its beans move to the target and it is deleted.",
        examples=[7],
    )
