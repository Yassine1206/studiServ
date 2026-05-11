from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    # ── Page d'accueil ──────────────────────────────────────────────
    path("", views.index, name="index"),

    # ── Authentification ─────────────────────────────────────────────
    path("login/",            views.MainLoginView.as_view(),  name="login"),
    path("login",             views.MainLoginView.as_view(),  name="login_noslash"),
    path("inscription/",      views.inscription,              name="inscription"),
    path("deconnexion/",      views.deconnexion,              name="logout"),

    # Connexions différenciées par rôle
    path("connexion/consommateur/", views.StudentLoginView.as_view(),  name="login_etudiant"),
    path("connexion/prestataire/",  views.ProviderLoginView.as_view(), name="login_prestataire"),

    # ── Dashboards (protégés par rôle) ───────────────────────────────
    path("etudiant/",    views.etudiant_dashboard,   name="etudiant_dashboard"),
    path("etudiant",     views.etudiant_dashboard,   name="etudiant_dashboard_slash"),
    path("prestataire/", views.prestatire_dashboard, name="prestataire_dashboard"),
    path("prestataire",  views.prestatire_dashboard, name="prestataire_dashboard_slash"),
    path("prestatire/",  views.prestatire_dashboard, name="prestatire_dashboard"),
    path("prestatire",   views.prestatire_dashboard, name="prestatire_dashboard_slash"),
]

# ── CRUD générique pour toutes les entités ───────────────────────────
for model_name in views.MODEL_NAMES:
    slug = model_name.lower()
    urlpatterns += [
        path(f"{slug}/",                      views.entity_list,   {"model_slug": slug}, name=f"{slug}_list"),
        path(f"{slug}/ajouter/",              views.entity_create, {"model_slug": slug}, name=f"{slug}_create"),
        path(f"{slug}/<int:pk>/",             views.entity_detail, {"model_slug": slug}, name=f"{slug}_detail"),
        path(f"{slug}/<int:pk>/modifier/",    views.entity_update, {"model_slug": slug}, name=f"{slug}_update"),
        path(f"{slug}/<int:pk>/supprimer/",   views.entity_delete, {"model_slug": slug}, name=f"{slug}_delete"),
    ]
