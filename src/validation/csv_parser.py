"""Parse Palier CSV files into a list of Orders for the validation runner.

CSV formats:
  Palier 1–4: seq, symbol, side, type, price, qty, order_id, action, ref_id
  Palier 5–6: seq, symbol, side, type, price, qty, peak_qty, order_id, action, ref_id

Type-to-internal-model mapping
  LIMIT   -> order_type=LIMIT
  MARKET  -> order_type=MARKET
  IOC     -> order_type=LIMIT, time_in_force=IOC
  FOK     -> order_type=LIMIT, time_in_force=FOK
  ICEBERG -> order_type=LIMIT, visible_quantity=peak_qty
  LOC     -> order_type=LOC
  MOC     -> order_type=MOC

Action mapping
  NEW    -> action=NEW         (uses order_id as id)
  CANCEL -> action=CANCEL      (uses ref_id as id; price/qty dummy)
  AMEND  -> action=AMEND       (uses ref_id as id; new price/qty from row)
  CLOSE  -> action=CLOSE       (per-asset closing auction trigger)
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from src.common.models import Action, Order, OrderType, Side, TimeInForce


def _float_or_none(value: str) -> float | None:
    s = value.strip() if value else ""
    return float(s) if s else None


def _float_or_zero(value: str) -> float:
    s = value.strip() if value else ""
    return float(s) if s else 0.0


def parse_csv_orders(csv_path: Path) -> List[Order]:
    """Parse a Palier CSV file and return a list of Orders."""
    orders: List[Order] = []

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        has_peak_qty = "peak_qty" in (reader.fieldnames or [])

        for row in reader:
            action_str = (row.get("action") or "NEW").strip().upper()
            symbol = row["symbol"].strip()
            seq = row["seq"].strip()

            if action_str == "CANCEL":
                orders.append(Order(
                    id=row["ref_id"].strip(),
                    side=Side.BUY,   # dummy – not used by cancel logic
                    price=0.0,
                    quantity=0.0,
                    asset=symbol,
                    action=Action.CANCEL,
                ))

            elif action_str == "AMEND":
                orders.append(Order(
                    id=row["ref_id"].strip(),
                    side=Side.BUY,   # dummy – preserved from original order
                    price=_float_or_zero(row.get("price", "")),
                    quantity=_float_or_zero(row.get("qty", "")),
                    asset=symbol,
                    action=Action.AMEND,
                ))

            elif action_str == "CLOSE":
                orders.append(Order(
                    id=seq,          # unique id for the close event
                    side=Side.BUY,   # dummy
                    price=0.0,
                    quantity=0.0,
                    asset=symbol,
                    action=Action.CLOSE,
                ))

            else:  # NEW
                type_str = (row.get("type") or "LIMIT").strip().upper()
                side_str = (row.get("side") or "BUY").strip().upper()
                price = _float_or_zero(row.get("price", ""))
                qty = _float_or_zero(row.get("qty", ""))
                order_id = row.get("order_id", seq).strip() or seq

                peak_qty = None
                if has_peak_qty:
                    peak_qty = _float_or_none(row.get("peak_qty", ""))

                # Map CSV type to internal model
                if type_str == "IOC":
                    order_type = OrderType.LIMIT
                    tif = TimeInForce.IOC
                    visible_quantity = None
                elif type_str == "FOK":
                    order_type = OrderType.LIMIT
                    tif = TimeInForce.FOK
                    visible_quantity = None
                elif type_str == "ICEBERG":
                    order_type = OrderType.LIMIT
                    tif = TimeInForce.GTC
                    visible_quantity = peak_qty  # peak_qty is the visible tranche
                elif type_str == "LOC":
                    order_type = OrderType.LOC
                    tif = TimeInForce.GTC
                    visible_quantity = None
                elif type_str == "MOC":
                    order_type = OrderType.MOC
                    tif = TimeInForce.GTC
                    visible_quantity = None
                elif type_str == "MARKET":
                    order_type = OrderType.MARKET
                    tif = TimeInForce.GTC
                    visible_quantity = None
                else:  # LIMIT (default)
                    order_type = OrderType.LIMIT
                    tif = TimeInForce.GTC
                    visible_quantity = None

                orders.append(Order(
                    id=order_id,
                    side=Side(side_str.lower()),
                    price=price,
                    quantity=qty,
                    asset=symbol,
                    order_type=order_type,
                    time_in_force=tif,
                    visible_quantity=visible_quantity,
                    action=Action.NEW,
                ))

    return orders
