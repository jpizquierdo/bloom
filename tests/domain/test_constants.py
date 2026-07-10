"""Unit tests for domain constants."""

from decimal import Decimal

from bloom.domain import constants


def test_categories_match_schema_check() -> None:
    assert constants.CATEGORY_ESPRESSO == "espresso"
    assert constants.CATEGORY_FILTER == "filter"
    assert constants.CATEGORY_IMMERSION == "immersion"
    assert constants.CATEGORIES == ("espresso", "filter", "immersion")


def test_ranges_are_decimal_low_below_high() -> None:
    for low, high in (
        constants.STRENGTH_RANGE_FILTER,
        constants.STRENGTH_RANGE_ESPRESSO,
        constants.EY_RANGE,
    ):
        assert isinstance(low, Decimal)
        assert isinstance(high, Decimal)
        assert low < high


def test_range_values() -> None:
    assert constants.STRENGTH_RANGE_FILTER == (Decimal("1.15"), Decimal("1.35"))
    assert constants.STRENGTH_RANGE_ESPRESSO == (Decimal("8.0"), Decimal("12.0"))
    assert constants.EY_RANGE == (Decimal("18.0"), Decimal("22.0"))
