from __future__ import annotations

from copy import copy, deepcopy
from typing import Dict, Iterable, List, Optional

from src.common.models import Action, MultiBook, Order, OrderBook, OrderType, Side, TimeInForce


def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
    mbook = deepcopy(initial_book)
    last_traded: Dict[str, Optional[float]] = {}
    # File d'ordres LOC/MOC par actif, en attente du prochain événement CLOSE
    auction_queue: Dict[str, List[Order]] = {}

    for incoming in orders:
        asset = incoming.asset
        book = mbook.get_or_create(asset)

        if incoming.action == Action.CLOSE:
            ltp = _run_auction(book, auction_queue.get(asset, []), last_traded.get(asset))
            auction_queue[asset] = []
            if ltp is not None:
                last_traded[asset] = ltp

        elif incoming.action == Action.CANCEL:
            # Annuler depuis le carnet continu OU depuis la file d'enchère
            if not _cancel_from_book(book, incoming.id):
                _cancel_from_queue(auction_queue.get(asset, []), incoming.id)

        elif incoming.action == Action.AMEND:
            queue = auction_queue.setdefault(asset, [])
            if not _amend_in_book(book, incoming):
                _amend_in_queue(queue, incoming)

        elif incoming.order_type in (OrderType.LOC, OrderType.MOC):
            auction_queue.setdefault(asset, []).append(incoming)

        else:
            ltp = _new_order(book, incoming, last_traded.get(asset))
            if ltp is not None:
                last_traded[asset] = ltp

    return mbook


# ── annulation ───────────────────────────────────────────────────────────────

def _cancel_from_book(book: OrderBook, order_id: str) -> bool:
    for side in (book.bids.orders, book.asks.orders):
        for i, o in enumerate(side):
            if o.id == order_id:
                side.pop(i)
                return True
    return False


def _cancel_from_queue(queue: List[Order], order_id: str) -> None:
    for i, o in enumerate(queue):
        if o.id == order_id:
            queue.pop(i)
            return


# ── modification ─────────────────────────────────────────────────────────────

def _amend_in_book(book: OrderBook, req: Order) -> bool:
    orig = _pop_by_id(book, req.id)
    if orig is None:
        return False
    amended = copy(orig)
    if req.price:
        amended.price = req.price
    if req.quantity:
        amended.quantity = req.quantity
    if amended.visible_quantity is not None:
        amended.visible_quantity = min(amended.visible_quantity, amended.quantity)
    amended.action = Action.NEW
    _new_order(book, amended, last_traded_price=None)
    return True


def _amend_in_queue(queue: List[Order], req: Order) -> None:
    for i, orig in enumerate(queue):
        if orig.id == req.id:
            queue.pop(i)
            amended = copy(orig)
            if req.price:
                amended.price = req.price
            if req.quantity:
                amended.quantity = req.quantity
            amended.action = Action.NEW
            queue.append(amended)  # réinséré en fin de file (perte de priorité)
            return


def _pop_by_id(book: OrderBook, order_id: str) -> Order | None:
    for side in (book.bids.orders, book.asks.orders):
        for i, o in enumerate(side):
            if o.id == order_id:
                return side.pop(i)
    return None


# ── nouvel ordre (marché continu) ─────────────────────────────────────────────

def _new_order(book: OrderBook, order: Order, last_traded_price: Optional[float]) -> Optional[float]:
    tif = order.time_in_force

    if tif == TimeInForce.FOK:
        available = _available_volume(book, order)
        if available < order.quantity:
            return last_traded_price
        return _match(book, order, last_traded_price)

    elif tif == TimeInForce.IOC:
        return _match(book, order, last_traded_price)

    else:  # GTC
        ltp = _match(book, order, last_traded_price)
        if order.quantity > 0 and order.order_type == OrderType.LIMIT:
            _insert(book, order)
        return ltp


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


def _match(book: OrderBook, order: Order, last_traded_price: Optional[float]) -> Optional[float]:
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
        last_traded_price = best.price
        if best.quantity > 0 and best.visible_quantity is not None:
            best.visible_quantity = min(best.visible_quantity, best.quantity)
        if best.quantity == 0:
            counterparts.pop(idx)
            continue
        idx += 1
    return last_traded_price


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


# ── enchère de clôture ────────────────────────────────────────────────────────

def _run_auction(
    book: OrderBook,
    queue: List[Order],
    last_traded_price: Optional[float],
) -> Optional[float]:
    """Décroisement max-volume. Tous les ordres LOC/MOC non exécutés sont annulés ensuite."""
    if not queue:
        return None

    bids = [o for o in queue if o.side == Side.BUY]
    asks = [o for o in queue if o.side == Side.SELL]

    if not bids or not asks:
        # File unilatérale : rien à matcher, tout annuler
        queue.clear()
        return None

    clearing_price = _find_clearing_price(bids, asks, last_traded_price)
    if clearing_price is None:
        queue.clear()
        return None

    ltp = _execute_auction(bids, asks, clearing_price)
    queue.clear()
    return ltp


def _find_clearing_price(
    bids: List[Order],
    asks: List[Order],
    last_traded_price: Optional[float],
) -> Optional[float]:
    # Prix candidats : tous les prix des ordres LOC ; les ordres MOC participent à n'importe quel prix
    candidates = sorted(set(
        o.price
        for o in (*bids, *asks)
        if o.order_type == OrderType.LOC and o.price and o.price > 0
    ))

    if not candidates:
        # Uniquement des ordres MOC : utiliser le dernier prix échangé comme référence
        return last_traded_price  # peut être None → pas de prix d'équilibre

    best_price: Optional[float] = None
    best_volume = 0.0

    for p in candidates:
        buy_vol = sum(
            o.quantity for o in bids
            if o.order_type == OrderType.MOC or o.price >= p
        )
        sell_vol = sum(
            o.quantity for o in asks
            if o.order_type == OrderType.MOC or o.price <= p
        )
        vol = min(buy_vol, sell_vol)

        if vol > best_volume:
            best_volume = vol
            best_price = p
        elif vol == best_volume and vol > 0 and best_price is not None:
            # Départage : préférer le prix le plus proche du dernier échangé
            if last_traded_price is not None:
                if abs(p - last_traded_price) < abs(best_price - last_traded_price):
                    best_price = p

    return best_price if best_volume > 0 else None


def _execute_auction(
    bids: List[Order],
    asks: List[Order],
    clearing_price: float,
) -> float:
    eligible_bids = [
        o for o in bids
        if o.order_type == OrderType.MOC or o.price >= clearing_price
    ]
    eligible_asks = [
        o for o in asks
        if o.order_type == OrderType.MOC or o.price <= clearing_price
    ]

    # Priorité : MOC en premier, puis LOC par meilleur prix, puis FIFO
    eligible_bids.sort(key=lambda o: (0 if o.order_type == OrderType.MOC else 1, -o.price))
    eligible_asks.sort(key=lambda o: (0 if o.order_type == OrderType.MOC else 1, o.price))

    bi, ai = 0, 0
    while bi < len(eligible_bids) and ai < len(eligible_asks):
        bid = eligible_bids[bi]
        ask = eligible_asks[ai]
        traded = min(bid.quantity, ask.quantity)
        bid.quantity -= traded
        ask.quantity -= traded
        if bid.quantity == 0:
            bi += 1
        if ask.quantity == 0:
            ai += 1

    return clearing_price
