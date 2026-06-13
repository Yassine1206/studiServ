# apps/administration/views.py
# M8 — Dashboard administration + gestion utilisateurs + modération

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from .models import StudentCardVerification, Dispute, FlaggedContent

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """Seuls les admins (is_staff) peuvent accéder."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


# ─────────────────────────────────────────────────────────────────────────────
# M8.1 — Tableau de bord : statistiques globales
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    """
    GET /api/administration/dashboard/
    Statistiques globales pour le tableau de bord admin.
    """
    from apps.services.models import Service
    from apps.orders.models import Order

    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    # Utilisateurs
    total_users = User.objects.count()
    new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
    active_providers = User.objects.filter(
        role='provider', is_active=True
    ).count()
    pending_verification = StudentCardVerification.objects.filter(
        status='pending'
    ).count()

    # Services
    total_services = Service.objects.count()
    active_services = Service.objects.filter(is_active=True).count()
    flagged_services = FlaggedContent.objects.filter(
        content_type='service', status='pending'
    ).count()

    # Commandes
    total_orders = Order.objects.count()
    orders_30d = Order.objects.filter(created_at__gte=last_30_days).count()
    completed_orders = Order.objects.filter(status='completed').count()
    revenue_simulated = Order.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Litiges
    open_disputes = Dispute.objects.filter(status__in=['open', 'in_review']).count()

    # Graphe commandes 7 derniers jours
    orders_trend = []
    for i in range(7):
        day = now - timedelta(days=6 - i)
        count = Order.objects.filter(
            created_at__date=day.date()
        ).count()
        orders_trend.append({
            'date': day.date().isoformat(),
            'orders': count
        })

    # Top 5 catégories
    from apps.services.models import ServiceCategory
    top_categories = ServiceCategory.objects.annotate(
        service_count=Count('services')
    ).order_by('-service_count')[:5].values('name', 'service_count')

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
            'revenue_simulated': float(revenue_simulated),
        },
        'disputes': {
            'open': open_disputes,
        },
        'charts': {
            'orders_trend': orders_trend,
            'top_categories': list(top_categories),
        }
    })


# ─────────────────────────────────────────────────────────────────────────────
# M8.2 — Gestion des utilisateurs
# ─────────────────────────────────────────────────────────────────────────────

class UserManagementView(APIView):
    """
    GET  /api/administration/users/?search=&role=&status=
    Liste et filtrage des utilisateurs.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = User.objects.all().order_by('-date_joined')
        search = request.query_params.get('search', '')
        role = request.query_params.get('role', '')
        active = request.query_params.get('status', '')

        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if active == 'active':
            qs = qs.filter(is_active=True)
        elif active == 'inactive':
            qs = qs.filter(is_active=False)

        # Pagination simple
        page = int(request.query_params.get('page', 1))
        per_page = 20
        total = qs.count()
        users = qs[(page - 1) * per_page: page * per_page]

        data = [
            {
                'id': u.id,
                'email': u.email,
                'full_name': u.get_full_name(),
                'role': getattr(u, 'role', 'unknown'),
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat(),
                'card_status': getattr(
                    getattr(u, 'card_verification', None), 'status', None
                ),
            }
            for u in users
        ]
        return Response({'total': total, 'page': page, 'results': data})


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_user_status(request, user_id):
    """
    PATCH /api/administration/users/<id>/toggle/
    Activer ou désactiver un compte utilisateur.
    """
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return Response({'error': 'Impossible de modifier un superutilisateur.'}, status=403)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return Response({
        'id': user.id,
        'is_active': user.is_active,
        'message': f"Compte {'activé' if user.is_active else 'désactivé'}."
    })


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    """
    DELETE /api/administration/users/<id>/
    Supprimer définitivement un compte.
    """
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return Response({'error': 'Impossible de supprimer un superutilisateur.'}, status=403)
    user.delete()
    return Response({'message': 'Compte supprimé.'}, status=204)


