from __future__ import annotations

from typing import Iterable

from src.common.models import MultiBook, Order, OrderType, Side


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    book = initial_book

    for order in orders:
        if order.order_type != OrderType.LIMIT:
            continue  # Level 1 only handles LIMIT orders

        asset = order.asset
        bids = book.get_or_create(asset).bids.orders  # buy orders, sorted descending by price
        asks = book.get_or_create(asset).asks.orders    # sell orders, sorted ascending by price

        remaining_qty = order.quantity

        if order.side == Side.BUY:
            # Match against asks (lowest price first)
            while remaining_qty > 0 and asks and asks[0].price <= order.price:
                best_ask = asks[0]
                traded_qty = min(remaining_qty, best_ask.quantity)
                remaining_qty -= traded_qty
                best_ask.quantity -= traded_qty
                if best_ask.quantity == 0:
                    asks.pop(0)

        elif order.side == Side.SELL:
            # Match against bids (highest price first)
            while remaining_qty > 0 and bids and bids[0].price >= order.price:
                best_bid = bids[0]
                traded_qty = min(remaining_qty, best_bid.quantity)
                remaining_qty -= traded_qty
                best_bid.quantity -= traded_qty
                if best_bid.quantity == 0:
                    bids.pop(0)

        # Place remaining quantity in the book
        if remaining_qty > 0:
            order.quantity = remaining_qty
            if order.side == Side.BUY:
                bids.append(order)
                bids.sort(key=lambda o: (-o.price, o.time_in_force))
            else:
                asks.append(order)
                asks.sort(key=lambda o: (o.price, o.time_in_force))

    return book
    raise NotImplementedError("Implémenter le Palier 1 : Ordres Limite de Base")
