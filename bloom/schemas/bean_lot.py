"""Pydantic DTOs for bean lots (a single physical purchase of a coffee)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from bloom.schemas.common import reject_null
from bloom.schemas.user import AuthorRead


class BeanLotBase(BaseModel):
    roast_date: date | None = Field(default=None, description="Roast date.", examples=["2026-07-01"])
    purchase_date: date | None = Field(default=None, description="Purchase date.", examples=["2026-07-05"])
    weight_grams: int | None = Field(default=None, gt=0, description="Bag weight in grams.", examples=[250])
    price: Decimal | None = Field(default=None, ge=0, description="Price paid for the bag.", examples=["18.50"])


class BeanLotCreate(BeanLotBase):
    is_finished: bool = Field(default=False, description="Whether the bag is used up.", examples=[False])


class BeanLotUpdate(BeanLotBase):
    """All fields optional; only provided fields are applied (PATCH semantics)."""

    is_finished: bool | None = Field(default=None, description="Whether the bag is used up.", examples=[True])

    _no_null = reject_null("is_finished")


class BeanLotRead(BeanLotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    bean_id: int = Field(examples=[1])
    user_id: int = Field(description="Owner id (who bought this bag).", examples=[1])
    owner: AuthorRead = Field(description="Owner (who bought this bag).")
    is_finished: bool = Field(examples=[False])
    created_at: datetime = Field(examples=["2026-07-05T09:30:00Z"])
