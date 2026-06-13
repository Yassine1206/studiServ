# apps/messaging/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/create/', views.ConversationCreateView.as_view(), name='conversation-create'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:pk>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('conversations/<int:pk>/upload/', views.upload_file_message, name='upload-file'),
    path('notifications/', views.notifications_count, name='notifications-count'),
]
