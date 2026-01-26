from __future__ import annotations

import importlib
from pathlib import Path
from typing import Callable, Iterable, List, Tuple, Union

import yaml

from src.common.models import MultiBook, Order, OrderBook


def load_team_module(team: str, level: str):
    module_path = f"submissions.{team}.{level}"
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ImportError(f"Missing module for team '{team}' level '{level}'") from exc


def parse_fixture(path: Path) -> Tuple[Union[OrderBook, MultiBook], List[Order], dict]:
    data = yaml.safe_load(path.read_text())
    if "books" in data:
        multibook = MultiBook()
        for asset, book_data in data["books"].items():
            book = multibook.get_or_create(asset)
            for bid in book_data.get("bids", []):
                bid_data = dict(bid)
                bid_data.setdefault("asset", asset)
                book.bids.add(Order(**bid_data))
            for ask in book_data.get("asks", []):
                ask_data = dict(ask)
                ask_data.setdefault("asset", asset)
                book.asks.add(Order(**ask_data))
        initial_state: Union[OrderBook, MultiBook] = multibook
    else:
        book = OrderBook()
        for bid in data.get("initial_book", {}).get("bids", []):
            book.bids.add(Order(**bid))
        for ask in data.get("initial_book", {}).get("asks", []):
            book.asks.add(Order(**ask))
        initial_state = book

    orders = [Order(**raw) for raw in data.get("orders", [])]
    expected = data.get("expected_final", {})
    return initial_state, orders, expected


def validate_level(team: str, level: str, fixture: Path) -> tuple[bool, str]:
    module = load_team_module(team, level)
    process_orders: Callable[[Union[OrderBook, MultiBook], Iterable[Order]], Union[OrderBook, MultiBook]] = getattr(
        module, "process_orders", None
    )
    if process_orders is None:
        return False, "process_orders not found"

    initial_state, orders, expected = parse_fixture(fixture)
    result = process_orders(initial_state, orders)

    if isinstance(expected, dict) and "bids" in expected:
        if not isinstance(result, OrderBook):
            return False, "process_orders must return OrderBook for single-book levels"
    if isinstance(expected, dict) and "bids" not in expected:
        if not isinstance(result, MultiBook):
            return False, "process_orders must return MultiBook for multi-asset levels"

    snapshot = result.snapshot() if hasattr(result, "snapshot") else None
    if snapshot == expected:
        return True, "Validation passed"

    return False, f"Final book mismatch.\nExpected: {expected}\nGot: {snapshot}"
