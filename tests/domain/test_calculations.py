"""Unit tests for the pure brew calculations."""

from decimal import Decimal

import pytest

from bloom.domain import constants
from bloom.domain.calculations import (
    ExtractionDiagnostics,
    brew_ratio,
    classify_extraction,
    extraction_yield,
    strength_range_for,
)

D = Decimal


class TestBrewRatio:
    def test_espresso_uses_yield_as_reference(self) -> None:
        # 36 g out / 18 g dose = 1:2
        assert brew_ratio(D("18"), D("36"), None, constants.CATEGORY_ESPRESSO) == D("2")

    def test_espresso_ignores_water(self) -> None:
        # Water is irrelevant for espresso; yield is the reference even if water is set.
        assert brew_ratio(D("18"), D("36"), D("500"), constants.CATEGORY_ESPRESSO) == D("2")

    def test_filter_uses_water_as_reference(self) -> None:
        assert brew_ratio(D("15"), None, D("250"), constants.CATEGORY_FILTER) == D("250") / D("15")

    def test_filter_falls_back_to_yield_when_water_missing(self) -> None:
        assert brew_ratio(D("15"), D("240"), None, constants.CATEGORY_FILTER) == D("240") / D("15")

    def test_immersion_behaves_like_filter(self) -> None:
        assert brew_ratio(D("16"), None, D("256"), constants.CATEGORY_IMMERSION) == D("16")

    def test_water_zero_falls_back_to_yield(self) -> None:
        assert brew_ratio(D("15"), D("240"), D("0"), constants.CATEGORY_FILTER) == D("240") / D("15")

    def test_accepts_int_arguments(self) -> None:
        assert brew_ratio(18, 36, None, constants.CATEGORY_ESPRESSO) == D("2")

    @pytest.mark.parametrize("dose", [D("0"), D("-1"), None])
    def test_missing_or_nonpositive_dose_returns_none(self, dose: Decimal | None) -> None:
        assert brew_ratio(dose, D("36"), D("250"), constants.CATEGORY_FILTER) is None

    def test_espresso_missing_yield_returns_none(self) -> None:
        assert brew_ratio(D("18"), None, D("250"), constants.CATEGORY_ESPRESSO) is None

    def test_filter_missing_water_and_yield_returns_none(self) -> None:
        assert brew_ratio(D("15"), None, None, constants.CATEGORY_FILTER) is None

    def test_nonpositive_reference_returns_none(self) -> None:
        assert brew_ratio(D("18"), D("-5"), None, constants.CATEGORY_ESPRESSO) is None


class TestExtractionYield:
    def test_typical_computation(self) -> None:
        # (1.35 * 250) / 15 = 22.5
        assert extraction_yield(D("1.35"), D("250"), D("15")) == D("22.5")

    def test_zero_tds_yields_zero(self) -> None:
        assert extraction_yield(D("0"), D("250"), D("15")) == D("0")

    def test_accepts_int_arguments(self) -> None:
        assert extraction_yield(2, 200, 20) == D("20")

    @pytest.mark.parametrize("dose", [D("0"), D("-3"), None])
    def test_missing_or_nonpositive_dose_returns_none(self, dose: Decimal | None) -> None:
        assert extraction_yield(D("1.35"), D("250"), dose) is None

    def test_missing_tds_returns_none(self) -> None:
        assert extraction_yield(None, D("250"), D("15")) is None

    def test_missing_yield_returns_none(self) -> None:
        assert extraction_yield(D("1.35"), None, D("15")) is None


class TestStrengthRangeFor:
    def test_espresso_range(self) -> None:
        assert strength_range_for(constants.CATEGORY_ESPRESSO) == constants.STRENGTH_RANGE_ESPRESSO

    def test_filter_range(self) -> None:
        assert strength_range_for(constants.CATEGORY_FILTER) == constants.STRENGTH_RANGE_FILTER

    def test_immersion_uses_filter_range(self) -> None:
        assert strength_range_for(constants.CATEGORY_IMMERSION) == constants.STRENGTH_RANGE_FILTER


class TestClassifyExtraction:
    def test_ideal_filter_brew_is_within_both_bands(self) -> None:
        result = classify_extraction(D("1.25"), D("20"), constants.CATEGORY_FILTER)
        assert result == ExtractionDiagnostics(strength="within", extraction="within")

    def test_weak_and_under_extracted(self) -> None:
        result = classify_extraction(D("1.0"), D("16"), constants.CATEGORY_FILTER)
        assert result == ExtractionDiagnostics(strength="below", extraction="below")

    def test_strong_and_over_extracted(self) -> None:
        result = classify_extraction(D("1.5"), D("24"), constants.CATEGORY_FILTER)
        assert result == ExtractionDiagnostics(strength="above", extraction="above")

    def test_espresso_uses_espresso_strength_scale(self) -> None:
        # TDS 10% is "within" for espresso but far "above" the filter scale.
        assert classify_extraction(D("10"), D("20"), constants.CATEGORY_ESPRESSO).strength == "within"
        assert classify_extraction(D("10"), D("20"), constants.CATEGORY_FILTER).strength == "above"

    def test_band_boundaries_are_inclusive(self) -> None:
        low = classify_extraction(D("1.15"), D("18"), constants.CATEGORY_FILTER)
        high = classify_extraction(D("1.35"), D("22"), constants.CATEGORY_FILTER)
        assert low == ExtractionDiagnostics(strength="within", extraction="within")
        assert high == ExtractionDiagnostics(strength="within", extraction="within")

    def test_missing_measurements_produce_none_bands(self) -> None:
        result = classify_extraction(None, None, constants.CATEGORY_FILTER)
        assert result == ExtractionDiagnostics(strength=None, extraction=None)
