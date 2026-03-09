from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from src.common.models import MultiBook, Order, OrderBook, OrderType, Side


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    mbook = deepcopy(initial_book)
    for incoming in orders:
        book = mbook.get_or_create(incoming.asset)
        if incoming.side == Side.BUY:
            _handle_buy(book, incoming)
        else:
            _handle_sell(book, incoming)
    return mbook


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
    # Les ordres MARKET ne reposent jamais ; les ordres LIMIT reposent si non exécutés
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
