# addons/models.py
# Nouveaux modèles ADDITIFS — ne modifient aucun modèle existant.
# Ils se rattachent à marketplace.Demande (la "commande") par clé étrangère.

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from marketplace.models import Demande


class Paiement(models.Model):
    """
    Paiement (simulé) d'une commande/Demande.
    Une commande possède au plus un paiement actif.
    Le téléchargement du livrable est conditionné à statut == PAID.
    """

    class Statut(models.TextChoices):
        PENDING = "pending", "En attente"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"
        REFUNDED = "refunded", "Remboursé"

    class Methode(models.TextChoices):
        CARD = "card", "Carte bancaire"
        WALLET = "wallet", "Portefeuille StudiServ"

    demande = models.OneToOneField(
        Demande, on_delete=models.CASCADE, related_name="paiement"
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=8, default="TND")
    methode = models.CharField(
        max_length=12, choices=Methode.choices, default=Methode.CARD
    )
    statut = models.CharField(
        max_length=12, choices=Statut.choices, default=Statut.PENDING
    )
    # Données de transaction (jamais le numéro complet de carte)
    transaction_ref = models.CharField(max_length=40, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    echec_raison = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement #{self.pk} – commande {self.demande_id} – {self.statut}"

    @property
    def is_paid(self):
        return self.statut == self.Statut.PAID

    def mark_paid(self, last4="", brand="", ref=""):
        self.statut = self.Statut.PAID
        self.paid_at = timezone.now()
        self.card_last4 = last4
        self.card_brand = brand
        self.transaction_ref = ref
        self.save(update_fields=[
            "statut", "paid_at", "card_last4", "card_brand", "transaction_ref"
        ])
        # Quand c'est payé, la commande passe "en cours"
        if self.demande.statut == "pending":
            self.demande.statut = "in_progress"
            self.demande.save(update_fields=["statut"])

    @property
    def deadline(self):
        """
        Date limite de livraison = date de paiement + délai du service (en jours).
        Calculée à la volée — aucune modification du modèle Demande nécessaire.
        """
        service = self.demande.service
        if not self.paid_at or not service:
            return None
        return self.paid_at + timedelta(days=service.delai_livraison)


def livrable_upload_path(instance, filename):
    return f"livrables/commande_{instance.demande_id}/{filename}"


class Livrable(models.Model):
    """
    Fichier livrable (ZIP) déposé par le prestataire pour une commande.
    Le consommateur ne peut le télécharger que si la commande est payée.
    """
    demande = models.ForeignKey(
        Demande, on_delete=models.CASCADE, related_name="livrables"
    )
    fichier = models.FileField(upload_to=livrable_upload_path)
    nom_original = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=500, blank=True)
    taille_octets = models.PositiveBigIntegerField(default=0)
    depose_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="livrables_deposes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Livrable"
        verbose_name_plural = "Livrables"

    def __str__(self):
        return f"Livrable #{self.pk} – commande {self.demande_id}"
