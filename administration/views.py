# apps/administration/views.py
# REMPLACEMENT COMPLET — corrige l'app administration qui référençait des
# modules inexistants (apps.services, apps.orders, apps.evaluations) et des
# champs absents du User par défaut (role, is_verified_provider) ou un FK
# dispute.order qui n'existe pas (le modèle a order_id : IntegerField).
#
# Désormais branché sur les VRAIS modèles :
#   marketplace.Service / Demande / Recommendation / Prestataire / Consommateur
#   addons.Paiement (pour le remboursement et le chiffre d'affaires)

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentCardVerification, Dispute, FlaggedContent

from marketplace.models import (
    Service, Demande, Recommendation, Prestataire, Consommateur, RoleUser,
    EtatCompte,
)

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


def _role_of(user):
    try:
        return user.compte.utilisateur.role
    except Exception:
        return None


# ── M8.1 — Tableau de bord ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    now = timezone.now()
    last_30 = now - timedelta(days=30)

    total_users = User.objects.count()
    new_users_30d = User.objects.filter(date_joined__gte=last_30).count()
    active_providers = Prestataire.objects.filter(carte_verifiee=True).count()
    pending_verification = StudentCardVerification.objects.filter(status='pending').count()

    total_services = Service.objects.count()
    active_services = Service.objects.filter(actif=True).count()
    flagged_services = FlaggedContent.objects.filter(
        content_type='service', status='pending'
    ).count()

    total_orders = Demande.objects.count()
    orders_30d = Demande.objects.filter(date_creation__gte=last_30).count()
    completed_orders = Demande.objects.filter(statut='completed').count()

    # Chiffre d'affaires simulé = somme des paiements "payés" (si l'app addons est là)
    revenue = 0.0
    try:
        from addons.models import Paiement
        revenue = float(
            Paiement.objects.filter(statut='paid').aggregate(t=Sum('montant'))['t'] or 0
        )
    except Exception:
        revenue = 0.0

    open_disputes = Dispute.objects.filter(status__in=['open', 'in_review']).count()

    # Tendance des commandes sur 7 jours
    orders_trend = []
    for i in range(7):
        day = now - timedelta(days=6 - i)
        orders_trend.append({
            'date': day.date().isoformat(),
            'orders': Demande.objects.filter(date_creation__date=day.date()).count(),
        })

    # Top 5 catégories (champ texte Service.categorie)
    top_categories = list(
        Service.objects.filter(actif=True)
        .values('categorie')
        .annotate(service_count=Count('id'))
        .order_by('-service_count')[:5]
    )
    top_categories = [
        {'name': c['categorie'] or 'Autre', 'service_count': c['service_count']}
        for c in top_categories
    ]

    return Response({
        'users': {
            'total': total_users,
            'new_last_30_days': new_users_30d,
            'active_providers': active_providers,
            'pending_verification': pending_verification,
        },
        'services': {
            'total': total_services,
            'active': active_services,
            'flagged_pending': flagged_services,
        },
        'orders': {
            'total': total_orders,
            'last_30_days': orders_30d,
            'completed': completed_orders,
            'revenue_simulated': revenue,
        },
        'disputes': {'open': open_disputes},
        'charts': {'orders_trend': orders_trend, 'top_categories': top_categories},
    })


# ── M8.2 — Gestion des utilisateurs ───────────────────────────────────────────

class UserManagementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = User.objects.select_related('compte__utilisateur').order_by('-date_joined')
        search = request.query_params.get('search', '')
        role = request.query_params.get('role', '')
        active = request.query_params.get('status', '')

        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        if active == 'active':
            qs = qs.filter(is_active=True)
        elif active == 'inactive':
            qs = qs.filter(is_active=False)

        users = list(qs)
        # Filtre par rôle (dérivé de Utilisateur.role, pas un champ du User)
        if role:
            role_map = {'provider': RoleUser.PRESTATAIRE,
                        'consumer': RoleUser.CONSOMMATEUR,
                        'admin': RoleUser.ADMIN}
            target = role_map.get(role)
            if target:
                users = [u for u in users if _role_of(u) == target]

        page = int(request.query_params.get('page', 1))
        per_page = 20
        total = len(users)
        chunk = users[(page - 1) * per_page: page * per_page]

        data = []
        for u in chunk:
            card = getattr(u, 'card_verification', None)
            data.append({
                'id': u.id,
                'email': u.email,
                'full_name': u.get_full_name(),
                'role': (_role_of(u) or 'unknown'),
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat(),
                'card_status': card.status if card else None,
            })
        return Response({'total': total, 'page': page, 'results': data})


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return Response({'error': 'Impossible de modifier un superutilisateur.'}, status=403)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    # Refléter aussi l'état du compte métier
    try:
        user.compte.etat = EtatCompte.ACTIF if user.is_active else EtatCompte.SUSPENDU
        user.compte.save(update_fields=['etat'])
    except Exception:
        pass
    return Response({'id': user.id, 'is_active': user.is_active,
                     'message': f"Compte {'activé' if user.is_active else 'désactivé'}."})


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return Response({'error': 'Impossible de supprimer un superutilisateur.'}, status=403)
    user.delete()
    return Response({'message': 'Compte supprimé.'}, status=204)


