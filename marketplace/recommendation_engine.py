
from django.db.models import Avg, Count, Q
from .models import Service, Recommendation, Consommateur, ReputationScore


def get_recommendations_for_user(user, limit=6):
    """
    Recommande des services personnalisés basés sur :
    1. Les catégories préférées de l'utilisateur (historique)
    2. Les meilleures notes (score de réputation)
    3. Les services similaires à ceux déjà commandés
    4. Les nouveaux services populaires

    Retourne une liste de services avec leurs scores.
    """
    # Services déjà commandés par cet utilisateur (à exclure)
    try:
        consommateur = user.compte.utilisateur.consommateur
        already_ordered_ids = Recommendation.objects.filter(
            consommateur=consommateur
        ).values_list('service_id', flat=True)

        # Catégorie préférée enregistrée
        categorie_preferee = consommateur.categorie_preferee or ''
    except Exception:
        already_ordered_ids = []
        categorie_preferee = ''

    # Base query — services actifs avec leurs scores
    base_qs = Service.objects.filter(actif=True).exclude(
        id__in=already_ordered_ids
    ).annotate(
        avg_score=Avg('recommendations__score'),
        nb_avis=Count('recommendations'),
    )

    results = []

    # 1. Services dans la catégorie préférée bien notés
    if categorie_preferee:
        preferred = list(
            base_qs.filter(
                categorie__icontains=categorie_preferee,
                nb_avis__gte=1
            ).order_by('-avg_score', '-nb_avis')[:limit]
        )
        results.extend(preferred)

    # 2. Services les mieux notés (tous prestataires avec badge de confiance)
    top_rated_provider_ids = ReputationScore.objects.filter(
        badge_confiance=True
    ).values_list('prestataire_id', flat=True)

    trusted = list(
        base_qs.filter(
            prestataire_id__in=top_rated_provider_ids
        ).exclude(
            id__in=[s.id for s in results]
        ).order_by('-avg_score', '-nb_avis')[:limit]
    )
    results.extend(trusted)

    # 3. Services populaires (les plus commandés) en complément
    if len(results) < limit:
        popular = list(
            base_qs.exclude(
                id__in=[s.id for s in results]
            ).filter(nb_avis__gte=1).order_by('-nb_avis')[:limit - len(results)]
        )
        results.extend(popular)

    # 4. Si toujours pas assez → nouveaux services sans avis
    if len(results) < limit:
        new_services = list(
            base_qs.exclude(
                id__in=[s.id for s in results]
            ).order_by('-date_creation')[:limit - len(results)]
        )
        results.extend(new_services)

    # Dédupliquer et limiter
    seen = set()
    final = []
    for s in results:
        if s.id not in seen:
            seen.add(s.id)
            final.append(s)
        if len(final) >= limit:
            break

    return final


def get_top_providers(limit=5):
    """
    Retourne les meilleurs prestataires classés par score de réputation.
    Utilisé pour la section 'Top prestataires' de la page d'accueil.
    """
    return ReputationScore.objects.filter(
        nb_avis__gte=1
    ).select_related(
        'prestataire__utilisateur__profil'
    ).order_by('-score_global')[:limit]


def get_similar_services(service, limit=4):
    """
    Retourne des services similaires à un service donné.
    Basé sur la même catégorie et les meilleures notes.
    """
    return Service.objects.filter(
        actif=True,
        categorie=service.categorie
    ).exclude(
        id=service.id
    ).annotate(
        avg_score=Avg('recommendations__score'),
        nb_avis=Count('recommendations'),
    ).order_by('-avg_score', '-nb_avis')[:limit]


def update_user_preferred_category(user):
    """
    Met à jour automatiquement la catégorie préférée du consommateur
    basée sur ses commandes (la catégorie la plus fréquente).
    Appelée après chaque évaluation laissée.
    """
    try:
        consommateur = user.compte.utilisateur.consommateur

        # Compter les avis par catégorie
        from django.db.models import Count as DCount
        category_counts = Recommendation.objects.filter(
            consommateur=consommateur
        ).values(
            'service__categorie'
        ).annotate(
            count=DCount('id')
        ).order_by('-count')

        if category_counts.exists():
            top_category = category_counts.first()['service__categorie']
            consommateur.categorie_preferee = top_category
            consommateur.save(update_fields=['categorie_preferee'])

    except Exception:
        pass
