from django.db import models
from django.conf import settings
from django.urls import reverse


class RoleUser(models.TextChoices):
    ADMIN = "ADMIN", "Administrateur"
    CONSOMMATEUR = "CONSOMMATEUR", "Consommateur"
    PRESTATAIRE = "PRESTATAIRE", "Prestataire"


class EtatCompte(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    SUSPENDU = "SUSPENDU", "Suspendu"
    EN_ATTENTE = "EN_ATTENTE", "En attente"


class Compte(models.Model):
    """
    Lié 1-à-1 au User Django (qui gère le mot de passe de manière sécurisée).
    Ne stocke PAS le mot de passe en clair.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="compte",
    )
    date_creation = models.DateField(auto_now_add=True)
    etat = models.CharField(
        max_length=20,
        choices=EtatCompte.choices,
        default=EtatCompte.EN_ATTENTE,
    )

    class Meta:
        ordering = ["user__email"]

    def __str__(self):
        return self.user.email

    def get_absolute_url(self):
        return reverse("marketplace:compte_detail", args=[self.pk])


class Utilisateur(models.Model):
    compte = models.OneToOneField(
        Compte,
        on_delete=models.CASCADE,
        related_name="utilisateur",
    )
    # ✅ Correction : suppression du champ `nom` dupliqué
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=RoleUser.choices)

    class Meta:
        ordering = ["nom", "prenom"]
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def get_absolute_url(self):
        return reverse("marketplace:utilisateur_detail", args=[self.pk])


class Consommateur(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="consommateur"
    )
    categorie_preferee = models.CharField(max_length=100, blank=True)
    historique_recherche = models.TextField(
        blank=True, help_text="Une recherche par ligne."
    )

    class Meta:
        ordering = ["utilisateur__nom", "utilisateur__prenom"]

    def __str__(self):
        return str(self.utilisateur)

    def get_absolute_url(self):
        return reverse("marketplace:consommateur_detail", args=[self.pk])


class Competence(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("marketplace:competence_detail", args=[self.pk])


class Prestataire(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="prestataire"
    )
    # ✅ Remplacé CharField par FileField pour stocker le vrai fichier
    carte_etudiant = models.FileField(
        upload_to="cartes_etudiants/", blank=True, null=True
    )
    carte_verifiee = models.BooleanField(default=False)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    competences = models.ManyToManyField(
        Competence, blank=True, related_name="prestataires"
    )

    class Meta:
        ordering = ["utilisateur__nom", "utilisateur__prenom"]

    def __str__(self):
        return str(self.utilisateur)

    def get_absolute_url(self):
        return reverse("marketplace:prestataire_detail", args=[self.pk])


class Profil(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil"
    )
    photo = models.ImageField(upload_to="avatars/", blank=True, null=True)
    biographie = models.TextField(blank=True)
    note_moyenne = models.FloatField(default=0)
    score_reputation = models.FloatField(default=0)
    nb_commandes_total = models.PositiveIntegerField(default=0)
    universite = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["utilisateur__nom", "utilisateur__prenom"]

    def __str__(self):
        return f"Profil de {self.utilisateur}"

    def get_absolute_url(self):
        return reverse("marketplace:profil_detail", args=[self.pk])


class Service(models.Model):
    prestataire = models.ForeignKey(
        Prestataire, on_delete=models.CASCADE, related_name="services"
    )
    titre = models.CharField(max_length=150)
    description = models.TextField()
    categorie = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    delai_livraison = models.PositiveIntegerField(help_text="Délai en jours.")
    avis = models.TextField(blank=True)
    penalite = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paiement = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["titre"]

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse("marketplace:service_detail", args=[self.pk])


class Demande(models.Model):
    consommateur = models.ForeignKey(
        Consommateur, on_delete=models.CASCADE, related_name="demandes"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes",
    )
    titre = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    STATUT_CHOICES = [
        ("pending", "En attente"),
        ("in_progress", "En cours"),
        ("completed", "Terminée"),
        ("cancelled", "Annulée"),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="pending")

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse("marketplace:demande_detail", args=[self.pk])


class Discussion(models.Model):
    utilisateurs = models.ManyToManyField(Utilisateur, related_name="discussions")
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="discussions",
    )
    sujet = models.CharField(max_length=150)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.sujet

    def get_absolute_url(self):
        return reverse("marketplace:discussion_detail", args=[self.pk])


class Recommendation(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="recommendations"
    )
    consommateur = models.ForeignKey(
        Consommateur, on_delete=models.CASCADE, related_name="recommendations"
    )
    commentaire = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(default=5)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Recommendation {self.score}/5 - {self.service}"

    def get_absolute_url(self):
        return reverse("marketplace:recommendation_detail", args=[self.pk])
    from django.db.models import Avg, Count


class ReputationScore(models.Model):
    """
    Score de réputation dynamique d'un prestataire.
    Recalculé automatiquement après chaque nouvelle évaluation.
    Score = (note_moyenne * 0.7) + (taux_complétion * 0.3) * 5
    """
    prestataire = models.OneToOneField(
        Prestataire,
        on_delete=models.CASCADE,
        related_name='reputation'
    )
    note_moyenne        = models.FloatField(default=0.0)
    taux_completion     = models.FloatField(default=0.0)   # % commandes terminées
    score_global        = models.FloatField(default=0.0)   # score final sur 5
    nb_avis             = models.PositiveIntegerField(default=0)
    nb_commandes_total  = models.PositiveIntegerField(default=0)
    badge_confiance     = models.BooleanField(default=False)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score_global']

    def __str__(self):
        return f"Réputation {self.prestataire} — {self.score_global:.1f}/5"

    @classmethod
    def update_score(cls, prestataire):
        """
        Recalcule et sauvegarde le score de réputation d'un prestataire.
        Appelé automatiquement après chaque évaluation.
        """
        # Récupérer tous les avis du prestataire
        avis = Recommendation.objects.filter(service__prestataire=prestataire)
        nb_avis = avis.count()

        if nb_avis == 0:
            note_moyenne = 0.0
        else:
            note_moyenne = round(
                avis.aggregate(avg=Avg('score'))['avg'] or 0.0, 2
            )

        # Calculer le taux de complétion des demandes/commandes
        total_demandes = Demande.objects.filter(
            service__prestataire=prestataire
        ).count()
        demandes_terminees = Demande.objects.filter(
            service__prestataire=prestataire,
            statut='completed'
        ).count()

        if total_demandes > 0:
            taux_completion = round(demandes_terminees / total_demandes, 2)
        else:
            taux_completion = 0.0

        # Formule : 70% note moyenne + 30% taux complétion
        score_global = round(
            (note_moyenne * 0.7) + (taux_completion * 5 * 0.3), 2
        )

        # Badge de confiance : note >= 4.5 ET au moins 10 avis
        badge_confiance = (note_moyenne >= 4.5 and nb_avis >= 10)

        # Créer ou mettre à jour
        rep, _ = cls.objects.update_or_create(
            prestataire=prestataire,
            defaults={
                'note_moyenne':       note_moyenne,
                'taux_completion':    taux_completion,
                'score_global':       score_global,
                'nb_avis':            nb_avis,
                'nb_commandes_total': total_demandes,
                'badge_confiance':    badge_confiance,
            }
        )

        # Mettre à jour aussi le Profil (note_moyenne et score_reputation)
        try:
            profil = prestataire.utilisateur.profil
            profil.note_moyenne     = note_moyenne
            profil.score_reputation = score_global
            profil.nb_commandes_total = total_demandes
            profil.save(update_fields=[
                'note_moyenne', 'score_reputation', 'nb_commandes_total'
            ])
        except Exception:
            pass

        # Alerte si chute brutale (score < 2.0 et avait un bon score avant)
        if score_global < 2.0 and nb_avis >= 3:
            rep._trigger_alert()

        return rep

    def _trigger_alert(self):
        """Alerte interne en cas de chute brutale de réputation."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"ALERTE RÉPUTATION : {self.prestataire} — score {self.score_global}/5"
        )

    
