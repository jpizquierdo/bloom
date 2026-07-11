"""Pydantic DTOs for brews (the central extraction entity)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BrewBase(BaseModel):
    grinder_id: int | None = None
    brewed_at: datetime | None = None
    yield_grams: Decimal | None = Field(default=None, gt=0)
    water_grams: Decimal | None = Field(default=None, gt=0)
    grind_setting: str | None = None
    water_temp_celsius: Decimal | None = None
    brew_time_seconds: int | None = Field(default=None, gt=0)
    tds_percent: Decimal | None = Field(default=None, ge=0)
    extraction_yield_percent: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class BrewCreate(BrewBase):
    bean_id: int
    method_id: int
    dose_grams: Decimal = Field(gt=0)


class BrewUpdate(BrewBase):
    """Partial update. bean_id/method_id are immutable after creation."""

    dose_grams: Decimal | None = Field(default=None, gt=0)


class ExtractionDiagnosticsRead(BaseModel):
    """Where the brew sits on the brewing control chart."""

    strength: str | None
    extraction: str | None


class BrewRead(BrewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int  # author — who prepared the brew
    bean_id: int
    method_id: int
    dose_grams: Decimal

    # Computed in the domain layer, never stored.
    ratio: Decimal | None = None
    diagnostics: ExtractionDiagnosticsRead | None = None
