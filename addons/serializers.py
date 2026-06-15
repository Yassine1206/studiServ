# addons/serializers.py
from rest_framework import serializers

from .models import Paiement, Livrable


class PaiementSerializer(serializers.ModelSerializer):
    is_paid = serializers.BooleanField(read_only=True)
    deadline = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Paiement
        fields = [
            "id", "demande", "montant", "devise", "methode", "statut",
            "transaction_ref", "card_last4", "card_brand",
            "is_paid", "deadline", "created_at", "paid_at",
        ]
        read_only_fields = fields


class LivrableSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Livrable
        fields = [
            "id", "demande", "nom_original", "description",
            "taille_octets", "created_at", "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        # URL gardée par permission — pointe vers l'endpoint protégé, pas vers MEDIA.
        return f"/api/orders/{obj.demande_id}/deliverables/{obj.id}/download/"


class OrderTrackingSerializer(serializers.Serializer):
    """
    Vue de suivi destinée au consommateur.
    Statut, paiement, deadline et disponibilité du livrable.
    """
    id = serializers.IntegerField()
    titre = serializers.CharField()
    statut = serializers.CharField()
    statut_label = serializers.SerializerMethodField()
    date_creation = serializers.DateTimeField()
    service_titre = serializers.SerializerMethodField()
    provider_ref = serializers.SerializerMethodField()
    is_paid = serializers.SerializerMethodField()
    montant = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()
    deliverable_available = serializers.SerializerMethodField()

    STATUT_LABELS = {
        "pending": "En attente de paiement",
        "in_progress": "En cours",
        "completed": "Terminée",
        "cancelled": "Annulée",
    }

    def get_statut_label(self, obj):
        return self.STATUT_LABELS.get(obj.statut, obj.statut)

    def get_service_titre(self, obj):
        return obj.service.titre if obj.service else obj.titre

    def get_provider_ref(self, obj):
        # Anonyme : on n'expose qu'un identifiant, jamais le nom.
        if obj.service and obj.service.prestataire_id:
            return f"Prestataire #{obj.service.prestataire_id}"
        return None

    def _paiement(self, obj):
        return getattr(obj, "paiement", None)

    def get_is_paid(self, obj):
        p = self._paiement(obj)
        return bool(p and p.is_paid)

    def get_montant(self, obj):
        p = self._paiement(obj)
        if p:
            return float(p.montant)
        return float(obj.service.prix) if obj.service else None

    def get_deadline(self, obj):
        p = self._paiement(obj)
        return p.deadline if p else None

    def get_deliverable_available(self, obj):
        p = self._paiement(obj)
        return bool(p and p.is_paid and obj.livrables.exists())
