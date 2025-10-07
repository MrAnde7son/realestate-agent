"""Tests for Yad2 property type utilities."""

import pytest

from yad2.utils.property_types import PropertyTypeUtils


@pytest.mark.parametrize(
    "name, expected_code",
    [
        ("דירת גן", 3),
        ("גג", 6),
        ("בית פרטי", 39),
    ],
)
def test_hebrew_name_to_code_returns_canonical_mapping(name, expected_code):
    """Ensure the canonical Hebrew mapping returns the correct Yad2 code."""
    assert PropertyTypeUtils.hebrew_name_to_code(name) == expected_code


@pytest.mark.parametrize(
    "search_term, expected_name, expected_code",
    [
        ("דירת גן", "דירת גן", 3),
        ("גן", "דירת גן", 3),
        ("פנטהאוס", "מיני פנטהאוס", 6),
        ("גג", "גג", 6),
    ],
)
def test_search_hebrew_name_to_code_matches_canonical_results(
    search_term, expected_name, expected_code
):
    """Search results should reuse the canonical mapping values."""
    results = PropertyTypeUtils.search_hebrew_name_to_code(search_term)
    assert results, "Expected search to return at least one match"

    results_dict = {name: code for code, name in results}
    assert results_dict[expected_name] == expected_code
    assert results_dict[expected_name] == PropertyTypeUtils.hebrew_name_to_code(expected_name)


def test_search_results_are_sorted_by_name():
    """Ensure deterministic ordering for downstream callers and tests."""
    results = PropertyTypeUtils.search_hebrew_name_to_code("בית")
    sorted_names = sorted(name for _, name in results)
    assert [name for _, name in results] == sorted_names
