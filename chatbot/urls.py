# apps/chatbot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Chat
    path('chat/', views.ChatView.as_view(), name='chatbot-chat'),
    path('history/<str:session_key>/', views.chat_history, name='chatbot-history'),

    # FAQ management (admin)
    path('faq/', views.FAQDocumentListCreateView.as_view(), name='faq-list-create'),
    path('faq/<int:pk>/', views.FAQDocumentDetailView.as_view(), name='faq-detail'),
    path('reindex/', views.reindex_faq, name='chatbot-reindex'),
    path('stats/', views.chatbot_stats, name='chatbot-stats'),
]
