"""
Views for the chatbot app.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from .agent import EcommerceAgent
from .serializers import ChatMessageSerializer, ChatResponseSerializer


class ChatView(APIView):
    """Chat endpoint for the AI assistant."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChatMessageSerializer,
        responses={200: ChatResponseSerializer},
        description="Send a message to the AI assistant",
        examples=[
            OpenApiExample(
                name="Order status query",
                value={"message": "What is the status of my order #1?"},
                request_only=True
            ),
            OpenApiExample(
                name="List orders",
                value={"message": "Show me my recent orders"},
                request_only=True
            )
        ]
    )
    def post(self, request):
        """Process a chat message and return the AI response."""
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']

        # Create agent for the authenticated user
        agent = EcommerceAgent(request.user)
        response_text = agent.chat(message)

        response_serializer = ChatResponseSerializer({
            'response': response_text,
            'user_message': message
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)
