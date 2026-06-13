# apps/chatbot/models.py
# M9 — Modèles pour le chatbot RAG

from django.db import models
from django.conf import settings


class FAQDocument(models.Model):
    """
    Document source pour le RAG — questions fréquentes et réponses.
    L'admin peut ajouter, modifier, supprimer ces docs.
    Ils sont automatiquement réindexés dans ChromaDB après sauvegarde.
    """

    class Category(models.TextChoices):
        GENERAL = 'general', 'Général'
        ACCOUNT = 'account', 'Compte & Inscription'
        SERVICES = 'services', 'Services & Annonces'
        ORDERS = 'orders', 'Commandes & Paiement'
        MESSAGING = 'messaging', 'Messagerie'
        REPUTATION = 'reputation', 'Réputation & Avis'
        TECHNICAL = 'technical', 'Problèmes techniques'

    title = models.CharField(max_length=255)
    question = models.TextField(help_text="Question fréquente des utilisateurs")
    answer = models.TextField(help_text="Réponse détaillée à cette question")
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    tags = models.CharField(
        max_length=255, blank=True,
        help_text="Tags séparés par des virgules : inscription,étudiant,vérification"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='faq_created'
    )

    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Document FAQ'
        verbose_name_plural = 'Documents FAQ'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    def to_text(self):
        """Texte complet pour l'indexation vectorielle."""
        parts = [f"Question: {self.question}", f"Réponse: {self.answer}"]
        if self.tags:
            parts.append(f"Tags: {self.tags}")
        return "\n".join(parts)


class ChatSession(models.Model):
    """Session de chat entre un utilisateur et le chatbot."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_sessions'
    )
    session_key = models.CharField(max_length=64, unique=True)  # pour les anonymes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_str = self.user.email if self.user else f"anonyme:{self.session_key[:8]}"
        return f"Session chatbot [{user_str}]"


class ChatMessage(models.Model):
    """Message dans une session chatbot."""

    class Role(models.TextChoices):
        USER = 'user', 'Utilisateur'
        ASSISTANT = 'assistant', 'Assistant'

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    sources_used = models.JSONField(default=list, blank=True)  # IDs des FAQDocuments utilisés
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
