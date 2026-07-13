"""Normalisation of user-supplied names."""

import pytest

from bloom.domain.naming import normalize_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Nomad Coffee", "Nomad Coffee"),  # already clean: unchanged
        ("  Nomad Coffee  ", "Nomad Coffee"),  # surrounding whitespace trimmed
        ("Nomad   Coffee", "Nomad Coffee"),  # inner run of spaces collapsed to one
        ("Nomad\tCoffee\nRoasters", "Nomad Coffee Roasters"),  # tabs/newlines are whitespace too
        ("nomad coffee", "nomad coffee"),  # capitalisation is preserved, never forced
        ("   ", ""),  # blank input normalises to empty (callers reject it)
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected
