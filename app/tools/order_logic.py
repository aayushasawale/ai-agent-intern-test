from typing import Any


def interpret_order_status(
    order: dict[str, Any],
) -> dict[str, Any]:
    if not order.get("found"):
        return {
            "action": "not_found",
            "customer_message": (
                "I couldn't find that order. "
                "Please check the order ID and try again."
            ),
        }

    status = str(
        order.get("status", "")
    ).lower()

    eta = order.get("estimated_delivery")

    if status in {"cancelled", "canceled"}:
        return {
            "action": "cancelled",
            "customer_message": (
                "This order has been cancelled. "
                "The previous delivery estimate is no longer applicable."
            ),
        }

    if status == "returned":
        return {
            "action": "returned",
            "customer_message": (
                "This order has been returned, "
                "so the previous delivery estimate is no longer applicable."
            ),
        }

    if status == "delivered":
        return {
            "action": "delivered",
            "customer_message": (
                "This order has been delivered."
            ),
        }

    if status == "shipped":
        if eta:
            return {
                "action": "shipped",
                "customer_message": (
                    f"Your order has shipped. "
                    f"The current estimated delivery date is {eta}."
                ),
            }

        return {
            "action": "shipped_eta_unavailable",
            "customer_message": (
                "Your order has shipped, but an "
                "estimated delivery date is not currently available."
            ),
        }

    if status == "pending":
        return {
            "action": "pending",
            "customer_message": (
                "We received your order, but it has "
                "not entered processing yet."
            ),
        }

    if status == "processing":
        return {
            "action": "processing",
            "customer_message": (
                "Your order is currently being processed."
            ),
        }

    return {
        "action": "unknown_status",
        "customer_message": (
            "I found the order, but I don't have enough "
            "information to provide a reliable delivery update."
        ),
    }