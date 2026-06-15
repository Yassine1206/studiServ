# addons/admin.py
from django.contrib import admin

from .models import Paiement, Livrable


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("id", "demande", "montant", "devise", "statut", "card_brand", "paid_at")
    list_filter = ("statut", "methode", "card_brand")
    search_fields = ("transaction_ref", "demande__id")
    readonly_fields = ("created_at", "paid_at")


@admin.register(Livrable)
class LivrableAdmin(admin.ModelAdmin):
    list_display = ("id", "demande", "nom_original", "taille_octets", "depose_par", "created_at")
    search_fields = ("nom_original", "demande__id")
    readonly_fields = ("created_at",)
