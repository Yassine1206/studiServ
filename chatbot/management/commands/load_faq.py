# chatbot/management/commands/load_faq.py
# Commande : python manage.py load_faq

from django.core.management.base import BaseCommand
from chatbot.models import FAQDocument

INITIAL_FAQ = [
    {
        'title': "Inscription sur StudiServ",
        'question': "Comment créer un compte sur StudiServ ?",
        'answer': (
            "Pour créer un compte, clique sur 'S'inscrire' en haut à droite. "
            "Tu dois fournir ton email universitaire, ton prénom, nom et un mot de passe sécurisé. "
            "Un email de confirmation sera envoyé à ton adresse universitaire. "
            "Clique sur le lien de confirmation pour activer ton compte."
        ),
        'category': 'account',
        'tags': 'inscription,compte,email,universitaire',
    },
    {
        'title': "Vérification carte étudiante",
        'question': "Pourquoi dois-je uploader ma carte étudiante pour devenir prestataire ?",
        'answer': (
            "StudiServ est une marketplace réservée aux étudiants. "
            "La vérification de la carte étudiante garantit que seuls les vrais étudiants "
            "peuvent proposer des services. "
            "Ta carte est examinée par notre équipe dans un délai de 24 à 48h. "
            "Tu recevras une notification dès que ton statut sera validé."
        ),
        'category': 'account',
        'tags': 'carte étudiante,vérification,prestataire,validation',
    },
    {
        'title': "Réinitialisation mot de passe",
        'question': "J'ai oublié mon mot de passe, comment le réinitialiser ?",
        'answer': (
            "Clique sur 'Mot de passe oublié' sur la page de connexion. "
            "Entre ton email universitaire et un lien de réinitialisation te sera envoyé. "
            "Ce lien est valide pendant 1 heure. "
            "Si tu ne reçois pas l'email, vérifie ton dossier spam."
        ),
        'category': 'account',
        'tags': 'mot de passe,oublié,réinitialisation',
    },
    {
        'title': "Blocage après tentatives échouées",
        'question': "Mon compte est bloqué après plusieurs tentatives de connexion, que faire ?",
        'answer': (
            "Pour des raisons de sécurité, ton compte est temporairement bloqué après 5 tentatives "
            "de connexion échouées consécutives. "
            "Attends 15 minutes avant de réessayer, ou utilise 'Mot de passe oublié' "
            "pour réinitialiser ton mot de passe immédiatement."
        ),
        'category': 'account',
        'tags': 'blocage,tentatives,connexion,sécurité',
    },
    {
        'title': "Créer une annonce de service",
        'question': "Comment publier une annonce de service sur StudiServ ?",
        'answer': (
            "Pour publier une annonce : "
            "1. Connecte-toi et assure-toi que ton statut de prestataire est validé. "
            "2. Clique sur 'Publier un service' dans ton tableau de bord. "
            "3. Remplis le titre, la description, la catégorie, le prix et le délai de livraison. "
            "4. Ajoute des images pour rendre ton annonce plus attractive. "
            "5. Clique sur 'Publier'."
        ),
        'category': 'services',
        'tags': 'annonce,service,publier,prestataire',
    },
    {
        'title': "Catégories de services disponibles",
        'question': "Quels types de services puis-je proposer sur StudiServ ?",
        'answer': (
            "StudiServ accepte de nombreuses catégories : "
            "cours particuliers, graphisme et design, traduction, "
            "rédaction et correction, développement web et mobile, "
            "montage vidéo et photo, et bien d'autres compétences étudiantes."
        ),
        'category': 'services',
        'tags': 'catégories,types,services,compétences',
    },
    {
        'title': "Modifier ou supprimer une annonce",
        'question': "Comment modifier ou supprimer mon annonce ?",
        'answer': (
            "Va dans ton tableau de bord, section 'Mes services'. "
            "Clique sur l'annonce puis sur 'Modifier' pour changer les informations. "
            "Pour supprimer, clique sur 'Supprimer'. "
            "Note : tu ne peux pas supprimer une annonce avec des commandes en cours."
        ),
        'category': 'services',
        'tags': 'modifier,supprimer,annonce,éditer',
    },
    {
        'title': "Recherche et filtres",
        'question': "Comment trouver un service sur StudiServ ?",
        'answer': (
            "Utilise la barre de recherche en haut de la page pour chercher par mots-clés. "
            "Affine avec les filtres : catégorie, fourchette de prix, note minimale. "
            "Les résultats sont triés par pertinence et score de réputation. "
            "Tu peux aussi parcourir les sections 'Services populaires' sur la page d'accueil."
        ),
        'category': 'services',
        'tags': 'recherche,filtres,trouver,service',
    },
    {
        'title': "Passer une commande",
        'question': "Comment passer une commande pour un service ?",
        'answer': (
            "Clique sur le service qui t'intéresse et examine les détails. "
            "Clique sur 'Commander' et confirme avec le paiement simulé. "
            "Le prestataire est notifié et la commande passe à l'état 'En attente'."
        ),
        'category': 'orders',
        'tags': 'commander,commande,achat,service',
    },
    {
        'title': "Paiement simulé",
        'question': "Comment fonctionne le paiement sur StudiServ ?",
        'answer': (
            "StudiServ utilise un système de paiement simulé à des fins académiques. "
            "Aucun vrai argent n'est transféré. Tu entres les informations d'une carte fictive "
            "pour simuler l'expérience d'une vraie marketplace."
        ),
        'category': 'orders',
        'tags': 'paiement,simulé,carte,fictif',
    },
    {
        'title': "Suivi de commande",
        'question': "Comment suivre l'état de ma commande ?",
        'answer': (
            "Va dans 'Mes commandes' dans ton tableau de bord. "
            "Chaque commande a un statut : En attente, En cours, Livré, ou Terminé. "
            "Tu peux communiquer avec le prestataire via la messagerie intégrée."
        ),
        'category': 'orders',
        'tags': 'suivi,état,commande,statut',
    },
    {
        'title': "Annuler une commande",
        'question': "Puis-je annuler une commande ?",
        'answer': (
            "Oui, tu peux annuler une commande uniquement si son statut est 'En attente'. "
            "Une fois la commande 'En cours', l'annulation n'est plus possible directement. "
            "Si tu as un problème, contacte le prestataire via la messagerie ou ouvre un litige."
        ),
        'category': 'orders',
        'tags': 'annulation,annuler,commande',
    },
    {
        'title': "Messagerie interne",
        'question': "Comment contacter un prestataire ou un consommateur ?",
        'answer': (
            "StudiServ dispose d'une messagerie interne temps réel. "
            "Depuis la page d'un service, clique sur 'Contacter le prestataire'. "
            "Tu peux envoyer des messages texte et des fichiers (PDF, images jusqu'à 10 MB). "
            "Tu reçois une notification pour chaque nouveau message."
        ),
        'category': 'messaging',
        'tags': 'messagerie,chat,contacter,message',
    },
    {
        'title': "Laisser un avis",
        'question': "Comment laisser un avis après une prestation ?",
        'answer': (
            "Après qu'une commande est marquée 'Terminée', tu as 14 jours pour laisser un avis. "
            "Va dans 'Mes commandes', clique sur la commande terminée, puis sur 'Laisser un avis'. "
            "Donne une note de 1 à 5 étoiles et écris un commentaire."
        ),
        'category': 'reputation',
        'tags': 'avis,note,étoiles,évaluation',
    },
    {
        'title': "Badge de confiance",
        'question': "Qu'est-ce que le badge de confiance StudiServ ?",
        'answer': (
            "Le badge de confiance est attribué aux prestataires ayant : "
            "une note moyenne d'au moins 4.5 étoiles et au moins 10 commandes complétées. "
            "Ce badge apparaît sur leur profil et les propulse en haut des résultats de recherche."
        ),
        'category': 'reputation',
        'tags': 'badge,confiance,réputation,prestataire',
    },
    {
        'title': "Contact support StudiServ",
        'question': "Comment contacter le support StudiServ ?",
        'answer': (
            "Tu peux contacter l'équipe StudiServ par email à support@studiserv.tn. "
            "Pour les problèmes urgents, utilise le formulaire de contact dans ton tableau de bord. "
            "Notre équipe répond généralement dans les 24h en jours ouvrés."
        ),
        'category': 'general',
        'tags': 'support,contact,aide,problème',
    },
]


