from __future__ import annotations

from typing import Iterable

from copy import deepcopy

from src.common.models import Order, OrderBook, Side


def process_orders(initial_book: OrderBook, orders: Iterable[Order]) -> OrderBook:
    # Work on a deep copy to avoid mutating fixtures across runs.
    book = deepcopy(initial_book)
    for incoming in orders:
        if incoming.side == Side.BUY:
            _handle_buy(book, incoming)
        elif incoming.side == Side.SELL:
            _handle_sell(book, incoming)
        else:
            raise ValueError(f"Unknown side: {incoming.side}")
    return book


def _handle_buy(book: OrderBook, order: Order) -> None:
    asks = book.asks.orders
    # Match against lowest ask prices first.
    idx = 0
    while order.quantity > 0 and idx < len(asks):
        best = asks[idx]
        if best.price > order.price:
            break
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        if best.quantity == 0:
            asks.pop(idx)
            continue
        idx += 1

    if order.quantity > 0:
        _insert_bid(book, order)


def _handle_sell(book: OrderBook, order: Order) -> None:
    bids = book.bids.orders
    # Match against highest bid prices first.
    idx = 0
    while order.quantity > 0 and idx < len(bids):
        best = bids[idx]
        if best.price < order.price:
            break
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        if best.quantity == 0:
            bids.pop(idx)
            continue
        idx += 1

    if order.quantity > 0:
        _insert_ask(book, order)


def _insert_bid(book: OrderBook, order: Order) -> None:
    bids = book.bids.orders
    # Descending price, FIFO within price level.
    idx = 0
    while idx < len(bids) and bids[idx].price >= order.price:
        idx += 1
    bids.insert(idx, order)


def _insert_ask(book: OrderBook, order: Order) -> None:
    asks = book.asks.orders
    # Ascending price, FIFO within price level.
    idx = 0
    while idx < len(asks) and asks[idx].price <= order.price:
        idx += 1
    asks.insert(idx, order)
