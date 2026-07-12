"""Domain constants: brew-method categories and brewing-control-chart ranges.

Pure data only — no ORM, no FastAPI. Values use ``Decimal`` to stay consistent
with the ``NUMERIC`` columns they are compared against (never floating point).
"""

from decimal import Decimal
from typing import Final

# Mirror the CHECK on brew_method.category (bloom/db/models/brew_method.py).
CATEGORY_ESPRESSO: Final = "espresso"
CATEGORY_FILTER: Final = "filter"
CATEGORY_IMMERSION: Final = "immersion"

CATEGORIES: Final = (CATEGORY_ESPRESSO, CATEGORY_FILTER, CATEGORY_IMMERSION)

# Control-chart target ranges as (low, high) inclusive bounds. Espresso is far more
# concentrated, so its strength (TDS %) band differs; the yield band is shared.
STRENGTH_RANGE_FILTER: Final[tuple[Decimal, Decimal]] = (Decimal("1.15"), Decimal("1.35"))
STRENGTH_RANGE_ESPRESSO: Final[tuple[Decimal, Decimal]] = (Decimal("8.0"), Decimal("12.0"))
EY_RANGE: Final[tuple[Decimal, Decimal]] = (Decimal("18.0"), Decimal("22.0"))
