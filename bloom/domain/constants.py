"""Domain constants: brew-method categories and brewing-control-chart ranges.

Pure data only — no ORM, no FastAPI. Values use ``Decimal`` to stay consistent
with the ``NUMERIC`` columns they are compared against (never floating point).
"""

from decimal import Decimal
from typing import Final

# Brew-method categories. These mirror the CHECK constraint on
# ``brew_method.category`` in schema.sql.
CATEGORY_ESPRESSO: Final = "espresso"
CATEGORY_FILTER: Final = "filter"
CATEGORY_IMMERSION: Final = "immersion"

CATEGORIES: Final = (CATEGORY_ESPRESSO, CATEGORY_FILTER, CATEGORY_IMMERSION)

# Brewing control chart target ranges, expressed as (low, high) inclusive bounds.
#
# Strength is measured as TDS %. The band depends on the category: espresso is a
# far more concentrated beverage than filter/immersion, so it uses its own scale.
# Extraction yield % shares a single target band across all categories.
STRENGTH_RANGE_FILTER: Final[tuple[Decimal, Decimal]] = (Decimal("1.15"), Decimal("1.35"))
STRENGTH_RANGE_ESPRESSO: Final[tuple[Decimal, Decimal]] = (Decimal("8.0"), Decimal("12.0"))
EY_RANGE: Final[tuple[Decimal, Decimal]] = (Decimal("18.0"), Decimal("22.0"))
