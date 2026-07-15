"""Pydantic DTOs for brews (the central extraction entity)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.common import reject_null
from bloom.schemas.user import AuthorRead


class BrewBase(BaseModel):
    lot_id: int | None = Field(
        default=None,
        description="Optional: the physical lot this brew came from (must belong to the bean).",
        examples=[1],
    )
    grinder_id: int | None = Field(default=None, description="Grinder used (equipment id).", examples=[1])
    brewed_at: datetime | None = Field(
        default=None,
        description="When it was brewed (defaults to now).",
        examples=["2026-07-12T08:00:00Z"],
    )
    yield_grams: Decimal | None = Field(default=None, gt=0, description="Beverage mass in the cup (g).", examples=["250"])
    water_grams: Decimal | None = Field(default=None, gt=0, description="Water used (g); for filter/immersion.", examples=["250"])
    grind_setting: str | None = Field(default=None, description="Grinder setting (grinder-specific).", examples=["18"])
    water_temp_celsius: Decimal | None = Field(default=None, description="Water temperature (°C).", examples=["93.0"])
    brew_time_seconds: int | None = Field(default=None, gt=0, description="Total brew time (s).", examples=[150])
    tds_percent: Decimal | None = Field(default=None, ge=0, description="Measured TDS % (refractometer).", examples=["1.35"])
    extraction_yield_percent: Decimal | None = Field(
        default=None,
        ge=0,
        description="Extraction yield %; computed and stored from TDS if omitted.",
        examples=["22.50"],
    )
    notes: str | None = Field(default=None, description="Free-form notes.", examples=["Even extraction"])


class BrewCreate(BrewBase):
    bean_id: int = Field(description="Bean brewed (any shared bean).", examples=[1])
    method_id: int = Field(description="Brew method id.", examples=[1])
    dose_grams: Decimal = Field(gt=0, description="Dry coffee dose (g).", examples=["15"])


class BrewUpdate(BrewBase):
    """Partial update. bean_id/method_id are immutable after creation."""

    dose_grams: Decimal | None = Field(default=None, gt=0, description="Dry coffee dose (g).", examples=["15"])

    _no_null = reject_null("dose_grams")


class ExtractionDiagnosticsRead(BaseModel):
    """Where the brew sits on the brewing control chart."""

    strength: str | None = Field(description="TDS band: below / within / above target.", examples=["within"])
    extraction: str | None = Field(description="Extraction-yield band: below / within / above target.", examples=["above"])


class BrewRead(BrewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    user_id: int = Field(description="Author id (who prepared the brew).", examples=[1])
    author: AuthorRead = Field(description="Author (who prepared the brew).")
    bean_id: int = Field(examples=[1])
    method_id: int = Field(examples=[1])
    dose_grams: Decimal = Field(examples=["15"])

    ratio: Decimal | None = Field(default=None, description="Computed brew ratio (never stored).", examples=["16.67"])
    diagnostics: ExtractionDiagnosticsRead | None = None
