"""Pydantic DTOs for the shared lookup tables (brew_method, equipment)."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BrewCategory = Literal["espresso", "filter", "immersion"]
EquipmentType = Literal["grinder", "espresso_machine", "kettle", "other"]


class BrewMethodCreate(BaseModel):
    name: str = Field(min_length=1)
    category: BrewCategory
    default_ratio: Decimal | None = Field(default=None, gt=0)


class BrewMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    default_ratio: Decimal | None


class EquipmentCreate(BaseModel):
    type: EquipmentType
    name: str = Field(min_length=1)
    brand: str | None = None
    notes: str | None = None


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: str
    brand: str | None
    notes: str | None
    created_at: datetime
