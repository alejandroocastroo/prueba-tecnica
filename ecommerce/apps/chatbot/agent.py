"""
Claude AI Agent for the e-commerce chatbot.
"""
import json
import logging
from typing import Any
from django.conf import settings

import anthropic

from apps.orders.models import Order
from apps.shipments.models import Shipment
from apps.payments.models import OrderPayment

logger = logging.getLogger(__name__)

# Define tools for the agent
TOOLS = [
    {
        "name": "get_order_status",
        "description": "Get the status of a specific order. Returns order details including status, total, and items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to look up"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "get_shipment_info",
        "description": "Get shipment information for an order. Returns tracking number and shipment status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to get shipment info for"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "get_payment_info",
        "description": "Get payment information for an order. Returns payment details and amounts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to get payment info for"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "list_user_orders",
        "description": "List all orders for the current user. Returns a summary of all orders.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

SYSTEM_PROMPT = """You are a helpful customer service assistant for an e-commerce platform.
You help customers with their orders, shipments, and payments.

You have access to the following tools to help customers:
- get_order_status: Get details about a specific order
- get_shipment_info: Get shipping and tracking information
- get_payment_info: Get payment details for an order
- list_user_orders: List all orders for the customer

Always be polite and helpful. If you can't find information, let the customer know politely.
Respond in the same language the customer uses.
"""


class EcommerceAgent:
    """Agent that uses Claude to answer customer queries about orders."""

    def __init__(self, user):
        self.user = user
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    def get_order_status(self, order_id: int) -> dict[str, Any]:
        """Get order status for the authenticated user."""
        try:
            order = Order.objects.prefetch_related('items__product').get(
                id=order_id,
                user=self.user
            )
            items = [
                {
                    "product": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "subtotal": str(item.subtotal)
                }
                for item in order.items.all()
            ]
            return {
                "found": True,
                "order_id": order.id,
                "status": order.get_status_display(),
                "total": str(order.total),
                "total_paid": str(order.total_paid),
                "is_fully_paid": order.is_fully_paid,
                "items": items,
                "created_at": order.created_at.isoformat()
            }
        except Order.DoesNotExist:
            return {
                "found": False,
                "error": f"Order #{order_id} not found or doesn't belong to you."
            }

    def get_shipment_info(self, order_id: int) -> dict[str, Any]:
        """Get shipment info for an order."""
        try:
            order = Order.objects.get(id=order_id, user=self.user)
            shipments = Shipment.objects.filter(order=order)

            if not shipments.exists():
                return {
                    "found": True,
                    "order_id": order_id,
                    "shipments": [],
                    "message": "No shipments created for this order yet."
                }

            shipment_data = [
                {
                    "shipment_id": s.id,
                    "status": s.get_status_display(),
                    "tracking_number": s.tracking_number or "Not assigned yet",
                    "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
                    "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None
                }
                for s in shipments
            ]

            return {
                "found": True,
                "order_id": order_id,
                "shipments": shipment_data
            }
        except Order.DoesNotExist:
            return {
                "found": False,
                "error": f"Order #{order_id} not found or doesn't belong to you."
            }

    def get_payment_info(self, order_id: int) -> dict[str, Any]:
        """Get payment info for an order."""
        try:
            order = Order.objects.get(id=order_id, user=self.user)
            order_payments = OrderPayment.objects.filter(order=order).select_related('payment')

            if not order_payments.exists():
                return {
                    "found": True,
                    "order_id": order_id,
                    "order_total": str(order.total),
                    "total_paid": "0.00",
                    "remaining": str(order.total),
                    "payments": [],
                    "message": "No payments recorded for this order yet."
                }

            payments_data = [
                {
                    "payment_id": op.payment.id,
                    "amount_applied": str(op.amount_applied),
                    "method": op.payment.get_method_display(),
                    "status": op.payment.get_status_display(),
                    "created_at": op.created_at.isoformat()
                }
                for op in order_payments
            ]

            return {
                "found": True,
                "order_id": order_id,
                "order_total": str(order.total),
                "total_paid": str(order.total_paid),
                "remaining": str(order.total - order.total_paid),
                "is_fully_paid": order.is_fully_paid,
                "payments": payments_data
            }
        except Order.DoesNotExist:
            return {
                "found": False,
                "error": f"Order #{order_id} not found or doesn't belong to you."
            }

    def list_user_orders(self) -> dict[str, Any]:
        """List all orders for the user."""
        orders = Order.objects.filter(user=self.user).order_by('-created_at')[:10]

        if not orders.exists():
            return {
                "orders": [],
                "message": "You don't have any orders yet."
            }

        orders_data = [
            {
                "order_id": order.id,
                "status": order.get_status_display(),
                "total": str(order.total),
                "items_count": order.items.count(),
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]

        return {
            "orders": orders_data,
            "total_orders": Order.objects.filter(user=self.user).count()
        }

    def process_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Process a tool call and return the result."""
        if tool_name == "get_order_status":
            result = self.get_order_status(tool_input["order_id"])
        elif tool_name == "get_shipment_info":
            result = self.get_shipment_info(tool_input["order_id"])
        elif tool_name == "get_payment_info":
            result = self.get_payment_info(tool_input["order_id"])
        elif tool_name == "list_user_orders":
            result = self.list_user_orders()
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result)

    def chat(self, message: str) -> str:
        """Process a chat message and return the response."""
        if not settings.ANTHROPIC_API_KEY:
            return "I'm sorry, the AI service is not configured. Please contact support."

        messages = [{"role": "user", "content": message}]

        try:
            # Initial API call
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            )

            # Handle tool use in a loop
            while response.stop_reason == "tool_use":
                # Find tool use blocks
                tool_uses = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                if not tool_uses:
                    break

                # Add assistant response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Process each tool call
                tool_results = []
                for tool_use in tool_uses:
                    result = self.process_tool_call(tool_use.name, tool_use.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result
                    })

                # Add tool results
                messages.append({"role": "user", "content": tool_results})

                # Get next response
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages
                )

            # Extract text response
            text_blocks = [
                block.text for block in response.content
                if hasattr(block, 'text')
            ]

            return " ".join(text_blocks) if text_blocks else "I couldn't process your request."

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return "I'm having trouble connecting to the AI service. Please try again later."
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return "An error occurred while processing your request. Please try again."
