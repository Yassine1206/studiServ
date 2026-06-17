"""Public provider profile endpoint.

Ajouté à marketplace via import dans api_urls. À garder séparé pour la lisibilité.
L'endpoint expose le profil public d'un prestataire (par son user_id ou prestataire_id) :
photo, biographie, université, score réputation, badge confiance, services et derniers avis.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Prestataire, Recommendation, ReputationScore
from .serializers import ServiceSerializer, RecommendationSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def api_provider_public_profile(request, provider_id):
    """GET /api/providers/<provider_id>/

    provider_id peut être soit l'ID du Prestataire, soit l'ID du User Django
    (on essaie les deux pour rester flexible).
    """
    prestataire = (
        Prestataire.objects.filter(pk=provider_id).first()
        or Prestataire.objects.filter(utilisateur__compte__user__id=provider_id).first()
    )
    if not prestataire:
        return Response({"message": "Prestataire introuvable."}, status=404)

    utilisateur = prestataire.utilisateur
    profil = getattr(utilisateur, "profil", None)

    # Réputation (créée si absente)
    reputation = getattr(prestataire, "reputation", None)
    if reputation is None:
        try:
            ReputationScore.update_score(prestataire)
            reputation = prestataire.reputation
        except Exception:
            reputation = None

    services = prestataire.services.filter(actif=True)
    recent_reviews = (
        Recommendation.objects.filter(service__prestataire=prestataire)
        .select_related("service", "consommateur__utilisateur")
        .order_by("-date_creation")[:10]
    )

    photo_url = None
    if profil and profil.photo:
        try:
            photo_url = profil.photo.url
        except Exception:
            photo_url = None

    return Response({
        "id": prestataire.id,
        "user_id": utilisateur.compte.user.id if utilisateur.compte else None,
        "nom": utilisateur.nom,
        "prenom": utilisateur.prenom,
        "universite": profil.universite if profil else "",
        "biographie": profil.biographie if profil else "",
        "telephone": profil.telephone if profil else "",
        "photo": photo_url,
        "carte_verifiee": prestataire.carte_verifiee,
        "reputation": {
            "note_moyenne": reputation.note_moyenne if reputation else 0,
            "score_global": reputation.score_global if reputation else 0,
            "taux_completion": reputation.taux_completion if reputation else 0,
            "nb_avis": reputation.nb_avis if reputation else 0,
            "nb_commandes_total": reputation.nb_commandes_total if reputation else 0,
            "badge_confiance": reputation.badge_confiance if reputation else False,
        } if reputation else None,
        "services": ServiceSerializer(services, many=True).data,
        "recent_reviews": RecommendationSerializer(recent_reviews, many=True).data,
    })
