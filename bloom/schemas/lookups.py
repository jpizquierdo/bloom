"""Pydantic DTOs for the shared lookup tables (brew_method, equipment)."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BrewCategory = Literal["espresso", "filter", "immersion"]
EquipmentType = Literal["grinder", "espresso_machine", "kettle", "other"]


class BrewMethodCreate(BaseModel):
    name: str = Field(min_length=1, description="Unique method name.", examples=["V60"])
    category: BrewCategory = Field(description="Brewing family the method belongs to.", examples=["filter"])
    default_ratio: Decimal | None = Field(
        default=None,
        gt=0,
        description="Optional default brew ratio (grams of water per gram of coffee).",
        examples=["16.00"],
    )


class BrewMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    name: str = Field(examples=["V60"])
    category: str = Field(examples=["filter"])
    default_ratio: Decimal | None = Field(examples=["16.00"])


class EquipmentCreate(BaseModel):
    type: EquipmentType = Field(description="Kind of equipment.", examples=["grinder"])
    name: str = Field(min_length=1, description="Model name.", examples=["Niche Zero"])
    brand: str | None = Field(default=None, description="Manufacturer.", examples=["Niche"])
    notes: str | None = Field(default=None, description="Free-form notes.", examples=["Single dosing"])


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    type: str = Field(examples=["grinder"])
    name: str = Field(examples=["Niche Zero"])
    brand: str | None = Field(examples=["Niche"])
    notes: str | None = Field(examples=["Single dosing"])
    created_at: datetime = Field(examples=["2026-07-12T18:00:00Z"])