# ── M8.3 — Validation des cartes étudiantes ───────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_cards(request):
    cards = StudentCardVerification.objects.filter(
        status='pending'
    ).select_related('user').order_by('submitted_at')
    data = [{
        'id': c.id,
        'user_id': c.user.id,
        'user_name': c.user.get_full_name() or c.user.email,
        'card_image_url': request.build_absolute_uri(c.card_image.url) if c.card_image else None,
        'submitted_at': c.submitted_at.isoformat(),
    } for c in cards]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def review_card(request, card_id):
    """
    POST /api/administration/cards/<id>/review/
    Body: { "action": "approve"|"reject", "rejection_reason": "..." }
    Approuver -> Prestataire.carte_verifiee=True + compte ACTIF.
    """
    card = get_object_or_404(StudentCardVerification, pk=card_id)
    action = request.data.get('action')
    if action not in ['approve', 'reject']:
        return Response({'error': 'action doit être "approve" ou "reject".'}, status=400)

    card.reviewed_by = request.user
    card.reviewed_at = timezone.now()

    if action == 'approve':
        card.status = 'approved'
        try:
            prestataire = card.user.compte.utilisateur.prestataire
            prestataire.carte_verifiee = True
            prestataire.save(update_fields=['carte_verifiee'])
            prestataire.utilisateur.compte.etat = EtatCompte.ACTIF
            prestataire.utilisateur.compte.save(update_fields=['etat'])
        except Exception:
            pass
    else:
        reason = request.data.get('rejection_reason', '')
        if not reason:
            return Response({'error': 'rejection_reason requis pour un refus.'}, status=400)
        card.status = 'rejected'
        card.rejection_reason = reason

    card.save()
    return Response({'status': card.status, 'message': f"Carte {card.status}."})


# ── M8.4 — Modération : signalements & litiges ────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def flagged_content_list(request):
    qs = FlaggedContent.objects.filter(status='pending').order_by('-created_at')
    content_type = request.query_params.get('type')
    if content_type:
        qs = qs.filter(content_type=content_type)
    data = [{
        'id': f.id, 'content_type': f.content_type, 'object_id': f.object_id,
        'reported_by': f.reported_by.email, 'reason': f.reason,
        'created_at': f.created_at.isoformat(),
    } for f in qs]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def moderate_flagged(request, flag_id):
    flag = get_object_or_404(FlaggedContent, pk=flag_id)
    action = request.data.get('action')
    if action == 'remove':
        if flag.content_type == 'service':
            Service.objects.filter(pk=flag.object_id).update(actif=False)
        elif flag.content_type == 'review':
            Recommendation.objects.filter(pk=flag.object_id).delete()
        flag.status = 'removed'
    elif action == 'dismiss':
        flag.status = 'dismissed'
    else:
        return Response({'error': 'action doit être "remove" ou "dismiss".'}, status=400)
    flag.reviewed_by = request.user
    flag.save()
    return Response({'status': flag.status})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dispute_list(request):
    qs = Dispute.objects.select_related('opened_by', 'resolved_by').order_by('-created_at')
    dispute_status = request.query_params.get('status', 'open')
    if dispute_status == 'open':
        qs = qs.filter(status__in=['open', 'in_review'])
    elif dispute_status == 'resolved':
        qs = qs.filter(status__in=['resolved', 'closed'])

    data = []
    for d in qs:
        # order_id pointe vers une Demande (pas de FK)
        commande = Demande.objects.filter(pk=d.order_id).select_related('service').first()
        data.append({
            'id': d.id,
            'order_id': d.order_id,
            'order_title': commande.titre if commande else None,
            'service': commande.service.titre if (commande and commande.service) else None,
            'opened_by': d.opened_by.email,
            'description': d.description,
            'status': d.status,
            'resolution': d.resolution,
            'admin_note': d.admin_note,
            'created_at': d.created_at.isoformat(),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_dispute(request, dispute_id):
    """
    POST /api/administration/disputes/<id>/resolve/
    Body: { "resolution": "refund|completed|partial|dismissed", "admin_note": "..." }
    """
    dispute = get_object_or_404(Dispute, pk=dispute_id)
    resolution = request.data.get('resolution')
    admin_note = request.data.get('admin_note', '')

    valid = [r.value for r in Dispute.Resolution]
    if resolution not in valid:
        return Response({'error': f'Résolution invalide. Options: {valid}'}, status=400)

    dispute.resolution = resolution
    dispute.admin_note = admin_note
    dispute.status = 'resolved'
    dispute.resolved_by = request.user
    dispute.resolved_at = timezone.now()
    dispute.save()

    commande = Demande.objects.filter(pk=dispute.order_id).first()
    if commande:
        if resolution == 'refund':
            commande.statut = 'cancelled'
            commande.save(update_fields=['statut'])
            try:
                from addons.models import Paiement
                p = getattr(commande, 'paiement', None)
                if p and p.statut == 'paid':
                    p.statut = 'refunded'
                    p.save(update_fields=['statut'])
            except Exception:
                pass
        elif resolution == 'completed':
            commande.statut = 'completed'
            commande.save(update_fields=['statut'])

    return Response({'status': 'resolved', 'resolution': resolution})
