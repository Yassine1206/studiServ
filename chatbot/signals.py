# apps/chatbot/signals.py
# Réindexation automatique dans ChromaDB quand un FAQDocument est sauvegardé

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FAQDocument
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FAQDocument)
def reindex_on_save(sender, instance, created, **kwargs):
    """Réindexe tous les docs actifs après sauvegarde."""
    import threading
    def _reindex():
        try:
            from .rag_engine import index_faq_documents
            count = index_faq_documents()
            logger.info(f"Réindexation automatique : {count} docs après save FAQDocument#{instance.id}")
        except Exception as e:
            logger.error(f"Erreur réindexation auto: {e}")

    thread = threading.Thread(target=_reindex, daemon=True)
    thread.start()


@receiver(post_delete, sender=FAQDocument)
def reindex_on_delete(sender, instance, **kwargs):
    """Réindexe après suppression."""
    import threading
    def _reindex():
        try:
            from .rag_engine import index_faq_documents
            index_faq_documents()
        except Exception as e:
            logger.error(f"Erreur réindexation après delete: {e}")

    thread = threading.Thread(target=_reindex, daemon=True)
    thread.start()
