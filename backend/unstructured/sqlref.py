"""Read-only reference values from the SQL dump, used to VALIDATE A's image extraction.

B owns loading and querying the database; this only parses data/sql/merlion_ops.sql in memory so A can check
each POD card against the record (order exists, delivered time, driver, postal code, block, COD). Keys are
(system_version, order_id) because order_id restarted at the Feb 2026 migration (T-A01).
"""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

INSERT_RE = re.compile(r"INSERT INTO `(\w+)` \((.*?)\) VALUES")
BLOCK_RE = re.compile(r"\bBlk\s*(\d{1,4}[A-Z]?)\b", re.I)
Key = Tuple[str, int]


def _rows(sql_text: str) -> Dict[str, List[Dict[str, str]]]:
    tables: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    current: Optional[str] = None
    columns: List[str] = []
    for line in sql_text.splitlines():
        m = INSERT_RE.match(line)
        if m:
            current, columns = m.group(1), [c.strip(" `") for c in m.group(2).split(",")]
            continue
        if current and line.startswith("("):
            body = re.sub(r"\)[,;]?\s*$", "", line.rstrip()[1:])
            values = next(csv.reader(io.StringIO(body), quotechar="'", escapechar="\\", skipinitialspace=True))
            tables[current].append(dict(zip(columns, values)))
            if line.rstrip().endswith(";"):
                current = None
        elif current and not line.strip():
            current = None
    return tables


class Reference:
    def __init__(self, orders: Dict[Key, Dict[str, Any]], deliveries: Dict[Key, List[Dict[str, Any]]]):
        self.orders, self.deliveries = orders, deliveries

    @classmethod
    def from_sql(cls, sql_path: Path) -> "Reference":
        tables = _rows(sql_path.read_text(encoding="utf-8"))
        drivers = {d["driver_id"]: d["driver_code"] for d in tables.get("drivers", [])}
        orders: Dict[Key, Dict[str, Any]] = {}
        for o in tables.get("orders", []):
            block = BLOCK_RE.search(o.get("delivery_address", ""))
            orders[(o["system_version"].lower(), int(o["order_id"]))] = {
                "order_date": o.get("order_date"), "postal_code": o.get("postal_code"),
                "block": block.group(1) if block else None,
                "cod_amount": float(o["cod_amount"]) if o.get("cod_amount") not in (None, "", "NULL") else None,
                "parcel_weight_kg": o.get("parcel_weight_kg"), "status": o.get("status")}
        deliveries: Dict[Key, List[Dict[str, Any]]] = defaultdict(list)
        for d in tables.get("deliveries", []):
            deliveries[(d["system_version"].lower(), int(d["order_id"]))].append({
                "delivered_time": d.get("delivered_time"), "driver_code": drivers.get(d.get("driver_id")),
                "outcome": d.get("outcome"), "remarks": d.get("remarks")})
        return cls(orders, dict(deliveries))
