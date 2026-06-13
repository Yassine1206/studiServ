# apps/messaging/models.py
# M4 — Messagerie interne temps réel (WebSocket)

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Conversation entre un consommateur et un prestataire,
    liée optionnellement à une commande spécifique.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    order_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        users = ', '.join(str(u) for u in self.participants.all())
        return f"Conversation [{users}]"

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()


class Message(models.Model):
    """Message dans une conversation."""

    class MessageType(models.TextChoices):
        TEXT = 'text', 'Texte'
        FILE = 'file', 'Fichier'
        IMAGE = 'image', 'Image'
        SYSTEM = 'system', 'Système'

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='messages/files/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.content[:50]}"

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None


class Notification(models.Model):
    """Notification pour nouveaux messages."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='notifications'
    )
    unread_count = models.PositiveIntegerField(default=0)
    last_notified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'conversation')
