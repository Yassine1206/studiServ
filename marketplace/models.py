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
    
