# addons/management/commands/seed_demo.py
"""
Seed la base de données avec des comptes et données de démo.

Usage:
    python manage.py seed_demo            # crée le jeu de démo
    python manage.py seed_demo --reset    # supprime d'abord les comptes demo

Comptes créés (mot de passe : demo1234 pour tous) :
    admin@studiserv.tn        — administrateur (is_staff=True)

    sarra.benali@esprit.tn    — prestataire vérifié (design)
    amine.hammami@enit.tn     — prestataire vérifié (dev web)
    leila.mansouri@isg.tn     — prestataire vérifié (cours)

    rayen.khelifi@enit.tn     — consommateur
    nadia.trabelsi@esprit.tn  — consommateur
    youssef.gharbi@isg.tn     — consommateur
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from marketplace.models import (
    Compte, Utilisateur, Consommateur, Prestataire, Profil,
    Service, Demande, Recommendation, RoleUser, EtatCompte,
)

PASSWORD = "demo1234"

ADMIN = {"email": "admin@studiserv.tn", "nom": "Admin", "prenom": "Studi"}

PRESTATAIRES = [
    {
        "email": "sarra.benali@esprit.tn", "nom": "Benali", "prenom": "Sarra",
        "universite": "ESPRIT",
        "biographie": "Étudiante en design graphique. Spécialisée en identité visuelle.",
        "services": [
            {"titre": "Création de logo professionnel", "categorie": "Design",
             "prix": 80, "delai_livraison": 3,
             "description": "Logo unique, plusieurs propositions, fichiers vectoriels inclus."},
            {"titre": "Affiche universitaire (A3/A4)", "categorie": "Design",
             "prix": 35, "delai_livraison": 2,
             "description": "Affiche pour événement étudiant, club ou association."},
        ],
    },
    {
        "email": "amine.hammami@enit.tn", "nom": "Hammami", "prenom": "Amine",
        "universite": "ENIT",
        "biographie": "Étudiant en ingénierie informatique. Full-stack React/Django.",
        "services": [
            {"titre": "Site vitrine React + Django", "categorie": "Développement web",
             "prix": 250, "delai_livraison": 10,
             "description": "Site web responsive, formulaire de contact, dashboard admin."},
            {"titre": "API REST Django", "categorie": "Développement web",
             "prix": 180, "delai_livraison": 7,
             "description": "API documentée avec JWT, tests inclus."},
        ],
    },
    {
        "email": "leila.mansouri@isg.tn", "nom": "Mansouri", "prenom": "Leïla",
        "universite": "ISG Tunis",
        "biographie": "Étudiante en master maths. Donne des cours particuliers depuis 3 ans.",
        "services": [
            {"titre": "Cours particulier maths L1", "categorie": "Cours particuliers",
             "prix": 40, "delai_livraison": 1,
             "description": "Algèbre, analyse, séances d'1h30 en ligne ou présentiel."},
            {"titre": "Aide rédaction CV étudiant", "categorie": "Rédaction",
             "prix": 25, "delai_livraison": 2,
             "description": "CV propre et adapté au profil étudiant tunisien."},
        ],
    },
]

CONSOMMATEURS = [
    {"email": "rayen.khelifi@enit.tn", "nom": "Khelifi", "prenom": "Rayen",
     "universite": "ENIT", "categorie_preferee": "Développement web"},
    {"email": "nadia.trabelsi@esprit.tn", "nom": "Trabelsi", "prenom": "Nadia",
     "universite": "ESPRIT", "categorie_preferee": "Design"},
    {"email": "youssef.gharbi@isg.tn", "nom": "Gharbi", "prenom": "Youssef",
     "universite": "ISG Tunis", "categorie_preferee": "Cours particuliers"},
]


class Command(BaseCommand):
    help = "Crée un jeu de données de démo (admin + prestataires + consommateurs + services + commandes + avis)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Supprime d'abord les comptes demo avant de re-seeder.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self._reset()

        self._create_admin()
        prestataires = [self._create_prestataire(p) for p in PRESTATAIRES]
        consommateurs = [self._create_consommateur(c) for c in CONSOMMATEURS]
        self._create_demandes_and_reviews(prestataires, consommateurs)

        self.stdout.write(self.style.SUCCESS("\nSeed terminé."))
        self.stdout.write("\nComptes (mot de passe : demo1234) :")
        self.stdout.write(f"  Admin         {ADMIN['email']}")
        for p in PRESTATAIRES:
            self.stdout.write(f"  Prestataire   {p['email']}")
        for c in CONSOMMATEURS:
            self.stdout.write(f"  Consommateur  {c['email']}")

    def _reset(self):
        emails = [ADMIN["email"]] + [p["email"] for p in PRESTATAIRES] + [c["email"] for c in CONSOMMATEURS]
        n = User.objects.filter(email__in=emails).count()
        User.objects.filter(email__in=emails).delete()
        self.stdout.write(self.style.WARNING(f"{n} comptes demo supprimés."))

    def _create_admin(self):
        user, created = User.objects.get_or_create(
            username=ADMIN["email"],
            defaults={"email": ADMIN["email"], "first_name": ADMIN["prenom"],
                      "last_name": ADMIN["nom"], "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        compte, _ = Compte.objects.get_or_create(user=user, defaults={"etat": EtatCompte.ACTIF})
        utilisateur, _ = Utilisateur.objects.get_or_create(
            compte=compte,
            defaults={"nom": ADMIN["nom"], "prenom": ADMIN["prenom"], "role": RoleUser.ADMIN},
        )
        Profil.objects.get_or_create(utilisateur=utilisateur)
        self.stdout.write(f"Admin: {ADMIN['email']}")
        return user

    def _create_prestataire(self, data):
        user, created = User.objects.get_or_create(
            username=data["email"],
            defaults={"email": data["email"], "first_name": data["prenom"],
                      "last_name": data["nom"]},
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        compte, _ = Compte.objects.get_or_create(user=user, defaults={"etat": EtatCompte.ACTIF})
        compte.etat = EtatCompte.ACTIF
        compte.save(update_fields=["etat"])

        utilisateur, _ = Utilisateur.objects.get_or_create(
            compte=compte,
            defaults={"nom": data["nom"], "prenom": data["prenom"], "role": RoleUser.PRESTATAIRE},
        )
        Profil.objects.update_or_create(
            utilisateur=utilisateur,
            defaults={"biographie": data["biographie"], "universite": data["universite"]},
        )
        prestataire, _ = Prestataire.objects.get_or_create(
            utilisateur=utilisateur, defaults={"carte_verifiee": True},
        )
        prestataire.carte_verifiee = True
        prestataire.save(update_fields=["carte_verifiee"])

        for svc in data["services"]:
            Service.objects.get_or_create(
                prestataire=prestataire, titre=svc["titre"],
                defaults={
                    "description": svc["description"], "categorie": svc["categorie"],
                    "prix": svc["prix"], "delai_livraison": svc["delai_livraison"],
                    "actif": True,
                },
            )
        self.stdout.write(f"Prestataire: {data['email']}  ({len(data['services'])} services)")
        return prestataire

    def _create_consommateur(self, data):
        user, created = User.objects.get_or_create(
            username=data["email"],
            defaults={"email": data["email"], "first_name": data["prenom"],
                      "last_name": data["nom"]},
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        compte, _ = Compte.objects.get_or_create(user=user, defaults={"etat": EtatCompte.ACTIF})
        utilisateur, _ = Utilisateur.objects.get_or_create(
            compte=compte,
            defaults={"nom": data["nom"], "prenom": data["prenom"], "role": RoleUser.CONSOMMATEUR},
        )
        Profil.objects.update_or_create(
            utilisateur=utilisateur, defaults={"universite": data["universite"]},
        )
        consommateur, _ = Consommateur.objects.get_or_create(
            utilisateur=utilisateur,
            defaults={"categorie_preferee": data["categorie_preferee"]},
        )
        self.stdout.write(f"Consommateur: {data['email']}")
        return consommateur

    def _create_demandes_and_reviews(self, prestataires, consommateurs):
        sarra, amine, leila = prestataires
        rayen, nadia, youssef = consommateurs

        scenarios = [
            (rayen,  amine.services.filter(titre__icontains="API").first(),
             "completed", 5, "Code propre, documentation impeccable. Je recommande !"),
            (rayen,  sarra.services.filter(titre__icontains="logo").first(),
             "completed", 4, "Très bon logo, livré en 2 jours seulement."),
            (nadia,  sarra.services.filter(titre__icontains="Affiche").first(),
             "in_progress", None, None),
            (nadia,  amine.services.filter(titre__icontains="Site").first(),
             "completed", 5, "Site magnifique, livraison rapide. Top !"),
            (youssef, leila.services.filter(titre__icontains="maths").first(),
             "in_progress", None, None),
            (youssef, leila.services.filter(titre__icontains="CV").first(),
             "pending", None, None),
            (rayen,  leila.services.filter(titre__icontains="maths").first(),
             "completed", 5, "Leïla est patiente et claire. Mon niveau a explosé."),
        ]

        created = 0
        for cons, service, statut, note, commentaire in scenarios:
            if not service:
                continue
            demande, was_created = Demande.objects.get_or_create(
                consommateur=cons, service=service, titre=f"Commande — {service.titre}",
                defaults={"description": "Commande de démo.", "statut": statut},
            )
            if was_created:
                created += 1
            else:
                demande.statut = statut
                demande.save(update_fields=["statut"])

            if statut == "completed" and note is not None:
                Recommendation.objects.get_or_create(
                    service=service, consommateur=cons,
                    defaults={"score": note, "commentaire": commentaire},
                )
        self.stdout.write(f"{created} commandes + {sum(1 for s in scenarios if s[3])} avis créés.")
