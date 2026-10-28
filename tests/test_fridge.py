"""Партии, точное количество, сроки и JSON упражнения Холодильник."""

from datetime import date
from decimal import Decimal

import pytest

from exercises.fridge import add, amount, expired, find, load, save


def test_batches_dates_and_json(tmp_path):
    goods = {}
    add(goods, "Молоко", "0.1", "2026-10-27")
    add(goods, "Молоко", "0.2", "2026-10-28")
    add(goods, "Рис", "2")
    assert amount(goods, "МОЛ") == Decimal("0.3")
    assert find(goods, "рис") == ["Рис"]
    assert expired(goods, date(2026, 10, 28)) == [("Молоко", Decimal("0.1"))]
    path = tmp_path / "fridge.json"
    save(goods, path)
    assert load(path) == goods


@pytest.mark.parametrize("quantity", ["0", "-1", "bad", "NaN", "Infinity"])
def test_invalid_quantity(quantity):
    goods = {}
    with pytest.raises(ValueError):
        add(goods, "Молоко", quantity)
    assert goods == {}


def test_invalid_date():
    with pytest.raises(ValueError):
        add({}, "Молоко", "1", "2026-02-30")
