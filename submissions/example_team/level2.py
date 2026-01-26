from __future__ import annotations

from typing import Iterable
from copy import deepcopy

from src.common.models import Order, OrderBook, Side, OrderType


def process_orders(initial_book: OrderBook, orders: Iterable[Order]) -> OrderBook:
    book = deepcopy(initial_book)
    for incoming in orders:
        if incoming.side == Side.BUY:
            _handle_buy(book, incoming)
        elif incoming.side == Side.SELL:
            _handle_sell(book, incoming)
    return book


def _handle_buy(book: OrderBook, order: Order) -> None:
    asks = book.asks.orders
    idx = 0
    # For market orders, we just match what we can.
    # For limit orders, we check price crossing.
    
    while order.quantity > 0 and idx < len(asks):
        best = asks[idx]
        
        # If Limit, check price constraint
        if order.order_type == OrderType.LIMIT and best.price > order.price:
            break
            
        # Match
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        
        if best.quantity == 0:
            asks.pop(idx)
            continue
        idx += 1

    # If Limit order and not fully filled, rest in book.
    # Market orders do not rest (Fill and Kill).
    if order.quantity > 0 and order.order_type == OrderType.LIMIT:
        _insert_bid(book, order)


def _handle_sell(book: OrderBook, order: Order) -> None:
    bids = book.bids.orders
    idx = 0
    
    while order.quantity > 0 and idx < len(bids):
        best = bids[idx]
        
        # If Limit, check price constraint
        if order.order_type == OrderType.LIMIT and best.price < order.price:
            break
            
        # Match
        traded = min(order.quantity, best.quantity)
        order.quantity -= traded
        best.quantity -= traded
        
        if best.quantity == 0:
            bids.pop(idx)
            continue
        idx += 1

    # If Limit order and not fully filled, rest in book.
    # Market orders do not rest.
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
