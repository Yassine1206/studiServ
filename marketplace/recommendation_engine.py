from django.db.models import Avg, Count

def get_recommendations_for_user(user, limit=6):
    """
    Recommande des services basés sur :
    1. Les meilleures notes (rating moyen)
    2. Les catégories préférées de l'utilisateur
    3. Les services similaires à ses commandes passées
    """
    from .models import Service, Review

    # Catégories que l'utilisateur a déjà commandées
    past_categories = Service.objects.filter(
        reviews__consumer=user
    ).values_list('category', flat=True).distinct()

    # Services bien notés dans ces catégories
    recommended = Service.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).filter(
        is_active=True,
        review_count__gte=1,
    ).exclude(
        reviews__consumer=user  # Pas déjà commandé
    ).order_by('-avg_rating', '-review_count')

    # Prioriser les catégories préférées
    if past_categories:
        preferred = recommended.filter(category__in=past_categories)
        others    = recommended.exclude(category__in=past_categories)
        result    = list(preferred[:limit]) + list(others[:limit])
        return result[:limit]

    return list(recommended[:limit])


def get_top_providers(limit=5):
    """Top prestataires par note moyenne."""
    from .models import Review
    from django.contrib.auth.models import User

    return User.objects.annotate(
        avg_rating=Avg('reviews_received__rating'),
        total_reviews=Count('reviews_received')
    ).filter(
        total_reviews__gte=3
    ).order_by('-avg_rating')[:limit]