"""Pydantic DTOs for beans (a physical bag/lot)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.roaster import RoasterName, RoasterRead

Process = Literal["washed", "natural", "honey", "anaerobic", "carbonic_maceration", "other"]
RoastLevel = Literal["light", "medium_light", "medium", "medium_dark", "dark"]


class BeanBase(BaseModel):
    origin_country: str | None = Field(default=None, description="Country of origin.", examples=["Ethiopia"])
    region: str | None = Field(default=None, description="Growing region.", examples=["Guji"])
    producer: str | None = Field(default=None, description="Farm or producer.", examples=["Tabe Burka"])
    variety: str | None = Field(default=None, description="Coffee variety.", examples=["Heirloom"])
    process: Process | None = Field(default=None, description="Post-harvest process.", examples=["washed"])
    roast_level: RoastLevel | None = Field(default=None, description="Roast level.", examples=["medium_light"])
    roast_date: date | None = Field(default=None, description="Roast date.", examples=["2026-07-01"])
    purchase_date: date | None = Field(default=None, description="Purchase date.", examples=["2026-07-05"])
    weight_grams: int | None = Field(default=None, gt=0, description="Bag weight in grams.", examples=[250])
    price: Decimal | None = Field(default=None, ge=0, description="Price paid for the bag.", examples=["18.50"])
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
    is_finished: bool = Field(default=False, description="Whether the bag is used up.", examples=[False])


class BeanUpdate(BeanBase):
    """All fields optional; only provided fields are applied (PATCH semantics)."""

    name: str | None = Field(default=None, min_length=1, description="Coffee name.", examples=["Guji Natural"])
    roaster: RoasterName | None = Field(
        default=None,
        description="Move the bean to this roaster. Matched case-insensitively; created if it does not exist yet.",
        examples=["Nomad Coffee"],
    )
    is_finished: bool | None = Field(default=None, description="Whether the bag is used up.", examples=[True])


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    user_id: int = Field(description="Owner (who added the bean).", examples=[1])
    name: str = Field(examples=["Guji Natural"])
    roaster: RoasterRead = Field(description="The roaster this bean came from.")
    is_finished: bool = Field(examples=[False])
    created_at: datetime = Field(examples=["2026-07-05T09:30:00Z"])
