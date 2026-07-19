"""Pydantic DTOs for beans (the coffee concept; purchases live in bean_lot)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.common import reject_null
from bloom.schemas.roaster import RoasterName, RoasterRead
from bloom.schemas.user import AuthorRead

Process = Literal["washed", "natural", "honey", "anaerobic", "carbonic_maceration", "other"]
RoastLevel = Literal["light", "medium_light", "medium", "medium_dark", "dark"]
RoastType = Literal["filter", "espresso", "omni", "unknown"]
Blend = Literal["single_origin", "blend", "unknown"]


class BeanBase(BaseModel):
    origin_country: str | None = Field(default=None, description="Country of origin.", examples=["Ethiopia"])
    region: str | None = Field(default=None, description="Growing region.", examples=["Guji"])
    producer: str | None = Field(default=None, description="Farm or producer.", examples=["Tabe Burka"])
    variety: str | None = Field(default=None, description="Coffee variety.", examples=["Heirloom"])
    process: Process | None = Field(default=None, description="Post-harvest process.", examples=["washed"])
    roast_level: RoastLevel | None = Field(default=None, description="Roast level.", examples=["medium_light"])
    roast_type: RoastType = Field(default="unknown", description="Brewing intent this coffee is roasted for.", examples=["filter"])
    blend: Blend = Field(default="single_origin", description="Single origin or a blend.", examples=["single_origin"])
    altitude_masl: int | None = Field(default=None, description="Growing altitude (metres above sea level).", examples=[2100])
    tasting_notes_label: str | None = Field(
        default=None,
        description="Tasting notes printed on the bag.",
        examples=["Peach, jasmine, black tea"],
    )
    rating: int | None = Field(default=None, ge=1, le=5, description="Overall rating of the coffee itself, 1–5 (null = unrated).", examples=[4])
    website: str | None = Field(
        default=None,
        description="URL with more info about the coffee or roaster.",
        examples=["https://nomadcoffee.es"],
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
    # NOT NULL-backed: re-declared optional so an explicit null is rejected (below) rather than
    # silently type-erroring; omitting the field leaves it unchanged (PATCH). rating is nullable
    # (null = unrated), so an explicit null is allowed to clear it — like the tasting scores.
    roast_type: RoastType | None = Field(default=None, description="Brewing intent this coffee is roasted for.", examples=["filter"])
    blend: Blend | None = Field(default=None, description="Single origin or a blend.", examples=["single_origin"])

    _no_null = reject_null("name", "roaster", "roast_type", "blend")


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    user_id: int = Field(description="Owner id (who added the bean).", examples=[1])
    owner: AuthorRead = Field(description="Owner (who added the bean).")
    name: str = Field(examples=["Guji Natural"])
    roaster: RoasterRead = Field(description="The roaster this bean came from.")
    created_at: datetime = Field(examples=["2026-07-05T09:30:00Z"])
