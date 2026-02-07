"""
Serializers for the chatbot app.
"""
from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for incoming chat messages."""

    message = serializers.CharField(
        max_length=1000,
        help_text="The message to send to the AI assistant"
    )

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses."""

    response = serializers.CharField(help_text="The AI assistant's response")
    user_message = serializers.CharField(help_text="The original user message")
