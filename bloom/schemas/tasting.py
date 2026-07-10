"""Pydantic DTOs for tastings (subjective evaluations of a brew)."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# A 1-10 subjective score (nullable), matching the DB CHECK constraints.
Score = Annotated[int | None, Field(default=None, ge=1, le=10)]


class TastingBase(BaseModel):
    aroma: Score = None
    acidity: Score = None
    sweetness: Score = None
    body: Score = None
    bitterness: Score = None
    aftertaste: Score = None
    overall: Score = None
    descriptors: list[str] = Field(default_factory=list)
    notes: str | None = None
    tasted_at: datetime | None = None


class TastingCreate(TastingBase):
    pass


class TastingUpdate(TastingBase):
    """Partial update; only provided fields are applied (PATCH semantics)."""

    descriptors: list[str] | None = None


class TastingRead(TastingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brew_id: int
