# addons/urls.py
# Monté sous /api/ depuis StudiServ/urls.py.
#
# Contient :
#   • paiement, livrables, suivi de commande
#   • CRUD service (édition/suppression)         <- M2 complété
#   • section recommandée de la page d'accueil   <- homepage complétée
#   • litiges (ouverture côté utilisateur)       <- litiges complétés
#   • RE-ROUTAGE des endpoints d'avis/recommandations sous /api/
#     (corrige le bug "impossible d'enregistrer une note")

from django.urls import path

from marketplace import views as mk_views
from . import views

urlpatterns = [
    # -- Paiement --
    path("orders/<int:demande_id>/pay/", views.create_payment, name="addons_create_payment"),
    path("orders/<int:demande_id>/payment/", views.payment_status, name="addons_payment_status"),

    # -- Suivi de commande --
    path("orders/tracking/", views.my_orders_tracking, name="addons_orders_tracking"),
    path("orders/<int:demande_id>/tracking/", views.order_tracking, name="addons_order_tracking"),

    # -- Livrables (depot ZIP prestataire / telechargement garde) --
    path("orders/<int:demande_id>/deliverables/", views.deliverables, name="addons_deliverables"),
    path("orders/<int:demande_id>/deliverables/<int:livrable_id>/download/",
         views.download_deliverable, name="addons_download_deliverable"),

    # -- Litiges --
    path("orders/<int:demande_id>/dispute/", views.create_dispute, name="addons_create_dispute"),
    path("disputes/mine/", views.my_disputes, name="addons_my_disputes"),

    # -- CRUD Service (edition / suppression par le prestataire) --
    path("provider/services/<int:service_id>/", views.provider_service_detail,
         name="addons_provider_service_detail"),

    # -- Homepage : section recommandee (publique) --
    path("home/recommended/", views.home_recommended, name="addons_home_recommended"),

    # -- CORRECTION RATING : avis & recommandations sous /api/ --
    path("services/<int:service_id>/review/", mk_views.api_leave_review, name="api_leave_review_fix"),
    path("services/<int:service_id>/reviews/", mk_views.api_service_reviews, name="api_service_reviews_fix"),
    path("services/<int:service_id>/similar/", mk_views.api_similar_services, name="api_similar_services_fix"),
    path("recommendations/smart/", mk_views.api_smart_recommendations, name="api_smart_recommendations_fix"),
    path("providers/top/", mk_views.api_top_providers, name="api_top_providers_fix"),
    path("providers/<int:provider_id>/reputation/", mk_views.api_provider_reputation, name="api_provider_reputation_fix"),
]
