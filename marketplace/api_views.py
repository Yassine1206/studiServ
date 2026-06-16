"""
Vues API REST pour StudiServ.
Ces vues s'ajoutent aux vues Django classiques existantes (templates HTML).
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .recommendation_engine import get_recommendations_for_user, get_top_providers

from .models import (
    Compte, Utilisateur, Consommateur, Prestataire,
    Service, Demande, Recommendation, RoleUser, EtatCompte,
)
from .serializers import (
    SignUpSerializer, SignInSerializer,
    UserProfileSerializer, UpdateProfileSerializer,
    ServiceSerializer, ServiceCreateSerializer,
    DemandeSerializer, DemandeCreateSerializer,
    RecommendationSerializer, AdminUserSerializer,
    get_tokens_for_user,
)


def get_user_role(user):
    """Retourne le rôle lisible (consumer / provider / admin)."""
    if user.is_superuser or user.is_staff:
        return "admin"
    try:
        role = user.compte.utilisateur.role
        return {
            RoleUser.ADMIN: "admin",
            RoleUser.CONSOMMATEUR: "consumer",
            RoleUser.PRESTATAIRE: "provider",
        }.get(role, "consumer")
    except Exception:
        return "consumer"


# ─── AUTHENTIFICATION ─────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def api_signup(request):
    """
    POST /api/auth/signup/
    Crée un compte et retourne les tokens JWT.
    """
    serializer = SignUpSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    tokens = get_tokens_for_user(user)
    role = get_user_role(user)

    return Response(
        {
            "token": tokens["access"],
            "refresh": tokens["refresh"],
            "role": role,
            "user": {
                "id": user.pk,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "message": (
                "Compte créé. En attente de vérification de la carte étudiante."
                if role == "provider"
                else "Inscription réussie !"
            ),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def api_signin(request):
    """
    POST /api/auth/signin/
    Authentifie l'utilisateur et retourne les tokens JWT.
    """
    serializer = SignInSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    # EmailBackend accepte l'email dans le champ `username`
    user = authenticate(request, username=email, password=password)
    if not user:
        return Response(
            {"message": "Email ou mot de passe incorrect."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Vérifier que le compte n'est pas suspendu
    try:
        if user.compte.etat == EtatCompte.SUSPENDU:
            return Response(
                {"message": "Votre compte a été suspendu. Contactez l'administration."},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Exception:
        pass

    tokens = get_tokens_for_user(user)
    role = get_user_role(user)

    return Response(
        {
            "token": tokens["access"],
            "refresh": tokens["refresh"],
            "role": role,
            "user": {
                "id": user.pk,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    POST /api/auth/logout/
    Blackliste le refresh token (optionnel avec ROTATE_REFRESH_TOKENS=True).
    """
    return Response({"message": "Déconnexion réussie."})


