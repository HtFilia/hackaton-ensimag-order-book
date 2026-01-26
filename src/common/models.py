from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    BLOCK = "block"


@dataclass
class Order:
    id: str
    side: Side
    price: float
    quantity: float
    asset: str = "default"
    order_type: OrderType = OrderType.LIMIT
    min_quantity: Optional[float] = None  # used for block orders

    def __post_init__(self) -> None:
        if isinstance(self.side, str):
            self.side = Side(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)


@dataclass
class BookSide:
    side: Side
    orders: List[Order] = field(default_factory=list)

    def add(self, order: Order) -> None:
        self.orders.append(order)

    def best(self) -> Optional[Order]:
        return self.orders[0] if self.orders else None


@dataclass
class OrderBook:
    bids: BookSide = field(default_factory=lambda: BookSide(side=Side.BUY))
    asks: BookSide = field(default_factory=lambda: BookSide(side=Side.SELL))

    def snapshot(self) -> dict:
        return {
            "bids": [order_to_dict(o) for o in self.bids.orders],
            "asks": [order_to_dict(o) for o in self.asks.orders],
        }


@dataclass
class MultiBook:
    books: Dict[str, OrderBook] = field(default_factory=dict)

    def get_or_create(self, asset: str) -> OrderBook:
        if asset not in self.books:
            self.books[asset] = OrderBook()
        return self.books[asset]

    def snapshot(self) -> dict:
        return {asset: book.snapshot() for asset, book in self.books.items()}


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "side": order.side.value if isinstance(order.side, Side) else order.side,
        "price": order.price,
        "quantity": order.quantity,
        "asset": order.asset,
        "order_type": order.order_type.value
        if isinstance(order.order_type, OrderType)
        else order.order_type,
        "min_quantity": order.min_quantity,
    }
