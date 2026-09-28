"""Pydantic DTOs for reusable bean recipes."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.common import (
    MAX_BREW_TIME_SECONDS,
    MAX_BREWING_MASS_GRAMS,
    MAX_BREWING_NOTES_LENGTH,
    MAX_GRIND_SETTING_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_TDS_PERCENT,
    MAX_WATER_TEMP_CELSIUS,
    CleanName,
    reject_null,
)
from bloom.schemas.user import AuthorRead


class RecipeParameters(BaseModel):
    grinder_id: int | None = Field(default=None, description="Grinder to use (equipment id).", examples=[1])
    yield_grams: Decimal | None = Field(
        default=None,
        gt=0,
        le=MAX_BREWING_MASS_GRAMS,
        description="Target beverage mass in the cup (g).",
        examples=["42"],
    )
    water_grams: Decimal | None = Field(
        default=None,
        gt=0,
        le=MAX_BREWING_MASS_GRAMS,
        description="Target water amount (g).",
        examples=["250"],
    )
    grind_setting: str | None = Field(
        default=None,
        max_length=MAX_GRIND_SETTING_LENGTH,
        description="Target grinder setting.",
        examples=["14"],
    )
    water_temp_celsius: Decimal | None = Field(
        default=None,
        ge=0,
        le=MAX_WATER_TEMP_CELSIUS,
        description="Target water temperature (°C).",
        examples=["94.0"],
    )
    brew_time_seconds: int | None = Field(
        default=None,
        gt=0,
        le=MAX_BREW_TIME_SECONDS,
        description="Target total brew time (s).",
        examples=[30],
    )


class RecipeCreate(RecipeParameters):
    name: CleanName = Field(
        max_length=MAX_RECIPE_NAME_LENGTH,
        description="Human-readable recipe name.",
        examples=["Brazil: recipe #1"],
    )
    method_id: int = Field(description="Brew method id.", examples=[1])
    dose_grams: Decimal = Field(
        gt=0,
        le=MAX_BREWING_MASS_GRAMS,
        description="Target dry coffee dose (g).",
        examples=["18"],
    )
    notes: str | None = Field(
        default=None,
        max_length=MAX_BREWING_NOTES_LENGTH,
        description="Notes about the recipe itself.",
        examples=["Start slightly coarser as it ages"],
    )


class RecipeUpdate(RecipeParameters):
    """Partial update; bean and creator are immutable."""

    name: CleanName | None = Field(
        default=None,
        max_length=MAX_RECIPE_NAME_LENGTH,
        description="Human-readable recipe name.",
        examples=["Brazil espresso"],
    )
    method_id: int | None = Field(default=None, description="Brew method id.", examples=[1])
    dose_grams: Decimal | None = Field(
        default=None,
        gt=0,
        le=MAX_BREWING_MASS_GRAMS,
        description="Target dry coffee dose (g).",
        examples=["18"],
    )
    notes: str | None = Field(
        default=None,
        max_length=MAX_BREWING_NOTES_LENGTH,
        description="Notes about the recipe itself.",
    )

    _no_null = reject_null("name", "method_id", "dose_grams")


class RecipeRead(RecipeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    bean_id: int = Field(description="Bean this recipe belongs to.", examples=[1])
    user_id: int = Field(description="Creator id.", examples=[1])
    owner: AuthorRead = Field(description="Creator of the recipe.")
    is_favorite: bool = Field(description="Whether the requesting user has favorited this recipe.")
    created_at: datetime = Field(examples=["2026-09-27T09:30:00Z"])


class BrewFromRecipeCreate(RecipeParameters):
    """Overrides and extraction-only values for a brew created from a recipe."""

    lot_id: int | None = Field(default=None, description="Optional physical lot used for this brew.", examples=[1])
    dose_grams: Decimal | None = Field(
        default=None,
        gt=0,
        le=MAX_BREWING_MASS_GRAMS,
        description="Override the recipe's dose (g).",
        examples=["18"],
    )
    brewed_at: datetime | None = Field(default=None, description="When it was brewed (defaults to now).")
    tds_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=MAX_TDS_PERCENT,
        description="Measured TDS % for this extraction.",
        examples=["1.35"],
    )
    notes: str | None = Field(
        default=None,
        max_length=MAX_BREWING_NOTES_LENGTH,
        description="Notes about this brew; recipe notes are never copied.",
    )

    _no_null = reject_null("dose_grams", "brewed_at")
