# apps/administration/models.py
# M8 — Modèles spécifiques à l'administration

from django.db import models
from django.conf import settings


class StudentCardVerification(models.Model):
    """Vérification de carte étudiante soumise par un prestataire."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        APPROVED = 'approved', 'Approuvée'
        REJECTED = 'rejected', 'Refusée'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='card_verification'
    )
    card_image = models.ImageField(upload_to='student_cards/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_cards'
    )
    rejection_reason = models.TextField(blank=True)

    def __str__(self):
        return f"Carte de {self.user} — {self.status}"


class Dispute(models.Model):
    """Litige entre consommateur et prestataire."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Ouvert'
        IN_REVIEW = 'in_review', 'En révision'
        RESOLVED = 'resolved', 'Résolu'
        CLOSED = 'closed', 'Fermé'

    class Resolution(models.TextChoices):
        REFUND = 'refund', 'Remboursement'
        COMPLETED = 'completed', 'Prestation validée'
        PARTIAL = 'partial', 'Résolution partielle'
        DISMISSED = 'dismissed', 'Rejet'

    order_id = models.IntegerField(null=True, blank=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disputes_opened'
    )
    description = models.TextField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    resolution = models.CharField(
        max_length=15, choices=Resolution.choices, null=True, blank=True
    )
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='disputes_resolved'
    )

    def __str__(self):
        return f"Litige #{self.id} — Commande #{self.order_id} ({self.status})"


class FlaggedContent(models.Model):
    """Contenu signalé (annonce ou avis)."""

    class ContentType(models.TextChoices):
        SERVICE = 'service', 'Annonce de service'
        REVIEW = 'review', 'Avis'

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        REMOVED = 'removed', 'Supprimé'
        DISMISSED = 'dismissed', 'Rejeté'

    content_type = models.CharField(max_length=10, choices=ContentType.choices)
    object_id = models.PositiveIntegerField()
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='flags_made'
    )
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='flags_reviewed'
    )

    def __str__(self):
        return f"Signalement {self.content_type} #{self.object_id}"
