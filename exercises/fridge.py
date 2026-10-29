from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def add(goods: dict, title: str, amount: str,
        expiration_date: str | None = None) -> None:
    title = title.strip()
    if not title:
        raise ValueError("Название продукта не должно быть пустым.")
    try:
        quantity = Decimal(str(amount))
    except InvalidOperation as error:
        raise ValueError("Неверное количество.") from error
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError("Количество должно быть положительным и конечным.")
    if expiration_date is not None:
        expiration_date = date.fromisoformat(expiration_date).isoformat()
    goods.setdefault(title, []).append({"amount": str(quantity),
                                       "expiration_date": expiration_date})


def find(goods: dict, query: str) -> list[str]:
    return [name for name in goods if query.casefold() in name.casefold()]


def amount(goods: dict, query: str) -> Decimal:
    return sum((Decimal(batch["amount"]) for name in find(goods, query)
                for batch in goods[name]), Decimal("0"))


def expired(goods: dict, on_date: date) -> list[tuple[str, Decimal]]:
    result = []
    for title, batches in goods.items():
        quantity = Decimal("0")
        for batch in batches:
            deadline = batch["expiration_date"]
            if deadline is not None and date.fromisoformat(deadline) < on_date:
                quantity += Decimal(batch["amount"])
        if quantity:
            result.append((title, quantity))
    return result


def save(goods: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(goods, stream, ensure_ascii=False, indent=2)


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise ValueError("Ожидался словарь продуктов.")
    goods = {}
    try:
        for title, batches in raw.items():
            if not isinstance(batches, list):
                raise ValueError("Ожидался список партий.")
            for batch in batches:
                add(goods, title, batch["amount"], batch["expiration_date"])
    except (KeyError, TypeError) as error:
        raise ValueError("Некорректная партия продукта.") from error
    return goods


def main() -> None:
    goods = {}
    add(goods, "Молоко", "1.5", "2026-10-27")
    add(goods, "Молоко", "0.5", "2026-10-30")
    add(goods, "Рис", "2")
    for title, batches in goods.items():
        print(title, batches)
    print("Всего молока:", amount(goods, "молоко"))
    print("Просрочено на 2026-10-28:", expired(goods, date(2026, 10, 28)))


if __name__ == "__main__":
    main()
