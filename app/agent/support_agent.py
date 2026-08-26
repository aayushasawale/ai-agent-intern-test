import re
from dataclasses import dataclass
from typing import Any

from app.tools.orders import OrderLookup


from dataclasses import dataclass
from typing import Any


class SupportResponse(dict):
    """Dictionary response with agent metadata exposed as attributes."""

    def __init__(
        self,
        data=None,
        tool_called=None,
        tool_arguments=None,
        answer=None,
    ):
        data = data or {}

        super().__init__(data)

        self.tool_called = tool_called
        self.tool_arguments = tool_arguments

        if answer is not None:
            self.answer = answer
        else:
            self.answer = self._build_answer(data)

    @staticmethod
    def _build_answer(data):
        # Unknown order
        if not data.get("found", False):
            return (
                f"I couldn't find order {data.get('order_id', '')}. "
                "Please check the order ID or contact support."
            )

        # Valid order
        order_id = data.get("order_id", "your order")
        status = str(data.get("status", "")).lower()
        carrier = str(data.get("carrier", "")).strip()

        answer = f"Order {order_id} is currently {status}."

        if carrier:
            answer += f" Carrier: {carrier}."

        estimated_delivery = data.get("estimated_delivery")

        if estimated_delivery:
            answer += f" Estimated delivery: {estimated_delivery}."

        return answer


ORDER_ID_PATTERN = re.compile(
    r"\bORD-\d{4}\b",
    re.IGNORECASE,
)


POLICY_KEYWORDS = {
    "return",
    "returns",
    "refund",
    "refunds",
    "warranty",
    "damaged",
    "damage",
    "wrong item",
    "wrong items",
    "shipping",
    "ship",
    "cancellation",
    "cancel",
    "gift card",
    "price adjustment",
    "membership",
    "product care",
}


class SupportAgent:
    """
    Main customer-support router.

    Routes:
        Order questions -> OrderLookup
        Policy questions -> PolicyAgent
        Missing order ID -> clarification
    """

    def __init__(
        self,
        retriever=None,
        orders_path=None,
    ):
        self.retriever = retriever
        self.last_order_id = None
        # Order lookup does not require a retriever.
        if orders_path is None:
            self.order_lookup = OrderLookup()
        else:
            self.order_lookup = OrderLookup(
                orders_path=orders_path
            )

        # Create PolicyAgent only when a retriever
        # has actually been supplied.
        self.policy_agent = None

        if retriever is not None:
            from app.agent.policy_agent import PolicyAgent

            self.policy_agent = PolicyAgent(retriever)

    def _extract_order_id(
        self,
        message: str,
    ) -> str | None:

        match = ORDER_ID_PATTERN.search(message)

        if match is None:
            return None

        return match.group(0).upper()

    def _is_policy_question(
        self,
        message: str,
    ) -> bool:

        message_lower = message.lower()

        return any(
            keyword in message_lower
            for keyword in POLICY_KEYWORDS
        )


    def handle_order_question(self, order_id: str | None) -> SupportResponse:
        """
        Handle an order-specific question.

        Args:
            order_id: Order ID supplied by the customer.
                      Can be None when no order ID was provided.

        Returns:
            A customer-safe order lookup result.
        """

        # No order ID supplied
        if order_id is None or not str(order_id).strip():
            return SupportResponse(
                data={
                    "found": False,
                    "needs_order_id": True,
                    "message": "Please provide your order ID.",
                },
                tool_called=None,
                tool_arguments=None,
                answer="Please provide your order ID.",
            )

        # Normalize the order ID
        normalized_order_id = str(order_id).strip().upper()

        # Look up the order
        result = self.order_lookup.lookup(normalized_order_id)

        # Order not found
        if not result.get("found", False):
            return SupportResponse(
                data=result,
                tool_called="order_lookup",
                tool_arguments={
                    "order_id": normalized_order_id,
                },
            )

        # Get status
        status = str(result.get("status", "")).lower()

        # Cancelled/returned orders must not expose stale ETA
        if status in {"cancelled", "canceled", "returned"}:
            result["estimated_delivery"] = None

        # Successful order lookup
        return SupportResponse(
            data=result,
            tool_called="order_lookup",
            tool_arguments={
                "order_id": normalized_order_id,
            },
        )

    def answer(
        self,
        message: str,
    ) -> dict[str, Any]:

        """
        Answer a customer question.
        """

        # --------------------------------------------------
        # 1. Check whether this is an order-specific question
        # --------------------------------------------------

        order_id = self._extract_order_id(message)

        if order_id is not None:
            # Remember the order for follow-up questions.
            self.last_order_id = order_id

            result = self.handle_order_question(order_id)

            return {
                "type": "order",
                "order_id": order_id,
                "answer": result,
            }

        # ------------------------------------------------------------
        # Follow-up question about the previously discussed order
        # ------------------------------------------------------------

        follow_up_words = {
            "arrive",
            "arrival",
            "delivery",
            "deliver",
            "when will it",
            "when should it",
            "tracking",
            "shipped",
            "where is it",
        }

        message_lower = message.lower()

        if (
            self.last_order_id is not None
            and any(word in message_lower for word in follow_up_words)
        ):
            result = self.handle_order_question(self.last_order_id)

            return {
                "type": "order",
                "order_id": self.last_order_id,
                "answer": result,
            }
       

        # --------------------------------------------------
        # 2. Check whether this is a policy question
        # --------------------------------------------------

        if self._is_policy_question(message):

            if self.policy_agent is None:
                return {
                    "type": "clarification",
                    "answer": (
                        "I need access to the policy knowledge "
                        "base to answer that question."
                    ),
                }

            response = self.policy_agent.answer(message)

            return {
                "type": "policy",
                "answer": response,
            }

        # --------------------------------------------------
        # 3. Customer mentioned an order-type question
        #    but did not provide an order ID.
        # --------------------------------------------------

        order_words = {
            "order",
            "package",
            "shipment",
            "delivery",
            "delivered",
            "shipped",
            "tracking",
        }

        message_lower = message.lower()

        if any(
            word in message_lower
            for word in order_words
        ):
            return {
                "type": "clarification",
                "answer": (
                    "Please provide your order ID, "
                    "for example ORD-1007, "
                    "so I can look up your order."
                ),
            }

        # --------------------------------------------------
        # 4. General clarification
        # --------------------------------------------------

        return {
            "type": "clarification",
            "answer": (
                "Please provide more details so I can "
                "help with your request."
            ),
        }