# addons/views.py
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from marketplace.models import Demande
from .models import Paiement, Livrable
from .serializers import (
    PaiementSerializer, LivrableSerializer, OrderTrackingSerializer,
)
from .payment_utils import process_payment


# ─── Helpers de rôle ──────────────────────────────────────────────────────────

def _consommateur(user):
    try:
        return user.compte.utilisateur.consommateur
    except Exception:
        return None


def _prestataire(user):
    try:
        return user.compte.utilisateur.prestataire
    except Exception:
        return None


def _is_order_consumer(user, demande):
    c = _consommateur(user)
    return c is not None and demande.consommateur_id == c.id


def _is_order_provider(user, demande):
    p = _prestataire(user)
    return (
        p is not None
        and demande.service is not None
        and demande.service.prestataire_id == p.id
    )


# ─── PAIEMENT ───────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment(request, demande_id):
    """
    POST /api/orders/<demande_id>/pay/
    Body: { card_number, card_name, exp_month, exp_year, cvv, methode? }
    Valide la carte, "encaisse" (simulé), passe la commande en cours.
    """
    demande = get_object_or_404(Demande, pk=demande_id)

    if not _is_order_consumer(request.user, demande):
        return Response({"error": "Seul l'auteur de la commande peut payer."},
                        status=status.HTTP_403_FORBIDDEN)

    if not demande.service:
        return Response({"error": "Commande sans service associé."}, status=400)

    montant = demande.service.prix

    paiement, _ = Paiement.objects.get_or_create(
        demande=demande,
        defaults={"montant": montant, "methode": request.data.get("methode", "card")},
    )

    if paiement.is_paid:
        return Response({"error": "Cette commande est déjà payée.",
                         "paiement": PaiementSerializer(paiement).data}, status=400)

    result = process_payment(montant, request.data)
    if not result["success"]:
        paiement.statut = Paiement.Statut.FAILED
        paiement.echec_raison = result["error"]
        paiement.save(update_fields=["statut", "echec_raison"])
        return Response({"error": result["error"]}, status=status.HTTP_402_PAYMENT_REQUIRED)

    paiement.mark_paid(
        last4=result["last4"], brand=result["brand"], ref=result["reference"]
    )
    return Response(
        {"message": "Paiement accepté.", "paiement": PaiementSerializer(paiement).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_status(request, demande_id):
    """GET /api/orders/<demande_id>/payment/ — état du paiement d'une commande."""
    demande = get_object_or_404(Demande, pk=demande_id)
    if not (_is_order_consumer(request.user, demande)
            or _is_order_provider(request.user, demande)):
        return Response({"error": "Accès refusé."}, status=403)
    paiement = getattr(demande, "paiement", None)
    if not paiement:
        return Response({"statut": "none", "is_paid": False})
    return Response(PaiementSerializer(paiement).data)


# ─── SUIVI DE COMMANDE (consommateur) ─────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_tracking(request, demande_id):
    """
    GET /api/orders/<demande_id>/tracking/
    Suivi : statut, paiement, deadline, dispo du livrable.
    """
    demande = get_object_or_404(
        Demande.objects.select_related("service", "paiement"), pk=demande_id
    )
    if not (_is_order_consumer(request.user, demande)
            or _is_order_provider(request.user, demande)):
        return Response({"error": "Accès refusé."}, status=403)
    return Response(OrderTrackingSerializer(demande).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders_tracking(request):
    """
    GET /api/orders/tracking/
    Liste de suivi de toutes les commandes du consommateur connecté.
    """
    consommateur = _consommateur(request.user)
    if consommateur is None:
        return Response({"error": "Accès réservé aux consommateurs."}, status=403)
    demandes = (
        consommateur.demandes
        .select_related("service", "paiement")
        .order_by("-date_creation")
    )
    return Response(OrderTrackingSerializer(demandes, many=True).data)


# ─── LIVRABLES ────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def deliverables(request, demande_id):
    """
    GET  /api/orders/<demande_id>/deliverables/  — liste (consommateur ou prestataire)
    POST /api/orders/<demande_id>/deliverables/  — dépôt d'un ZIP (prestataire uniquement)
    """
    demande = get_object_or_404(Demande, pk=demande_id)

    if request.method == "GET":
        if not (_is_order_consumer(request.user, demande)
                or _is_order_provider(request.user, demande)):
            return Response({"error": "Accès refusé."}, status=403)
        qs = demande.livrables.all()
        return Response(LivrableSerializer(qs, many=True).data)

    # POST — dépôt
    if not _is_order_provider(request.user, demande):
        return Response({"error": "Seul le prestataire de la commande peut déposer un livrable."},
                        status=403)

    fichier = request.FILES.get("fichier") or request.FILES.get("file")
    if not fichier:
        return Response({"error": "Aucun fichier fourni."}, status=400)

    name = (fichier.name or "").lower()
    is_zip = (
        name.endswith(".zip")
        or getattr(fichier, "content_type", "") in (
            "application/zip", "application/x-zip-compressed",
            "application/octet-stream",
        )
    )
    if not is_zip:
        return Response({"error": "Le livrable doit être une archive .zip."}, status=400)

    max_size = 50 * 1024 * 1024  # 50 MB
    if fichier.size > max_size:
        return Response({"error": "Archive trop volumineuse (max 50 Mo)."}, status=400)

    livrable = Livrable.objects.create(
        demande=demande,
        fichier=fichier,
        nom_original=fichier.name,
        description=request.data.get("description", ""),
        taille_octets=fichier.size,
        depose_par=request.user,
    )
    return Response(LivrableSerializer(livrable).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_deliverable(request, demande_id, livrable_id):
    """
    GET /api/orders/<demande_id>/deliverables/<livrable_id>/download/
    Téléchargement GARDÉ : le consommateur doit avoir payé.
    Le prestataire (auteur) peut toujours retélécharger le sien.
    """
    demande = get_object_or_404(Demande, pk=demande_id)
    livrable = get_object_or_404(Livrable, pk=livrable_id, demande=demande)

    if _is_order_provider(request.user, demande):
        pass  # le prestataire accède à son propre dépôt
    elif _is_order_consumer(request.user, demande):
        paiement = getattr(demande, "paiement", None)
        if not (paiement and paiement.is_paid):
            return Response(
                {"error": "Paiement requis pour accéder au livrable."},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
    else:
        return Response({"error": "Accès refusé."}, status=403)

    try:
        f = livrable.fichier.open("rb")
    except Exception:
        raise Http404("Fichier introuvable.")
    response = FileResponse(f, as_attachment=True,
                            filename=livrable.nom_original or "livrable.zip")
    return response


# ─── CRUD SERVICE (édition / suppression par le prestataire) ──────────────────

@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def provider_service_detail(request, service_id):
    """
    GET/PUT/PATCH/DELETE /api/provider/services/<service_id>/
    Le prestataire ne peut modifier/supprimer QUE ses propres services.
    DELETE = désactivation douce (actif=False) pour préserver l'historique.
    """
    from marketplace.models import Service
    from marketplace.serializers import ServiceSerializer, ServiceCreateSerializer

    prestataire = _prestataire(request.user)
    if prestataire is None:
        return Response({"error": "Accès réservé aux prestataires."}, status=403)

    try:
        service = Service.objects.get(pk=service_id, prestataire=prestataire)
    except Service.DoesNotExist:
        return Response({"error": "Service introuvable ou non autorisé."}, status=404)

    if request.method == "GET":
        return Response(ServiceSerializer(service).data)

    if request.method == "DELETE":
        service.actif = False
        service.save(update_fields=["actif"])
        return Response({"message": "Service désactivé."}, status=200)

    # PUT / PATCH — mise à jour partielle autorisée
    partial = request.method == "PATCH"
    allowed = ["titre", "description", "categorie", "prix", "delai_livraison", "actif"]
    data = {k: v for k, v in request.data.items() if k in allowed}
    serializer = ServiceCreateSerializer(
        service, data=data, partial=partial, context={"request": request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    serializer.save()
    return Response(ServiceSerializer(service).data)


# ─── HOMEPAGE — sections recommandées (PUBLIC) ────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def home_recommended(request):
    """
    GET /api/home/recommended/
    Section "recommandé" de la page d'accueil — accessible sans connexion.
    Renvoie : meilleurs prestataires + services les mieux notés
    (+ recommandations personnalisées si l'utilisateur est connecté).
    """
    from marketplace.models import Service
    from marketplace.recommendation_engine import get_top_providers

    # Top prestataires (par score de réputation)
    providers = []
    try:
        for rep in get_top_providers(limit=6):
            p = rep.prestataire
            photo = None
            try:
                photo = p.utilisateur.profil.photo.url if p.utilisateur.profil.photo else None
            except Exception:
                photo = None
            providers.append({
                "prestataire_id": p.id,
                "nom": str(p.utilisateur),
                "photo": photo,
                "note_moyenne": rep.note_moyenne,
                "score_global": rep.score_global,
                "nb_avis": rep.nb_avis,
                "badge_confiance": rep.badge_confiance,
                "nb_services": p.services.filter(actif=True).count(),
            })
    except Exception:
        providers = []

    # Services les mieux notés (public)
    from django.db.models import Avg, Count
    top_services_qs = (
        Service.objects.filter(actif=True)
        .annotate(avg_score=Avg("recommendations__score"),
                  nb_avis=Count("recommendations"))
        .order_by("-avg_score", "-nb_avis")[:8]
    )
    top_services = [{
        "id": s.id,
        "titre": s.titre,
        "categorie": s.categorie,
        "prix": str(s.prix),
        "provider_name": str(s.prestataire.utilisateur),
        "note_moyenne": round(s.avg_score or 0, 1),
        "nb_avis": s.nb_avis or 0,
    } for s in top_services_qs]

    # Personnalisé (si consommateur connecté)
    personalized = []
    if request.user and request.user.is_authenticated:
        try:
            from marketplace.recommendation_engine import get_recommendations_for_user
            for s in get_recommendations_for_user(request.user, limit=6):
                personalized.append({
                    "id": s.id, "titre": s.titre, "categorie": s.categorie,
                    "prix": str(s.prix), "provider_name": str(s.prestataire.utilisateur),
                })
        except Exception:
            personalized = []

    return Response({
        "top_providers": providers,
        "top_services": top_services,
        "personalized": personalized,
    })


# ─── LITIGES / DISPUTES ───────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_dispute(request, demande_id):
    """
    POST /api/orders/<demande_id>/dispute/
    Le consommateur OU le prestataire de la commande peut ouvrir un litige.
    Body: { "description": "..." }
    """
    from administration.models import Dispute

    demande = get_object_or_404(Demande, pk=demande_id)
    if not (_is_order_consumer(request.user, demande)
            or _is_order_provider(request.user, demande)):
        return Response({"error": "Accès refusé."}, status=403)

    description = (request.data.get("description") or "").strip()
    if not description:
        return Response({"error": "Décris le problème rencontré."}, status=400)

    # Un seul litige ouvert par commande
    existing = Dispute.objects.filter(
        order_id=demande.id, status__in=["open", "in_review"]
    ).first()
    if existing:
        return Response({"error": "Un litige est déjà ouvert pour cette commande.",
                         "dispute_id": existing.id}, status=400)

    dispute = Dispute.objects.create(
        order_id=demande.id,
        opened_by=request.user,
        description=description,
        status="open",
    )
    return Response({"message": "Litige ouvert. L'administrateur va l'examiner.",
                     "dispute_id": dispute.id}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_disputes(request):
    """GET /api/disputes/mine/ — litiges ouverts par l'utilisateur connecté."""
    from administration.models import Dispute
    qs = Dispute.objects.filter(opened_by=request.user).order_by("-created_at")
    data = [{
        "id": d.id, "order_id": d.order_id, "description": d.description,
        "status": d.status, "resolution": d.resolution,
        "admin_note": d.admin_note, "created_at": d.created_at.isoformat(),
    } for d in qs]
    return Response(data)
