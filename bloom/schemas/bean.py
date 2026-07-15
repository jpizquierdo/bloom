"""Pydantic DTOs for beans (the coffee concept; purchases live in bean_lot)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.common import reject_null
from bloom.schemas.roaster import RoasterName, RoasterRead
from bloom.schemas.user import AuthorRead

Process = Literal["washed", "natural", "honey", "anaerobic", "carbonic_maceration", "other"]
RoastLevel = Literal["light", "medium_light", "medium", "medium_dark", "dark"]


class BeanBase(BaseModel):
    origin_country: str | None = Field(default=None, description="Country of origin.", examples=["Ethiopia"])
    region: str | None = Field(default=None, description="Growing region.", examples=["Guji"])
    producer: str | None = Field(default=None, description="Farm or producer.", examples=["Tabe Burka"])
    variety: str | None = Field(default=None, description="Coffee variety.", examples=["Heirloom"])
    process: Process | None = Field(default=None, description="Post-harvest process.", examples=["washed"])
    roast_level: RoastLevel | None = Field(default=None, description="Roast level.", examples=["medium_light"])
    altitude_masl: int | None = Field(default=None, description="Growing altitude (metres above sea level).", examples=[2100])
    tasting_notes_label: str | None = Field(
        default=None,
        description="Tasting notes printed on the bag.",
        examples=["Peach, jasmine, black tea"],
    )
    notes: str | None = Field(default=None, description="Your own notes.", examples=["Great as filter"])


class BeanCreate(BeanBase):
    name: str = Field(min_length=1, description="Coffee name.", examples=["Guji Natural"])
    roaster: RoasterName = Field(
        description="Roaster name. Matched case-insensitively; created if it does not exist yet.",
        examples=["Nomad Coffee"],
    )


class BeanUpdate(BeanBase):
    """All fields optional; only provided fields are applied (PATCH semantics)."""

    name: str | None = Field(default=None, min_length=1, description="Coffee name.", examples=["Guji Natural"])
    roaster: RoasterName | None = Field(
        default=None,
        description="Move the bean to this roaster. Matched case-insensitively; created if it does not exist yet.",
        examples=["Nomad Coffee"],
    )

    _no_null = reject_null("name", "roaster")


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    user_id: int = Field(description="Owner id (who added the bean).", examples=[1])
    owner: AuthorRead = Field(description="Owner (who added the bean).")
    name: str = Field(examples=["Guji Natural"])
    roaster: RoasterRead = Field(description="The roaster this bean came from.")
    created_at: datetime = Field(examples=["2026-07-05T09:30:00Z"])