# ─────────────────────────────────────────────────────────────────────────────
# M8.3 — Validation des cartes étudiantes
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_cards(request):
    """
    GET /api/administration/cards/
    Liste des cartes étudiantes en attente de validation.
    """
    cards = StudentCardVerification.objects.filter(
        status='pending'
    ).select_related('user').order_by('submitted_at')

    data = [
        {
            'id': c.id,
            'user_id': c.user.id,
            'user_name': c.user.get_full_name() or c.user.email,
            'card_image_url': request.build_absolute_uri(c.card_image.url) if c.card_image else None,
            'submitted_at': c.submitted_at.isoformat(),
        }
        for c in cards
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def review_card(request, card_id):
    """
    POST /api/administration/cards/<id>/review/
    Body: { "action": "approve"|"reject", "rejection_reason": "..." }
    """
    card = get_object_or_404(StudentCardVerification, pk=card_id)
    action = request.data.get('action')

    if action not in ['approve', 'reject']:
        return Response({'error': 'action doit être "approve" ou "reject".'}, status=400)

    card.reviewed_by = request.user
    card.reviewed_at = timezone.now()

    if action == 'approve':
        card.status = 'approved'
        card.user.is_verified_provider = True
        card.user.save(update_fields=['is_verified_provider'])
    else:
        reason = request.data.get('rejection_reason', '')
        if not reason:
            return Response({'error': 'rejection_reason requis pour un refus.'}, status=400)
        card.status = 'rejected'
        card.rejection_reason = reason

    card.save()
    return Response({'status': card.status, 'message': f"Carte {card.status}."})


# ─────────────────────────────────────────────────────────────────────────────
# M8.4 — Modération : signalements & litiges
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def flagged_content_list(request):
    """
    GET /api/administration/flagged/?type=service|review
    Liste des contenus signalés.
    """
    qs = FlaggedContent.objects.filter(status='pending').order_by('-created_at')
    content_type = request.query_params.get('type')
    if content_type:
        qs = qs.filter(content_type=content_type)

    data = [
        {
            'id': f.id,
            'content_type': f.content_type,
            'object_id': f.object_id,
            'reported_by': f.reported_by.email,
            'reason': f.reason,
            'created_at': f.created_at.isoformat(),
        }
        for f in qs
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def moderate_flagged(request, flag_id):
    """
    POST /api/administration/flagged/<id>/moderate/
    Body: { "action": "remove"|"dismiss" }
    """
    flag = get_object_or_404(FlaggedContent, pk=flag_id)
    action = request.data.get('action')

    if action == 'remove':
        # Supprimer le contenu ciblé
        if flag.content_type == 'service':
            from apps.services.models import Service
            Service.objects.filter(pk=flag.object_id).delete()
        elif flag.content_type == 'review':
            from apps.evaluations.models import Review
            Review.objects.filter(pk=flag.object_id).delete()
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
    """
    GET /api/administration/disputes/?status=open
    Liste des litiges.
    """
    qs = Dispute.objects.select_related(
        'order', 'opened_by', 'resolved_by'
    ).order_by('-created_at')

    dispute_status = request.query_params.get('status', 'open')
    if dispute_status == 'open':
        qs = qs.filter(status__in=['open', 'in_review'])
    elif dispute_status == 'resolved':
        qs = qs.filter(status__in=['resolved', 'closed'])

    data = [
        {
            'id': d.id,
            'order_id': d.order_id,
            'opened_by': d.opened_by.email,
            'description': d.description,
            'status': d.status,
            'resolution': d.resolution,
            'admin_note': d.admin_note,
            'created_at': d.created_at.isoformat(),
        }
        for d in qs
    ]
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

    valid_resolutions = [r.value for r in Dispute.Resolution]
    if resolution not in valid_resolutions:
        return Response({'error': f'Résolution invalide. Options: {valid_resolutions}'}, status=400)

    dispute.resolution = resolution
    dispute.admin_note = admin_note
    dispute.status = 'resolved'
    dispute.resolved_by = request.user
    dispute.resolved_at = timezone.now()
    dispute.save()

    # Si remboursement → annuler la commande
    if resolution == 'refund':
        dispute.order.status = 'cancelled'
        dispute.order.save(update_fields=['status'])

    return Response({'status': 'resolved', 'resolution': resolution})
