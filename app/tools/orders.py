import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ORDERS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "orders.json"
)


SAFE_ITEM_FIELDS = {
    "name",
    "quantity",
    "final_sale",
}


SAFE_ORDER_FIELDS = {
    "order_id",
    "membership_tier",
    "placed_at",
    "status",
    "status_updated_at",
    "shipped_at",
    "delivered_at",
    "carrier",
    "tracking_number",
    "estimated_delivery",
    "customer_safe_message",
}


class OrderLookup:
    """
    Safe read-only lookup over the mock order dataset.

    Internal customer information and internal operational data
    are deliberately never returned.
    """

    def __init__(
        self,
        orders_path: str | Path = DEFAULT_ORDERS_PATH,
    ):
        self.orders_path = Path(orders_path)

        with self.orders_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.data = json.load(file)

        self.orders = self.data.get("orders", [])

        self._orders_by_id = {
            order["order_id"]: order
            for order in self.orders
            if "order_id" in order
        }

    @staticmethod
    def normalize_order_id(order_id: str) -> str:
        """
        Normalize harmless user formatting differences.

        Examples:
            ord-1007 -> ORD-1007
            " ORD-1007 " -> ORD-1007
            "ORD 1007" -> ORD1007

        We do not guess substantially different IDs.
        """

        normalized = order_id.strip().upper()

        normalized = re.sub(
            r"[\s\.,;:!?]+",
            "",
            normalized,
        )

        return normalized

    def lookup(
        self,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Look up an order and return only customer-safe fields.
        """

        normalized_id = self.normalize_order_id(
            order_id
        )

        order = self._orders_by_id.get(
            normalized_id
        )

        if order is None:
            return {
                "found": False,
                "order_id": normalized_id,
                "message": (
                    "Order was not found. "
                    "Please check the order ID or contact support."
                ),
            }

        result: dict[str, Any] = {
            "found": True,
        }

        for field in SAFE_ORDER_FIELDS:
            if field in order:
                result[field] = order[field]

        safe_items = []

        for item in order.get("items", []):
            safe_item = {
                key: item[key]
                for key in SAFE_ITEM_FIELDS
                if key in item
            }

            safe_items.append(safe_item)

        if safe_items:
            result["items"] = safe_items

        return result


def lookup_order(
    order_id: str,
    orders_path: str | Path = DEFAULT_ORDERS_PATH,
) -> dict[str, Any]:
    """
    Convenience function used by the agent/tool layer.
    """

    lookup = OrderLookup(
        orders_path=orders_path
    )

    return lookup.lookup(order_id)