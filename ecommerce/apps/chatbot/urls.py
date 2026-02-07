"""
URL patterns for the chatbot app.
"""
from django.urls import path

from .views import ChatView

app_name = 'chatbot'

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
]
