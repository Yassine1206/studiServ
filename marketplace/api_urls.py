"""
URLs de l'API REST — à inclure dans StudiServ/urls.py sous le préfixe /api/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views
from .api_provider_public import api_provider_public_profile

urlpatterns = [
    # ── Authentification ──────────────────────────────────
    path("auth/signup/",         api_views.api_signup,              name="api_signup"),
    path("auth/signin/",         api_views.api_signin,              name="api_signin"),
    path("auth/logout/",         api_views.api_logout,              name="api_logout"),
    path("auth/reset-password/", api_views.api_reset_password,      name="api_reset_password"),
    path("auth/token/refresh/",  TokenRefreshView.as_view(),        name="api_token_refresh"),
    path("auth/profile/",        api_views.api_profile,             name="api_profile"),
    path("auth/avatar/",         api_views.api_upload_avatar,       name="api_avatar"),

    # ── Services ───────────────────────────────────────
    path("services/",            api_views.api_services_list,       name="api_services"),
    path("services/<int:pk>/",   api_views.api_service_detail,      name="api_service_detail"),
    path("services/<int:service_id>/order/", api_views.api_create_order, name="api_create_order"),

    # ── Consommateur ──────────────────────────────────
    path("consumer/orders/",         api_views.api_consumer_orders,         name="api_consumer_orders"),
    path("recommendations/",         api_views.api_consumer_recommendations, name="api_recommendations"),

    # ── Prestataire ────────────────────────────────────
    path("provider/services/",   api_views.api_provider_services,   name="api_provider_services"),
    path("provider/orders/",     api_views.api_provider_orders,     name="api_provider_orders"),
    path("provider/orders/<int:demande_id>/status/", api_views.api_provider_update_order, name="api_provider_update_order"),
    path("provider/statistics/", api_views.api_provider_statistics, name="api_provider_stats"),
    path("provider/reviews/",    api_views.api_provider_reviews,    name="api_provider_reviews"),
    path("providers/<int:provider_id>/", api_provider_public_profile, name="api_provider_public_profile"),

    # ── Administration ─────────────────────────────────
    path("admin/users/",                       api_views.api_admin_users,         name="api_admin_users"),
    path("admin/users/<int:user_id>/suspend/", api_views.api_admin_suspend_user,  name="api_admin_suspend"),
    path("admin/users/<int:user_id>/activate/",api_views.api_admin_activate_user, name="api_admin_activate"),
    path("admin/verify-card/<int:user_id>/",   api_views.api_admin_verify_card,   name="api_admin_verify"),
    path("admin/statistics/",                  api_views.api_admin_statistics,    name="api_admin_stats"),
]