class Command(BaseCommand):
    help = 'Charge les FAQ initiales de StudiServ et indexe dans ChromaDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reindex-only',
            action='store_true',
            help='Réindexer uniquement sans charger les FAQ'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer toutes les FAQ existantes avant de charger'
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = FAQDocument.objects.count()
            FAQDocument.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'{count} FAQ supprimées.'))

        if not options['reindex_only']:
            created_count = 0
            for faq_data in INITIAL_FAQ:
                obj, created = FAQDocument.objects.get_or_create(
                    title=faq_data['title'],
                    defaults=faq_data
                )
                if created:
                    created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'{created_count} nouvelles FAQ chargées.')
            )

        # Indexation dans ChromaDB
        self.stdout.write('Indexation dans ChromaDB...')
        try:
            from chatbot.rag_engine import index_faq_documents
            count = index_faq_documents()
            self.stdout.write(
                self.style.SUCCESS(f'✓ {count} documents indexés dans ChromaDB.')
            )
        except ImportError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'Dépendances RAG manquantes : {e}\n'
                    'Les FAQ sont chargées en base mais pas encore indexées.\n'
                    'Installe : pip install langchain langchain-community chromadb sentence-transformers'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'ChromaDB non disponible : {e}\nLes FAQ sont quand même en base.'))