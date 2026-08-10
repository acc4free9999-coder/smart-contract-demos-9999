from __future__ import annotations

from collections import defaultdict
from typing import Any


class SettlementService:
    def __init__(self, transactions: list[dict[str, Any]] | None = None):
        self.transactions = transactions or []

    def compute(self) -> list[dict[str, Any]]:
        summary: dict[str, dict[str, int]] = defaultdict(lambda: {"points_issued": 0, "points_redeemed": 0})
        for tx in self.transactions:
            bucket = summary[tx["partner"]]
            if tx["type"] == "EARN":
                bucket["points_issued"] += int(tx["amount"])
            else:
                bucket["points_redeemed"] += int(tx["amount"])
        return [
            {
                "partner": partner,
                "points_issued": payload["points_issued"],
                "points_redeemed": payload["points_redeemed"],
                "net_position": payload["points_issued"] - payload["points_redeemed"],
            }
            for partner, payload in sorted(summary.items())
        ]
