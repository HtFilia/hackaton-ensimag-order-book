from __future__ import annotations

from copy import copy, deepcopy
from typing import Iterable

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side, TimeInForce


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
    tif = order.time_in_force

    if tif == TimeInForce.FOK:
        # Vérifier l'exécutabilité totale avant de toucher au carnet
        available = _available_volume(book, order)
        if available < order.quantity:
            return  # ordre rejeté entièrement
        _match(book, order)  # sera entièrement exécuté

    elif tif == TimeInForce.IOC:
        _match(book, order)
        # la quantité restante est annulée (ne repose jamais)

    else:  # GTC
        _match(book, order)
        if order.quantity > 0 and order.order_type == OrderType.LIMIT:
            _insert(book, order)


def _available_volume(book: OrderBook, order: Order) -> float:
    total = 0.0
    if order.side == Side.BUY:
        for o in book.asks.orders:
            if order.order_type == OrderType.LIMIT and o.price > order.price:
                break
            total += o.quantity
            if total >= order.quantity:
                break
    else:
        for o in book.bids.orders:
            if order.order_type == OrderType.LIMIT and o.price < order.price:
                break
            total += o.quantity
            if total >= order.quantity:
                break
    return total


def _match(book: OrderBook, order: Order) -> None:
    if order.side == Side.BUY:
        counterparts = book.asks.orders
        def price_ok(best: Order) -> bool:
            return order.order_type == OrderType.MARKET or best.price <= order.price
    else:
        counterparts = book.bids.orders
        def price_ok(best: Order) -> bool:
            return order.order_type == OrderType.MARKET or best.price >= order.price

    idx = 0
    while order.quantity > 0 and idx < len(counterparts):
        best = counterparts[idx]
        if not price_ok(best):
            break
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        if best.quantity == 0:
            counterparts.pop(idx)
            continue
        idx += 1


def _insert(book: OrderBook, order: Order) -> None:
    if order.side == Side.BUY:
        bids = book.bids.orders
        idx = 0
        while idx < len(bids) and bids[idx].price >= order.price:
            idx += 1
        bids.insert(idx, order)
    else:
        asks = book.asks.orders
        idx = 0
        while idx < len(asks) and asks[idx].price <= order.price:
            idx += 1
        asks.insert(idx, order)
