from dataclasses import dataclass
from typing import Any

from app.tools.orders import OrderLookup
from app.tools.order_logic import interpret_order_status


@dataclass
class AgentResponse:
    answer: str
    sources: list[str]
    handoff: bool = False
    tool_called: str | None = None
    tool_arguments: dict[str, Any] | None = None


class SupportAgent:
    """
    Deterministic application layer for the support agent.

    The LLM will be added later. This layer owns:
    - order tool usage
    - order-status interpretation
    - safe response handling
    """

    def __init__(
        self,
        order_lookup: OrderLookup | None = None,
    ):
        self.order_lookup = (
            order_lookup
            or OrderLookup()
        )

    def handle_order_question(
        self,
        order_id: str | None,
    ) -> AgentResponse:

        if not order_id:
            return AgentResponse(
                answer=(
                    "Sure — I can check that for you. "
                    "Please provide your order ID."
                ),
                sources=[],
                handoff=False,
                tool_called=None,
            )

        result = self.order_lookup.lookup(
            order_id
        )

        if not result.get("found"):
            return AgentResponse(
                answer=(
                    "I couldn't find that order. "
                    "Please check the order ID and try again."
                ),
                sources=[],
                handoff=False,
                tool_called="order_lookup",
                tool_arguments={
                    "order_id": order_id
                },
            )

        interpretation = interpret_order_status(
            result
        )

        answer = interpretation[
            "customer_message"
        ]

        # Add carrier/tracking information only
        # when it is actually present.
        if (
            interpretation["action"]
            == "shipped"
        ):
            carrier = result.get(
                "carrier"
            )

            tracking = result.get(
                "tracking_number"
            )

            if carrier:
                answer += (
                    f" Carrier: {carrier}."
                )

            if tracking:
                answer += (
                    f" Tracking number: {tracking}."
                )

        return AgentResponse(
            answer=answer,
            sources=[],
            handoff=False,
            tool_called="order_lookup",
            tool_arguments={
                "order_id": order_id
            },
        )