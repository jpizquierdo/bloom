"""Pure normalisation of user-supplied names (roasters today, more later)."""

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_name(raw: str) -> str:
    """Trim and collapse inner whitespace, keeping the caller's capitalisation.

    Capitalisation is preserved because it is part of a brand's identity, while
    matching is case-insensitive at the DB level (unique index on ``lower(name)``):
    ``"  nomad   coffee "`` and ``"Nomad Coffee"`` resolve to the same roaster.
    """
    return _WHITESPACE.sub(" ", raw).strip()