@api_view(["POST"])
@permission_classes([AllowAny])
def api_reset_password(request):
    """
    POST /api/auth/reset-password/
    Placeholder — à compléter avec l'envoi d'email.
    """
    email = request.data.get("email", "")
    # TODO: Envoyer un email de réinitialisation
    return Response(
        {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_token_refresh_custom(request):
    """Alias pratique — utiliser l'endpoint simplejwt directement."""
    return Response({"detail": "Utilisez /api/auth/token/refresh/"})


# ─── PROFIL UTILISATEUR ─────────────────────────────────────────────────────────

@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """GET/PUT /api/auth/profile/"""
    if request.method == "GET":
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    serializer = UpdateProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.update(request.user, serializer.validated_data)
    return Response({"message": "Profil mis à jour."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_upload_avatar(request):
    """POST /api/auth/avatar/"""
    if "avatar" not in request.FILES:
        return Response(
            {"message": "Aucun fichier envoyé."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        profil = request.user.compte.utilisateur.profil
        profil.photo = request.FILES["avatar"]
        profil.save()
        return Response({"message": "Photo mise à jour.", "url": profil.photo.url})
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── SERVICES ─────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def api_services_list(request):
    """GET /api/services/ — accessible sans authentification."""
    qs = Service.objects.filter(actif=True).select_related(
        "prestataire__utilisateur"
    )
    # Filtre par catégorie
    categorie = request.query_params.get("categorie")
    if categorie and categorie != "all":
        qs = qs.filter(categorie__iexact=categorie)
    # Recherche textuelle
    q = request.query_params.get("q")
    if q:
        qs = qs.filter(titre__icontains=q) | qs.filter(description__icontains=q)

    serializer = ServiceSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_service_detail(request, pk):
    """GET /api/services/<pk>/"""
    try:
        service = Service.objects.get(pk=pk, actif=True)
    except Service.DoesNotExist:
        return Response({"message": "Service introuvable."}, status=404)
    serializer = ServiceSerializer(service)
    return Response(serializer.data)


# ─── CONSOMMATEUR ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_consumer_orders(request):
    """GET /api/consumer/orders/"""
    try:
        consommateur = request.user.compte.utilisateur.consommateur
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    demandes = consommateur.demandes.select_related("service").order_by("-date_creation")
    serializer = DemandeSerializer(demandes, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_create_order(request, service_id):
    """POST /api/services/<service_id>/order/"""
    try:
        service = Service.objects.get(pk=service_id, actif=True)
    except Service.DoesNotExist:
        return Response({"message": "Service introuvable."}, status=404)

    serializer = DemandeCreateSerializer(
        data={**request.data, "service": service.pk},
        context={"request": request},
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    demande = serializer.save()
    return Response(
        DemandeSerializer(demande).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_consumer_recommendations(request):
    """GET /api/recommendations/"""
    try:
        consommateur = request.user.compte.utilisateur.consommateur
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
    recs = consommateur.recommendations.select_related("service").order_by("-date_creation")
    serializer = RecommendationSerializer(recs, many=True)
    return Response(serializer.data)


# ─── PRESTATAIRE ──────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def api_provider_services(request):
    """GET /api/provider/services/ | POST pour créer un service."""
    try:
        prestataire = request.user.compte.utilisateur.prestataire
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        services = prestataire.services.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    # POST — bloquer la publication tant que l'admin n'a pas validé la carte étudiante
    if not prestataire.carte_verifiee:
        return Response(
            {"message": "Ton compte n'est pas encore vérifié. "
                        "Un administrateur doit valider ta carte étudiante "
                        "avant que tu puisses publier un service."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ServiceCreateSerializer(
        data=request.data, context={"request": request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    service = serializer.save()
    return Response(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_provider_orders(request):
    """GET /api/provider/orders/"""
    try:
        prestataire = request.user.compte.utilisateur.prestataire
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    demandes = Demande.objects.filter(
        service__prestataire=prestataire
    ).select_related("service", "consommateur__utilisateur").order_by("-date_creation")
    serializer = DemandeSerializer(demandes, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_provider_update_order(request, demande_id):
    """POST /api/provider/orders/<demande_id>/status/
    Body: { "statut": "in_progress" | "completed" | "cancelled" }
    Transitions autorisees : pending -> in_progress -> completed ; * -> cancelled."""
    try:
        prestataire = request.user.compte.utilisateur.prestataire
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    try:
        demande = Demande.objects.select_related("service").get(pk=demande_id)
    except Demande.DoesNotExist:
        return Response({"message": "Commande introuvable."}, status=404)

    if not demande.service or demande.service.prestataire_id != prestataire.id:
        return Response({"message": "Cette commande n'est pas la vôtre."}, status=403)

    new_status = request.data.get("statut")
    allowed = {
        "pending":     ["in_progress", "cancelled"],
        "in_progress": ["completed",   "cancelled"],
    }
    if new_status not in allowed.get(demande.statut, []):
        return Response(
            {"message": f"Transition '{demande.statut}' -> '{new_status}' non autorisée."},
            status=400,
        )

    demande.statut = new_status
    demande.save(update_fields=["statut"])
    return Response(DemandeSerializer(demande).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_provider_statistics(request):
    """GET /api/provider/statistics/"""
    try:
        prestataire = request.user.compte.utilisateur.prestataire
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    services = prestataire.services.all()
    demandes = Demande.objects.filter(service__prestataire=prestataire)
    completed = demandes.filter(statut="completed").count()
    total = demandes.count()

    all_recs = Recommendation.objects.filter(service__prestataire=prestataire)
    avg_rating = (
        round(sum(r.score for r in all_recs) / all_recs.count(), 1)
        if all_recs.exists() else 0
    )

    return Response(
        {
            "totalEarnings": float(prestataire.revenue),
            "totalOrders": total,
            "completionRate": round((completed / total * 100) if total else 0, 1),
            "reputation": avg_rating,
            "totalReviews": all_recs.count(),
            "totalServices": services.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_provider_reviews(request):
    """GET /api/provider/reviews/"""
    try:
        prestataire = request.user.compte.utilisateur.prestataire
    except Exception:
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    reviews = Recommendation.objects.filter(
        service__prestataire=prestataire
    ).select_related("service", "consommateur__utilisateur").order_by("-date_creation")

    serializer = RecommendationSerializer(reviews, many=True)
    return Response(serializer.data)


# ─── ADMINISTRATION ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_admin_users(request):
    """GET /api/admin/users/"""
    if get_user_role(request.user) != "admin":
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.select_related(
        "compte__utilisateur__prestataire"
    ).order_by("-date_joined")
    serializer = AdminUserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_admin_suspend_user(request, user_id):
    """POST /api/admin/users/<id>/suspend/"""
    if get_user_role(request.user) != "admin":
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
    try:
        target = User.objects.get(pk=user_id)
        target.compte.etat = EtatCompte.SUSPENDU
        target.compte.save()
        return Response({"message": "Compte suspendu."})
    except User.DoesNotExist:
        return Response({"message": "Utilisateur introuvable."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_admin_activate_user(request, user_id):
    """POST /api/admin/users/<id>/activate/"""
    if get_user_role(request.user) != "admin":
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
    try:
        target = User.objects.get(pk=user_id)
        target.compte.etat = EtatCompte.ACTIF
        target.compte.save()
        return Response({"message": "Compte activé."})
    except User.DoesNotExist:
        return Response({"message": "Utilisateur introuvable."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_admin_verify_card(request, user_id):
    """POST /api/admin/verify-card/<id>/"""
    if get_user_role(request.user) != "admin":
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
    approved = request.data.get("approved", False)
    try:
        prestataire = User.objects.get(pk=user_id).compte.utilisateur.prestataire
        prestataire.carte_verifiee = approved
        prestataire.save()
        # Activer le compte si approuvé
        if approved:
            prestataire.utilisateur.compte.etat = EtatCompte.ACTIF
            prestataire.utilisateur.compte.save()
        return Response({"message": "Carte vérifiée." if approved else "Carte rejetée."})
    except Exception:
        return Response({"message": "Prestataire introuvable."}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_admin_statistics(request):
    """GET /api/admin/statistics/"""
    if get_user_role(request.user) != "admin":
        return Response({"message": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    total_users = User.objects.count()
    total_providers = Prestataire.objects.count()
    total_consumers = Consommateur.objects.count()
    total_services = Service.objects.filter(actif=True).count()
    total_orders = Demande.objects.count()

    return Response(
        {
            "totalUsers": total_users,
            "totalProviders": total_providers,
            "totalConsumers": total_consumers,
            "totalServices": total_services,
            "totalOrders": total_orders,
            "averageRating": 0,
        }
    )
