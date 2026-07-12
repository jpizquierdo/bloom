"""Pydantic DTOs for tastings (subjective evaluations of a brew)."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# A 1-10 subjective score (nullable), matching the DB CHECK constraints.
Score = Annotated[
    int | None, Field(default=None, ge=1, le=10, description="Score from 1 to 10.", examples=[8])
]


class TastingBase(BaseModel):
    aroma: Score = None
    acidity: Score = None
    sweetness: Score = None
    body: Score = None
    bitterness: Score = None
    aftertaste: Score = None
    overall: Score = None
    descriptors: list[str] = Field(
        default_factory=list,
        description="Flavor descriptors.",
        examples=[["peach", "jasmine"]],
    )
    notes: str | None = Field(
        default=None, description="Free-form notes.", examples=["Juicy, clean finish"]
    )
    tasted_at: datetime | None = Field(
        default=None,
        description="When tasted (defaults to now).",
        examples=["2026-07-12T08:10:00Z"],
    )


class TastingCreate(TastingBase):
    pass


class TastingUpdate(TastingBase):
    """Partial update; only provided fields are applied (PATCH semantics)."""

    descriptors: list[str] | None = Field(
        default=None, description="Flavor descriptors.", examples=[["peach"]]
    )


class TastingRead(TastingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    brew_id: int = Field(examples=[1])
    user_id: int = Field(description="Taster (who scored the brew).", examples=[1])
