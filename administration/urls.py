# apps/administration/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_stats, name='admin-dashboard'),

    # Utilisateurs
    path('users/', views.UserManagementView.as_view(), name='admin-users'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='admin-user-toggle'),
    path('users/<int:user_id>/', views.delete_user, name='admin-user-delete'),

    # Cartes étudiantes
    path('cards/', views.pending_cards, name='admin-cards'),
    path('cards/<int:card_id>/review/', views.review_card, name='admin-card-review'),

    # Signalements
    path('flagged/', views.flagged_content_list, name='admin-flagged'),
    path('flagged/<int:flag_id>/moderate/', views.moderate_flagged, name='admin-flagged-moderate'),

    # Litiges
    path('disputes/', views.dispute_list, name='admin-disputes'),
    path('disputes/<int:dispute_id>/resolve/', views.resolve_dispute, name='admin-dispute-resolve'),
]
