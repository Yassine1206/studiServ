from django.contrib import admin

from .models import (
    Competence,
    Compte,
    Consommateur,
    Demande,
    Discussion,
    Prestataire,
    Profil,
    Recommendation,
    Service,
    Utilisateur,
)


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    # ✅ email est maintenant sur user, pas sur Compte directement
    list_display  = ("get_email", "etat", "date_creation")
    search_fields = ("user__email",)
    list_filter   = ("etat",)

    @admin.display(description="Email")
    def get_email(self, obj):
        return obj.user.email


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display  = ("prenom", "nom", "role", "compte")
    search_fields = ("nom", "prenom", "compte__user__email")
    list_filter   = ("role",)


@admin.register(Consommateur)
class ConsommateurAdmin(admin.ModelAdmin):
    list_display  = ("utilisateur", "categorie_preferee")
    search_fields = ("utilisateur__nom", "utilisateur__prenom")


@admin.register(Prestataire)
class PrestataireAdmin(admin.ModelAdmin):
    list_display   = ("utilisateur", "carte_verifiee", "revenue")
    search_fields  = ("utilisateur__nom", "utilisateur__prenom")
    list_filter    = ("carte_verifiee",)
    filter_horizontal = ("competences",)


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display  = ("utilisateur", "note_moyenne", "score_reputation", "nb_commandes_total")
    search_fields = ("utilisateur__nom", "utilisateur__prenom")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ("titre", "prestataire", "categorie", "prix", "actif")
    search_fields = ("titre", "description", "categorie")
    list_filter   = ("categorie", "actif")


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display  = ("titre", "consommateur", "service", "statut", "date_creation")
    search_fields = ("titre", "description")
    list_filter   = ("statut",)


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display      = ("sujet", "service", "date_creation")
    search_fields     = ("sujet", "message")
    filter_horizontal = ("utilisateurs",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display  = ("service", "consommateur", "score", "date_creation")
    search_fields = ("commentaire", "service__titre")


admin.site.register(Competence)