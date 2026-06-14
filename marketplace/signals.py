from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Recommendation, ReputationScore
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Recommendation)
def update_reputation_on_review(sender, instance, created, **kwargs):
    """
    Recalcule le score de réputation du prestataire
    automatiquement après chaque nouvel avis ou modification.
    """
    try:
        prestataire = instance.service.prestataire
        rep = ReputationScore.update_score(prestataire)
        logger.info(
            f"Score mis à jour pour {prestataire} → {rep.score_global}/5 "
            f"({rep.nb_avis} avis, badge={rep.badge_confiance})"
        )
    except Exception as e:
        logger.error(f"Erreur mise à jour réputation : {e}")


@receiver(post_delete, sender=Recommendation)
def update_reputation_on_delete(sender, instance, **kwargs):
    """Recalcule aussi quand un avis est supprimé (modération admin)."""
    try:
        prestataire = instance.service.prestataire
        ReputationScore.update_score(prestataire)
    except Exception as e:
        logger.error(f"Erreur mise à jour réputation après suppression : {e}")
