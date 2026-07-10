"""Pure brew calculations: ratio, extraction yield, and diagnostics.

These functions are framework-free — no ORM, no FastAPI, no database session —
which keeps them trivially unit-testable in isolation. Values are ``Decimal``
(ints are accepted too) to match the ``NUMERIC`` columns they originate from;
floats are intentionally not supported so no precision is silently lost.
"""

from dataclasses import dataclass
from decimal import Decimal

from bloom.domain import constants

# A NUMERIC-backed measurement: Decimal in production, int in tests/callers.
Measure = Decimal | int


@dataclass(frozen=True)
class ExtractionDiagnostics:
    """Where a brew sits against the brewing control chart.

    Each field is ``"below"``, ``"within"`` or ``"above"`` the target band, or
    ``None`` when the underlying measurement was not provided.
    """

    strength: str | None
    extraction: str | None


def brew_ratio(
    dose_grams: Measure | None,
    yield_grams: Measure | None,
    water_grams: Measure | None,
    category: str,
) -> Decimal | None:
    """Return the brew ratio (reference mass per gram of dose), or ``None``.

    The reference mass is the beverage ``yield_grams`` for espresso; for every
    other category it is ``water_grams`` when available, otherwise
    ``yield_grams``. Returns ``None`` when the dose is missing or non-positive,
    or when no usable reference mass is available.
    """
    if dose_grams is None or dose_grams <= 0:
        return None

    if category == constants.CATEGORY_ESPRESSO:
        reference = yield_grams
    else:
        reference = water_grams if _is_positive(water_grams) else yield_grams

    if not _is_positive(reference):
        return None

    return Decimal(reference) / Decimal(dose_grams)


def extraction_yield(
    tds_percent: Measure | None,
    yield_grams: Measure | None,
    dose_grams: Measure | None,
) -> Decimal | None:
    """Compute extraction yield % from TDS, beverage mass and dose.

    ``extraction_yield = (tds_percent * yield_grams) / dose_grams``. Returns
    ``None`` when TDS or beverage mass is missing, or when the dose is missing
    or non-positive.
    """
    if dose_grams is None or dose_grams <= 0:
        return None
    if tds_percent is None or yield_grams is None:
        return None

    return (Decimal(tds_percent) * Decimal(yield_grams)) / Decimal(dose_grams)


def strength_range_for(category: str) -> tuple[Decimal, Decimal]:
    """Return the target TDS % band for a brew-method category."""
    if category == constants.CATEGORY_ESPRESSO:
        return constants.STRENGTH_RANGE_ESPRESSO
    return constants.STRENGTH_RANGE_FILTER


def classify_extraction(
    tds_percent: Measure | None,
    extraction_yield_percent: Measure | None,
    category: str,
) -> ExtractionDiagnostics:
    """Classify a brew's strength and extraction against the control chart."""
    strength_low, strength_high = strength_range_for(category)
    ey_low, ey_high = constants.EY_RANGE
    return ExtractionDiagnostics(
        strength=_band(tds_percent, strength_low, strength_high),
        extraction=_band(extraction_yield_percent, ey_low, ey_high),
    )


def _is_positive(value: Measure | None) -> bool:
    """Return True when ``value`` is present and strictly greater than zero."""
    return value is not None and value > 0


def _band(
    value: Measure | None,
    low: Decimal,
    high: Decimal,
) -> str | None:
    """Locate ``value`` relative to an inclusive ``[low, high]`` target band."""
    if value is None:
        return None
    if value < low:
        return "below"
    if value > high:
        return "above"
    return "within"
