"""Unit tests for the eval's answer comparison (no database or Gemini needed)."""
from datetime import date
from decimal import Decimal

from harness import results_match


def test_same_values_under_different_column_names_match():
    assert results_match([{"count": 7}], [{"active_subscriptions": 7}])


def test_extra_predicted_columns_are_fine():
    gold = [{"subscription_name": "A"}, {"subscription_name": "B"}]
    pred = [{"id": 1, "subscription_name": "B", "plan": "x"}, {"id": 2, "subscription_name": "A", "plan": "y"}]
    assert results_match(gold, pred)


def test_row_order_ignored_unless_ordered():
    gold = [{"n": "A"}, {"n": "B"}]
    pred = [{"n": "B"}, {"n": "A"}]
    assert results_match(gold, pred)
    assert not results_match(gold, pred, ordered=True)


def test_missing_or_extra_rows_do_not_match():
    assert not results_match([{"n": "A"}, {"n": "B"}], [{"n": "A"}])
    assert not results_match([{"n": "A"}], [{"n": "A"}, {"n": "C"}])


def test_wrong_value_does_not_match():
    assert not results_match([{"total": Decimal("7960.00")}], [{"total": Decimal("7961.00")}])


def test_numeric_and_date_types_are_normalised():
    assert results_match([{"x": Decimal("9.545454")}], [{"y": 9.55}])
    assert results_match([{"d": date(2026, 10, 12)}], [{"d": date(2026, 10, 12)}])


def test_rows_must_stay_together():
    # Each column matches on its own, but the pairs are mixed up
    gold = [{"name": "A", "price": 1}, {"name": "B", "price": 2}]
    pred = [{"name": "A", "price": 2}, {"name": "B", "price": 1}]
    assert not results_match(gold, pred)


def test_empty_results():
    assert results_match([], [])
    assert not results_match([], [{"n": 1}])
