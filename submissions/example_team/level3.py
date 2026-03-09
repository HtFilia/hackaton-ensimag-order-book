from __future__ import annotations

from copy import copy, deepcopy
from typing import Iterable, List

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    mbook = deepcopy(initial_book)
    for incoming in orders:
        book = mbook.get_or_create(incoming.asset)
        if incoming.action == Action.CANCEL:
            _cancel(book, incoming.id)
        elif incoming.action == Action.AMEND:
            _amend(book, incoming)
        else:
            _new_order(book, incoming)
    return mbook


# ── annulation ───────────────────────────────────────────────────────────────

def _cancel(book: OrderBook, order_id: str) -> None:
    for side in (book.bids.orders, book.asks.orders):
        for i, o in enumerate(side):
            if o.id == order_id:
                side.pop(i)
                return


# ── modification ─────────────────────────────────────────────────────────────

def _amend(book: OrderBook, req: Order) -> None:
    orig = _pop_by_id(book, req.id)
    if orig is None:
        return
    amended = copy(orig)
    if req.price:
        amended.price = req.price
    if req.quantity:
        amended.quantity = req.quantity
    amended.action = Action.NEW
    _new_order(book, amended)


def _pop_by_id(book: OrderBook, order_id: str) -> Order | None:
    for side in (book.bids.orders, book.asks.orders):
        for i, o in enumerate(side):
            if o.id == order_id:
                return side.pop(i)
    return None


# ── nouvel ordre ──────────────────────────────────────────────────────────────

def _new_order(book: OrderBook, order: Order) -> None:
    if order.side == Side.BUY:
        _handle_buy(book, order)
    else:
        _handle_sell(book, order)


def _handle_buy(book: OrderBook, order: Order) -> None:
    asks = book.asks.orders
    idx = 0
    while order.quantity > 0 and idx < len(asks):
        best = asks[idx]
        if order.order_type == OrderType.LIMIT and best.price > order.price:
            break
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        if best.quantity == 0:
            asks.pop(idx)
            continue
        idx += 1
    if order.quantity > 0 and order.order_type == OrderType.LIMIT:
        _insert_bid(book, order)


def _handle_sell(book: OrderBook, order: Order) -> None:
    bids = book.bids.orders
    idx = 0
    while order.quantity > 0 and idx < len(bids):
        best = bids[idx]
        if order.order_type == OrderType.LIMIT and best.price < order.price:
            break
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        if best.quantity == 0:
            bids.pop(idx)
            continue
        idx += 1
    if order.quantity > 0 and order.order_type == OrderType.LIMIT:
        _insert_ask(book, order)


def _insert_bid(book: OrderBook, order: Order) -> None:
    bids = book.bids.orders
    idx = 0
    while idx < len(bids) and bids[idx].price >= order.price:
        idx += 1
    bids.insert(idx, order)


def _insert_ask(book: OrderBook, order: Order) -> None:
    asks = book.asks.orders
    idx = 0
    while idx < len(asks) and asks[idx].price <= order.price:
        idx += 1
    asks.insert(idx, order)
