"""Pydantic DTOs for beans (a physical bag/lot)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Process = Literal[
    "washed", "natural", "honey", "anaerobic", "carbonic_maceration", "other"
]
RoastLevel = Literal["light", "medium_light", "medium", "medium_dark", "dark"]


class BeanBase(BaseModel):
    origin_country: str | None = None
    region: str | None = None
    producer: str | None = None
    variety: str | None = None
    process: Process | None = None
    roast_level: RoastLevel | None = None
    roast_date: date | None = None
    purchase_date: date | None = None
    weight_grams: int | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, ge=0)
    altitude_masl: int | None = None
    tasting_notes_label: str | None = None
    notes: str | None = None


class BeanCreate(BeanBase):
    name: str = Field(min_length=1)
    roaster: str = Field(min_length=1)
    is_finished: bool = False


class BeanUpdate(BeanBase):
    """All fields optional; only provided fields are applied (PATCH semantics)."""

    name: str | None = Field(default=None, min_length=1)
    roaster: str | None = Field(default=None, min_length=1)
    is_finished: bool | None = None


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    roaster: str
    is_finished: bool
    created_at: datetime
