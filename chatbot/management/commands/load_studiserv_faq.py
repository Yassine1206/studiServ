# chatbot/management/commands/load_studiserv_faq.py
# Commande : python manage.py load_studiserv_faq
# Charge la base de connaissances complète de StudiServ (extrait du PDF officiel)
# et indexe dans ChromaDB pour le chatbot RAG.

from django.core.management.base import BaseCommand
from chatbot.models import FAQDocument

STUDISERV_KNOWLEDGE_BASE = [
    # ═══════════════════════════════════════════════════════════════════════
    # PRÉSENTATION GÉNÉRALE
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Qu'est-ce que StudiServ",
        'question': "C'est quoi StudiServ ? Présente-moi la plateforme.",
        'answer': (
            "StudiServ est une plateforme web de type marketplace dédiée exclusivement à la communauté étudiante. "
            "Elle permet aux étudiants universitaires de proposer leurs compétences sous forme de services payants "
            "et d'accéder aux services proposés par leurs pairs, dans un environnement sécurisé, tracé et basé sur la confiance. "
            "La plateforme a été développée par Eya Boiguerra, Amine Hasnaoui et Rayen Hammi, encadrés par Slim Abbes (SESAME)."
        ),
        'category': 'general',
        'tags': 'présentation,définition,studiServ,marketplace,étudiants',
    },
    {
        'title': "Objectif de StudiServ",
        'question': "Pourquoi StudiServ a-t-il été créé ? Quel problème résout-il ?",
        'answer': (
            "StudiServ répond à un manque identifié : les étudiants disposent de compétences variées "
            "(cours particuliers, graphisme, développement web, traduction, montage vidéo, rédaction, etc.) "
            "mais il n'existait aucune plateforme centralisée et adaptée à leurs besoins. "
            "Avant StudiServ, ils passaient par les réseaux sociaux ou le bouche-à-oreille, "
            "sans garantie de qualité ni traçabilité. La plateforme apporte visibilité, garantie de qualité, "
            "traçabilité, sécurité des transactions et communication structurée."
        ),
        'category': 'general',
        'tags': 'objectif,problème,raison,besoin',
    },
    {
        'title': "Types de services disponibles",
        'question': "Quels types de services puis-je trouver ou proposer sur StudiServ ?",
        'answer': (
            "StudiServ accepte de nombreuses catégories de services étudiants : "
            "cours particuliers (mathématiques, langues, informatique), "
            "graphisme et design (logos, affiches, identité visuelle), "
            "traduction de documents (français, anglais, arabe), "
            "rédaction et correction de textes académiques ou professionnels, "
            "développement web (front-end, back-end, full-stack), "
            "montage vidéo et création de contenu multimédia, "
            "et bien d'autres services liés aux compétences des étudiants."
        ),
        'category': 'services',
        'tags': 'catégories,types,services,compétences',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ACTEURS - PRESTATAIRE
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Rôle du prestataire",
        'question': "C'est quoi un prestataire sur StudiServ ? Que peut-il faire ?",
        'answer': (
            "Un prestataire est un étudiant vendeur sur StudiServ. Il peut : "
            "créer un compte avec son email universitaire, "
            "soumettre sa carte étudiante pour vérification et validation, "
            "publier des annonces de services avec description, prix et délai, "
            "recevoir, accepter et traiter les commandes des consommateurs, "
            "communiquer en temps réel avec les consommateurs via la messagerie, "
            "consulter ses statistiques personnelles (revenus simulés, commandes, performance), "
            "suivre son score de réputation et ses badges de confiance, "
            "et modifier ou supprimer ses annonces à tout moment."
        ),
        'category': 'account',
        'tags': 'prestataire,vendeur,rôle,droits',
    },
    {
        'title': "Devenir prestataire",
        'question': "Comment devenir prestataire sur StudiServ ?",
        'answer': (
            "Pour devenir prestataire : "
            "1. Inscris-toi avec ton email universitaire, nom, prénom et mot de passe. "
            "2. Choisis le rôle 'Prestataire' lors de l'inscription. "
            "3. Upload ta carte étudiante via ton tableau de bord. "
            "4. Attends la validation de ta carte par l'administrateur (sous 24-48h). "
            "5. Une fois validé, tu obtiens le statut 'Prestataire vérifié' et peux publier tes annonces."
        ),
        'category': 'account',
        'tags': 'devenir prestataire,inscription,validation,carte étudiante',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ACTEURS - CONSOMMATEUR
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Rôle du consommateur",
        'question': "C'est quoi un consommateur sur StudiServ ? Que peut-il faire ?",
        'answer': (
            "Un consommateur est un étudiant acheteur sur StudiServ. Il peut : "
            "créer un compte avec son email universitaire, "
            "rechercher des services par mots-clés, catégorie, prix ou note, "
            "recevoir des recommandations personnalisées basées sur son historique, "
            "consulter les profils détaillés des prestataires avec leurs avis, "
            "passer des commandes et effectuer un paiement simulé, "
            "suivre l'état de ses commandes (En attente → En cours → Livré → Terminé), "
            "communiquer directement avec le prestataire via la messagerie interne, "
            "laisser une évaluation et un commentaire après la prestation, "
            "et annuler une commande avant le début de la prestation."
        ),
        'category': 'account',
        'tags': 'consommateur,acheteur,rôle,droits,étudiant',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ACTEURS - ADMINISTRATEUR
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Rôle de l'administrateur",
        'question': "C'est quoi un administrateur sur StudiServ ? Que peut-il faire ?",
        'answer': (
            "L'administrateur est le gestionnaire de la plateforme. Il peut : "
            "accéder à un tableau de bord global avec statistiques complètes, "
            "gérer les utilisateurs (activation, désactivation, suppression de compte), "
            "vérifier et valider les cartes étudiantes soumises par les prestataires, "
            "modérer les annonces (validation ou suppression des annonces signalées), "
            "gérer les litiges entre consommateurs et prestataires, "
            "modérer les avis (suppression des avis abusifs ou frauduleux), "
            "et surveiller l'activité globale de la plateforme."
        ),
        'category': 'account',
        'tags': 'administrateur,admin,gestionnaire,modération',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M1 - AUTHENTIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Inscription sur StudiServ",
        'question': "Comment créer un compte sur StudiServ ?",
        'answer': (
            "Pour créer un compte sur StudiServ : "
            "1. Clique sur 'S'inscrire' en haut à droite. "
            "2. Renseigne ton email universitaire (obligatoire, doit être un email .edu, .ens.tn, .essai.tn, etc.). "
            "3. Entre ton nom, prénom et un mot de passe sécurisé. "
            "4. Choisis ton rôle : consommateur (acheteur) ou prestataire (vendeur). "
            "5. Si tu es prestataire, upload aussi ta carte étudiante. "
            "6. Valide le formulaire et tu reçois un email de confirmation."
        ),
        'category': 'account',
        'tags': 'inscription,créer compte,signup,enregistrement',
    },
    {
        'title': "Email universitaire obligatoire",
        'question': "Pourquoi dois-je utiliser un email universitaire pour m'inscrire ?",
        'answer': (
            "StudiServ est réservé exclusivement à la communauté étudiante. "
            "L'email utilisé pour l'inscription doit obligatoirement être un email universitaire valide "
            "afin de garantir que seuls les étudiants peuvent accéder à la plateforme. "
            "C'est une mesure de sécurité pour préserver la qualité et l'esprit de la communauté."
        ),
        'category': 'account',
        'tags': 'email,universitaire,obligatoire,règle',
    },
    {
        'title': "Connexion sécurisée",
        'question': "Comment se connecter à mon compte StudiServ ?",
        'answer': (
            "Pour te connecter : "
            "1. Va sur la page de connexion. "
            "2. Entre ton email universitaire et ton mot de passe. "
            "3. Clique sur 'Se connecter'. "
            "StudiServ utilise une authentification sécurisée par JWT (JSON Web Token) "
            "qui maintient ta session active pendant 2 heures, avec un refresh token valide 7 jours."
        ),
        'category': 'account',
        'tags': 'connexion,login,authentification,JWT',
    },
    {
        'title': "Blocage anti-brute-force",
        'question': "Mon compte est bloqué après plusieurs tentatives de connexion, que faire ?",
        'answer': (
            "Pour des raisons de sécurité, ton compte est temporairement bloqué après "
            "5 tentatives de connexion échouées consécutives. "
            "Cette mesure protège contre les attaques par force brute. "
            "Attends 15 minutes avant de réessayer, ou utilise la fonction 'Mot de passe oublié' "
            "pour réinitialiser ton mot de passe immédiatement par email."
        ),
        'category': 'account',
        'tags': 'blocage,tentatives,brute force,sécurité',
    },
    {
        'title': "Réinitialisation mot de passe",
        'question': "J'ai oublié mon mot de passe, comment le réinitialiser ?",
        'answer': (
            "Pour réinitialiser ton mot de passe : "
            "1. Clique sur 'Mot de passe oublié' sur la page de connexion. "
            "2. Entre ton email universitaire. "
            "3. Un lien de réinitialisation t'est envoyé par email. "
            "4. Clique sur le lien (valide 1 heure) et choisis un nouveau mot de passe. "
            "Si tu ne reçois pas l'email, vérifie ton dossier spam."
        ),
        'category': 'account',
        'tags': 'mot de passe,oublié,réinitialisation,email',
    },
    {
        'title': "Vérification carte étudiante",
        'question': "Pourquoi dois-je uploader ma carte étudiante ?",
        'answer': (
            "Seuls les prestataires (vendeurs) doivent uploader leur carte étudiante. "
            "Cette vérification garantit que seuls les vrais étudiants peuvent proposer des services, "
            "assurant la confiance sur la plateforme. "
            "Ta carte est examinée manuellement par l'administrateur dans un délai de 24 à 48h. "
            "Une fois validée, tu obtiens le statut 'Prestataire vérifié' et peux publier tes annonces."
        ),
        'category': 'account',
        'tags': 'carte étudiante,vérification,prestataire,validation',
    },
    {
        'title': "Gestion du profil",
        'question': "Comment modifier mon profil ?",
        'answer': (
            "Va dans 'Mon profil' depuis ton tableau de bord. Tu peux modifier : "
            "ta photo de profil, ta biographie, tes compétences, ton université, "
            "et tes informations personnelles. "
            "Les modifications sont sauvegardées immédiatement après avoir cliqué sur 'Enregistrer'."
        ),
        'category': 'account',
        'tags': 'profil,modifier,biographie,photo,compétences',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M2 - SERVICES ET ANNONCES
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Créer une annonce de service",
        'question': "Comment publier une annonce de service ?",
        'answer': (
            "Pour publier une annonce (réservé aux prestataires vérifiés) : "
            "1. Va dans ton tableau de bord prestataire. "
            "2. Clique sur 'Publier un service' ou 'Nouvelle annonce'. "
            "3. Remplis les champs obligatoires : titre, description détaillée, catégorie, prix, délai de livraison. "
            "4. Ajoute une galerie d'images pour rendre ton annonce plus attractive. "
            "5. Clique sur 'Publier'. "
            "Ton annonce est immédiatement visible par les consommateurs."
        ),
        'category': 'services',
        'tags': 'créer annonce,publier service,nouveau service',
    },
    {
        'title': "Champs obligatoires d'une annonce",
        'question': "Quels sont les champs obligatoires pour créer une annonce ?",
        'answer': (
            "Une annonce sur StudiServ doit obligatoirement comporter : "
            "un titre, une description détaillée, une catégorie, un prix et un délai de livraison. "
            "Sans ces 5 informations, l'annonce ne peut pas être publiée. "
            "Tu peux aussi ajouter des images pour la galerie afin d'illustrer ton service."
        ),
        'category': 'services',
        'tags': 'champs obligatoires,annonce,création',
    },
    {
        'title': "Modifier ou supprimer une annonce",
        'question': "Comment modifier ou supprimer mon annonce ?",
        'answer': (
            "Va dans ton tableau de bord, section 'Mes services'. "
            "Clique sur l'annonce que tu veux modifier, puis sur 'Modifier'. "
            "Tu peux changer toutes les informations. "
            "Pour supprimer une annonce, clique sur 'Supprimer'. "
            "Seul le prestataire propriétaire peut modifier ou supprimer son annonce. "
            "Note : tu ne peux pas supprimer une annonce qui a des commandes en cours."
        ),
        'category': 'services',
        'tags': 'modifier,supprimer,annonce,éditer',
    },
    {
        'title': "Rechercher un service",
        'question': "Comment rechercher un service sur StudiServ ?",
        'answer': (
            "StudiServ offre un système de recherche avancée : "
            "1. Utilise la barre de recherche en haut de la page avec des mots-clés. "
            "2. Affine avec les filtres : catégorie, fourchette de prix, note minimum, disponibilité. "
            "3. Les résultats sont triés par pertinence et par score de réputation. "
            "Tu peux aussi parcourir les sections 'Services populaires' et 'Nouveaux prestataires' "
            "sur la page d'accueil pour découvrir des services."
        ),
        'category': 'services',
        'tags': 'recherche,filtres,trouver,découvrir',
    },
    {
        'title': "Page détaillée d'un service",
        'question': "Quelles informations trouve-t-on sur la page d'un service ?",
        'answer': (
            "La page détaillée d'un service contient : "
            "la galerie d'images du service, "
            "la description complète, "
            "le titre, prix et délai de livraison, "
            "le profil du prestataire (photo, bio, compétences, réputation), "
            "les avis et notes des consommateurs précédents, "
            "et le bouton pour passer commande ou contacter le prestataire."
        ),
        'category': 'services',
        'tags': 'page service,détails,affichage',
    },
    {
        'title': "Annonces signalées",
        'question': "Que se passe-t-il si mon annonce est signalée ?",
        'answer': (
            "Si une annonce est signalée par un utilisateur, elle est soumise à validation par "
            "l'administrateur avant republication. L'administrateur examine le signalement et : "
            "soit il valide l'annonce (elle reste publique), "
            "soit il la supprime si elle viole les règles de la plateforme. "
            "Tu reçois une notification dans les deux cas."
        ),
        'category': 'services',
        'tags': 'signalement,modération,annonce,validation',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M3 - COMMANDES ET PAIEMENT
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Passer une commande",
        'question': "Comment passer une commande pour un service ?",
        'answer': (
            "Pour passer une commande : "
            "1. Trouve le service qui t'intéresse via la recherche. "
            "2. Clique sur le service pour voir les détails. "
            "3. Examine les options et le profil du prestataire. "
            "4. Clique sur 'Commander'. "
            "5. Choisis les options si disponibles. "
            "6. Confirme avec le paiement simulé (carte fictive). "
            "Le prestataire est notifié immédiatement et la commande passe à l'état 'En attente'."
        ),
        'category': 'orders',
        'tags': 'commander,commande,achat,service',
    },
    {
        'title': "Paiement simulé",
        'question': "Comment fonctionne le paiement sur StudiServ ?",
        'answer': (
            "StudiServ utilise un système de paiement simulé à des fins académiques. "
            "Tu entres les informations d'une carte bancaire fictive pour simuler l'expérience "
            "d'une vraie marketplace. AUCUNE TRANSACTION RÉELLE n'a lieu, aucun argent n'est transféré. "
            "Les revenus affichés dans le tableau de bord des prestataires sont également simulés. "
            "C'est un projet académique qui démontre l'architecture d'une marketplace complète."
        ),
        'category': 'orders',
        'tags': 'paiement,simulé,carte fictive,académique',
    },
    {
        'title': "Cycle de vie d'une commande",
        'question': "Quels sont les différents états d'une commande ?",
        'answer': (
            "Une commande suit un cycle strict et non réversible avec 4 états : "
            "1. En attente : la commande vient d'être passée, le prestataire ne l'a pas encore acceptée. "
            "2. En cours : le prestataire a accepté et travaille sur la commande. "
            "3. Livré : le prestataire a terminé et soumis le travail pour validation. "
            "4. Terminé : le consommateur a validé la réception et peut laisser un avis. "
            "Ce flux ne peut pas être inversé une fois engagé."
        ),
        'category': 'orders',
        'tags': 'états,statut,cycle,workflow',
    },
    {
        'title': "Suivi de commande",
        'question': "Comment suivre l'état de ma commande ?",
        'answer': (
            "Va dans 'Mes commandes' depuis ton tableau de bord. "
            "Chaque commande affiche son statut actuel : En attente, En cours, Livré, ou Terminé. "
            "Tu reçois aussi des notifications à chaque changement d'état. "
            "Tu peux communiquer avec le prestataire via la messagerie intégrée pour toute question. "
            "L'historique complet de tes commandes (achetées et vendues) est accessible à tout moment."
        ),
        'category': 'orders',
        'tags': 'suivi,état,commande,historique',
    },
    {
        'title': "Annuler une commande",
        'question': "Puis-je annuler une commande ?",
        'answer': (
            "L'annulation d'une commande n'est possible QUE si son statut est 'En attente' "
            "(c'est-à-dire avant que le prestataire ne l'accepte et commence le travail). "
            "Une fois la commande à l'état 'En cours', l'annulation n'est plus possible directement. "
            "Si tu rencontres un problème après ce stade, contacte le prestataire via la messagerie "
            "ou ouvre un litige auprès de l'administrateur."
        ),
        'category': 'orders',
        'tags': 'annulation,annuler,commande,règle',
    },
    {
        'title': "Historique des commandes",
        'question': "Où puis-je voir mes anciennes commandes ?",
        'answer': (
            "Va dans 'Mes commandes' dans ton tableau de bord. Tu trouveras : "
            "- Côté consommateur : l'historique de toutes les commandes que tu as achetées. "
            "- Côté prestataire : l'historique de toutes les commandes que tu as reçues (vendues). "
            "Chaque commande affiche son statut, sa date, le montant et les détails du service. "
            "Tu peux filtrer par état pour retrouver rapidement une commande spécifique."
        ),
        'category': 'orders',
        'tags': 'historique,anciennes commandes,archives',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M4 - MESSAGERIE TEMPS RÉEL
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Messagerie temps réel",
        'question': "Comment fonctionne la messagerie sur StudiServ ?",
        'answer': (
            "StudiServ dispose d'une messagerie interne temps réel basée sur la technologie WebSockets. "
            "Elle permet aux consommateurs et prestataires de communiquer instantanément. "
            "Depuis la page d'un service, clique sur 'Contacter le prestataire'. "
            "Tu peux envoyer des messages texte et des fichiers (PDF, images jusqu'à 10 MB). "
            "Tu reçois une notification en temps réel pour chaque nouveau message reçu. "
            "Toutes les conversations sont archivées et accessibles depuis ton tableau de bord."
        ),
        'category': 'messaging',
        'tags': 'messagerie,chat,temps réel,websocket',
    },
    {
        'title': "Démarrer une conversation",
        'question': "Comment démarrer une conversation avec un prestataire ou un consommateur ?",
        'answer': (
            "Plusieurs façons de démarrer une conversation : "
            "1. Depuis la page d'un service, clique sur 'Contacter le prestataire'. "
            "2. Depuis ta liste de commandes, clique sur 'Messagerie' pour cette commande. "
            "3. Depuis l'onglet Messages, clique sur '+' pour nouvelle conversation. "
            "La messagerie est privée et 1-à-1 entre deux utilisateurs (consommateur ↔ prestataire)."
        ),
        'category': 'messaging',
        'tags': 'démarrer,conversation,contacter,nouvelle',
    },
    {
        'title': "Partage de fichiers",
        'question': "Quels types de fichiers puis-je partager dans la messagerie ?",
        'answer': (
            "Tu peux partager des fichiers PDF et des images (JPEG, PNG, GIF, WEBP) "
            "directement dans la conversation. "
            "La taille maximale par fichier est de 10 MB. "
            "Clique sur l'icône trombone dans la conversation pour sélectionner un fichier. "
            "Le fichier est envoyé instantanément et reste accessible dans l'historique."
        ),
        'category': 'messaging',
        'tags': 'fichiers,partager,PDF,images,upload',
    },
    {
        'title': "Notifications messages",
        'question': "Est-ce que je reçois des notifications pour les nouveaux messages ?",
        'answer': (
            "Oui ! StudiServ envoie des notifications push en temps réel pour chaque nouveau message. "
            "Tu vois un badge avec le nombre de messages non lus dans l'onglet Messages. "
            "Les notifications fonctionnent même quand tu navigues sur d'autres pages de la plateforme. "
            "Tu peux marquer les messages comme lus en ouvrant la conversation."
        ),
        'category': 'messaging',
        'tags': 'notifications,messages,alertes,push',
    },
    {
        'title': "Archivage des conversations",
        'question': "Mes conversations sont-elles sauvegardées ?",
        'answer': (
            "Oui, toutes les conversations sont archivées automatiquement et restent accessibles "
            "dans l'historique des messages. Tu peux retrouver tous tes échanges passés "
            "même après la clôture d'une commande. Les fichiers partagés sont également conservés "
            "et téléchargeables à tout moment."
        ),
        'category': 'messaging',
        'tags': 'archivage,historique,sauvegarde,conversations',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M5 - ÉVALUATIONS ET AVIS
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Laisser un avis",
        'question': "Comment laisser un avis après une prestation ?",
        'answer': (
            "Pour laisser un avis : "
            "1. Va dans 'Mes commandes' dans ton tableau de bord. "
            "2. Trouve une commande au statut 'Terminé'. "
            "3. Clique sur 'Laisser un avis'. "
            "4. Donne une note de 1 à 5 étoiles. "
            "5. Rédige un commentaire textuel décrivant ton expérience. "
            "6. Valide. "
            "Un avis ne peut être laissé QUE lorsque la commande est au statut 'Terminé'. "
            "Tu ne peux laisser qu'UN SEUL avis par commande terminée."
        ),
        'category': 'reputation',
        'tags': 'avis,note,étoiles,évaluation,commentaire',
    },
    {
        'title': "Note moyenne",
        'question': "Comment est calculée la note moyenne d'un prestataire ?",
        'answer': (
            "La note moyenne d'un prestataire est recalculée AUTOMATIQUEMENT "
            "après chaque nouvel avis. C'est la moyenne arithmétique de toutes les notes "
            "(1 à 5 étoiles) reçues par le prestataire sur toutes ses commandes terminées. "
            "Cette note est affichée sur son profil public et influence son classement "
            "dans les résultats de recherche."
        ),
        'category': 'reputation',
        'tags': 'note moyenne,calcul,moyenne,étoiles',
    },
    {
        'title': "Signaler un avis abusif",
        'question': "Comment signaler un avis que je pense abusif ou faux ?",
        'answer': (
            "Sur chaque avis, tu trouveras un bouton 'Signaler'. "
            "1. Clique sur 'Signaler' à côté de l'avis problématique. "
            "2. Indique la raison du signalement (avis abusif, faux, frauduleux, contenu inapproprié). "
            "3. L'administrateur examine ton signalement. "
            "4. Si l'avis est jugé abusif, il est supprimé et tu en es notifié. "
            "Le système de modération maintient la qualité et l'authenticité des avis."
        ),
        'category': 'reputation',
        'tags': 'signaler,avis,abusif,modération,faux',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M6 - REPUTATION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Score de réputation",
        'question': "Qu'est-ce que le score de réputation ?",
        'answer': (
            "Le score de réputation est un indicateur dynamique calculé à partir de deux critères : "
            "1. Les avis reçus (note moyenne sur 5 étoiles). "
            "2. Le taux de complétion des commandes (pourcentage de commandes menées à terme). "
            "Ce score influence directement le classement du prestataire dans les résultats de recherche : "
            "plus le score est élevé, plus le prestataire apparaît en haut. "
            "L'historique du score est visible sur le profil public du prestataire."
        ),
        'category': 'reputation',
        'tags': 'réputation,score,calcul,classement',
    },
    {
        'title': "Badge de confiance",
        'question': "Qu'est-ce que le badge 'Prestataire de confiance' ?",
        'answer': (
            "Le badge 'Prestataire de confiance' est une distinction visuelle attribuée AUTOMATIQUEMENT "
            "aux prestataires qui remplissent DEUX conditions cumulatives : "
            "1. Une note moyenne d'au moins 4.5 étoiles. "
            "2. Au moins 10 commandes terminées. "
            "Ce badge apparaît sur leur profil et leurs annonces, "
            "et les propulse en haut des résultats de recherche. "
            "C'est un signal fort de qualité pour les consommateurs."
        ),
        'category': 'reputation',
        'tags': 'badge,confiance,prestataire,distinction',
    },
    {
        'title': "Alerte chute de réputation",
        'question': "Que se passe-t-il si ma réputation baisse fortement ?",
        'answer': (
            "StudiServ surveille en permanence les scores de réputation. "
            "En cas de chute brutale du score d'un prestataire, une alerte interne est déclenchée "
            "automatiquement. Cette alerte permet à l'administrateur d'examiner la situation, "
            "et au prestataire d'être notifié pour comprendre les raisons (avis négatifs récents, "
            "commandes annulées, etc.) et améliorer ses pratiques."
        ),
        'category': 'reputation',
        'tags': 'alerte,chute,réputation,surveillance',
    },
    {
        'title': "Classement dans les recherches",
        'question': "Comment apparaître en haut des résultats de recherche ?",
        'answer': (
            "Pour bien te classer dans les résultats de recherche : "
            "1. Maintiens une excellente note moyenne (au moins 4.5 étoiles). "
            "2. Complète toutes tes commandes (évite les annulations). "
            "3. Obtiens le badge 'Prestataire de confiance' (4.5+ et 10+ commandes). "
            "4. Réponds rapidement aux messages des consommateurs. "
            "5. Soigne tes annonces (descriptions détaillées, belles images). "
            "Le classement est basé sur le score de réputation dynamique."
        ),
        'category': 'reputation',
        'tags': 'classement,recherche,visibilité,SEO',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M7 - RECOMMANDATIONS
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Système de recommandation",
        'question': "Comment StudiServ me recommande-t-il des services ?",
        'answer': (
            "StudiServ utilise un moteur de recommandation intelligent qui te suggère "
            "des services pertinents basés sur : "
            "1. Ton historique de commandes passées. "
            "2. Les services similaires à ceux que tu consultes. "
            "3. Tes catégories préférées (la catégorie la plus fréquentée par toi). "
            "4. Les services populaires et les nouveaux prestataires. "
            "Les recommandations apparaissent dans ton tableau de bord et sur la page d'accueil."
        ),
        'category': 'general',
        'tags': 'recommandations,IA,suggestions,personnalisation',
    },
    {
        'title': "Sections page d'accueil",
        'question': "Quelles sections trouve-t-on sur la page d'accueil ?",
        'answer': (
            "La page d'accueil de StudiServ propose plusieurs sections éditoriales : "
            "1. 'Services populaires' : les services les plus commandés. "
            "2. 'Nouveaux prestataires' : les derniers prestataires inscrits sur la plateforme. "
            "3. 'Recommandations pour toi' : services personnalisés selon ton profil. "
            "4. 'Catégories' : navigation par type de service. "
            "Ces sections aident à découvrir facilement de nouveaux services."
        ),
        'category': 'general',
        'tags': 'page accueil,sections,populaires,nouveaux',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # M8 - ADMINISTRATION
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Dashboard administrateur",
        'question': "Que contient le tableau de bord administrateur ?",
        'answer': (
            "Le dashboard administrateur affiche des statistiques globales : "
            "nombre total d'utilisateurs (consommateurs et prestataires), "
            "nombre de services actifs, "
            "nombre de commandes (en cours, terminées, annulées), "
            "revenus simulés totaux, "
            "tendances sur les 7 derniers jours, "
            "top 5 des catégories les plus actives, "
            "et nombre de cartes étudiantes en attente de validation."
        ),
        'category': 'general',
        'tags': 'dashboard,admin,statistiques,tableau de bord',
    },
    {
        'title': "Gestion des utilisateurs admin",
        'question': "Comment l'admin gère-t-il les utilisateurs ?",
        'answer': (
            "L'administrateur peut : "
            "rechercher des utilisateurs par nom, email ou rôle, "
            "filtrer par statut (actif/inactif) et par rôle (consommateur/prestataire), "
            "activer ou désactiver un compte, "
            "supprimer définitivement un compte en cas de violation grave des règles. "
            "Toutes les actions sont tracées dans les logs de modération."
        ),
        'category': 'general',
        'tags': 'gestion utilisateurs,admin,modération,comptes',
    },
    {
        'title': "Validation cartes étudiantes",
        'question': "Comment l'admin valide-t-il les cartes étudiantes ?",
        'answer': (
            "L'administrateur examine manuellement chaque carte étudiante soumise : "
            "1. Il accède à la file d'attente des cartes en attente. "
            "2. Il vérifie l'authenticité de la carte (nom, université, validité). "
            "3. Il valide ou refuse la carte avec justification. "
            "Le délai de traitement est de 24 à 48h. "
            "Le prestataire reçoit une notification email du résultat."
        ),
        'category': 'general',
        'tags': 'validation,carte étudiante,admin,vérification',
    },
    {
        'title': "Gestion des litiges",
        'question': "Comment sont gérés les litiges sur StudiServ ?",
        'answer': (
            "En cas de litige entre un consommateur et un prestataire : "
            "1. L'un des deux ouvre un litige depuis sa commande. "
            "2. Il décrit le problème (travail non livré, qualité insatisfaisante, etc.). "
            "3. L'administrateur examine les preuves et la conversation. "
            "4. Il prend une décision : remboursement, prestation validée, résolution partielle, ou rejet. "
            "5. Les deux parties sont notifiées de la résolution. "
            "Le système assure une médiation neutre."
        ),
        'category': 'general',
        'tags': 'litige,conflit,résolution,médiation',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TECHNIQUE
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Stack technologique",
        'question': "Avec quelles technologies StudiServ est-il développé ?",
        'answer': (
            "StudiServ est une application web full-stack utilisant : "
            "Frontend : React.js, JavaScript, HTML, CSS (Single Page Application). "
            "Backend : Python avec Django comme framework principal. "
            "API : Django REST Framework pour exposer les endpoints RESTful. "
            "Temps réel : WebSockets via Django Channels pour la messagerie instantanée. "
            "Base de données : SQL relationnelle. "
            "Authentification : JWT (JSON Web Tokens) pour la sécurité des sessions. "
            "Chatbot : RAG avec LangChain, ChromaDB et OpenAI/Ollama."
        ),
        'category': 'technical',
        'tags': 'stack,technologies,django,react,websocket',
    },
    {
        'title': "Architecture de StudiServ",
        'question': "Quelle est l'architecture technique de StudiServ ?",
        'answer': (
            "StudiServ suit une architecture client-serveur RESTful classique avec : "
            "un client SPA React qui consomme une API REST Django, "
            "des WebSockets pour le temps réel (messagerie), "
            "une base de données SQL pour la persistance, "
            "un système de stockage de fichiers pour les cartes étudiantes, "
            "images de services et fichiers partagés. "
            "L'authentification utilise JWT avec refresh tokens pour la sécurité."
        ),
        'category': 'technical',
        'tags': 'architecture,SPA,REST,client-serveur',
    },
    {
        'title': "Problème de messagerie WebSocket",
        'question': "La messagerie ne fonctionne pas, les messages ne s'envoient pas en temps réel.",
        'answer': (
            "Si la messagerie temps réel ne fonctionne pas : "
            "1. Actualise la page (F5). "
            "2. Vérifie ta connexion internet. "
            "3. Désactive temporairement les extensions de navigateur (VPN, bloqueurs). "
            "4. Essaie un autre navigateur (Chrome, Firefox). "
            "5. Si le problème persiste, le serveur WebSocket peut être temporairement indisponible. "
            "Les messages envoyés seront livrés dès le rétablissement de la connexion."
        ),
        'category': 'technical',
        'tags': 'problème,websocket,messagerie,connexion',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ÉQUIPE ET CONTEXTE
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Équipe de développement",
        'question': "Qui a développé StudiServ ?",
        'answer': (
            "StudiServ a été développé par une équipe de 3 étudiants : "
            "Eya Boiguerra, Amine Hasnaoui et Rayen Hammi. "
            "Le projet a été encadré par Slim Abbes (SESAME). "
            "C'est un projet académique réalisé durant l'année universitaire 2025-2026."
        ),
        'category': 'general',
        'tags': 'équipe,développeurs,étudiants,projet',
    },
    {
        'title': "Encadrement projet",
        'question': "Qui encadre le projet StudiServ ?",
        'answer': (
            "Le projet StudiServ est encadré par Slim Abbes, professeur à SESAME. "
            "Il guide l'équipe (Eya Boiguerra, Amine Hasnaoui et Rayen Hammi) "
            "tout au long du développement, depuis la conception jusqu'à la mise en production."
        ),
        'category': 'general',
        'tags': 'encadrant,professeur,SESAME,Slim Abbes',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # GLOSSAIRE / DÉFINITIONS
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Définition Marketplace",
        'question': "C'est quoi une marketplace ?",
        'answer': (
            "Une marketplace est une plateforme qui met en relation des vendeurs (prestataires) "
            "et des acheteurs (consommateurs). Dans le cas de StudiServ, c'est une marketplace "
            "spécifiquement dédiée aux étudiants : les étudiants prestataires y proposent leurs "
            "compétences sous forme de services payants, et les étudiants consommateurs y achètent "
            "ces services. La plateforme gère toute la transaction de bout en bout."
        ),
        'category': 'general',
        'tags': 'définition,marketplace,plateforme,concept',
    },
    {
        'title': "Définition WebSocket",
        'question': "C'est quoi un WebSocket ?",
        'answer': (
            "Un WebSocket est un protocole de communication qui permet une connexion bidirectionnelle "
            "et persistante entre le navigateur de l'utilisateur et le serveur. "
            "Contrairement aux requêtes HTTP classiques (qui sont fermées après la réponse), "
            "le WebSocket reste ouvert, permettant au serveur d'envoyer des messages instantanément "
            "au client. StudiServ utilise les WebSockets via Django Channels pour la messagerie en temps réel."
        ),
        'category': 'technical',
        'tags': 'websocket,définition,protocole,temps réel',
    },
    {
        'title': "Définition JWT",
        'question': "C'est quoi JWT ?",
        'answer': (
            "JWT (JSON Web Token) est un mécanisme d'authentification sécurisé moderne. "
            "Quand tu te connectes à StudiServ, le serveur te délivre un token signé numériquement. "
            "Ce token est ensuite envoyé avec chaque requête pour prouver ton identité. "
            "StudiServ utilise JWT avec un access token (valide 2h) et un refresh token (valide 7 jours) "
            "pour maintenir la session de manière sécurisée."
        ),
        'category': 'technical',
        'tags': 'JWT,authentification,token,sécurité',
    },
    {
        'title': "Définition RAG",
        'question': "C'est quoi RAG ? Comment fonctionne le chatbot ?",
        'answer': (
            "RAG signifie 'Retrieval-Augmented Generation' — c'est la technique utilisée par le chatbot StudiServ. "
            "Quand tu poses une question, le chatbot : "
            "1. Cherche dans sa base de connaissances les documents les plus pertinents (Retrieval). "
            "2. Combine ces informations avec ta question (Augmented). "
            "3. Génère une réponse cohérente et précise avec un LLM (Generation). "
            "Cela permet d'avoir des réponses précises basées sur les vraies informations de StudiServ, "
            "et non sur des connaissances générales du modèle."
        ),
        'category': 'technical',
        'tags': 'RAG,chatbot,IA,génération,recherche',
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FAQ PRATIQUES
    # ═══════════════════════════════════════════════════════════════════════
    {
        'title': "Combien coûte StudiServ",
        'question': "Est-ce que StudiServ est gratuit ? Combien ça coûte ?",
        'answer': (
            "L'inscription et l'utilisation de StudiServ sont entièrement gratuites pour les étudiants. "
            "La plateforme ne prend pas de commission sur les transactions (qui sont d'ailleurs simulées "
            "dans cette version académique). "
            "Tu peux donc t'inscrire, publier des annonces, passer des commandes et utiliser "
            "toutes les fonctionnalités sans aucun frais."
        ),
        'category': 'general',
        'tags': 'gratuit,prix,coût,frais,commission',
    },
    {
        'title': "Sécurité de la plateforme",
        'question': "StudiServ est-il sécurisé ? Mes données sont-elles protégées ?",
        'answer': (
            "StudiServ implémente plusieurs mesures de sécurité : "
            "authentification JWT sécurisée, "
            "protection anti-brute-force (blocage après 5 tentatives échouées), "
            "vérification obligatoire de l'identité étudiante, "
            "communication chiffrée (HTTPS en production), "
            "modération active des contenus et signalements, "
            "et système de litige pour résoudre les conflits. "
            "Tes données personnelles sont stockées de manière sécurisée et ne sont pas partagées."
        ),
        'category': 'general',
        'tags': 'sécurité,protection,données,confidentialité',
    },
    {
        'title': "Différence consommateur prestataire",
        'question': "Quelle est la différence entre consommateur et prestataire ?",
        'answer': (
            "Sur StudiServ il y a 2 types d'étudiants : "
            "CONSOMMATEUR (acheteur) : il cherche et achète des services proposés par d'autres étudiants. "
            "Il n'a pas besoin de vérifier sa carte étudiante pour s'inscrire. "
            "PRESTATAIRE (vendeur) : il propose ses compétences sous forme de services payants. "
            "Il doit OBLIGATOIREMENT uploader et faire valider sa carte étudiante avant de publier des annonces. "
            "Un même utilisateur peut être à la fois consommateur (pour acheter) et prestataire (pour vendre)."
        ),
        'category': 'account',
        'tags': 'différence,consommateur,prestataire,rôle',
    },
    {
        'title': "Compétences techniques",
        'question': "Quelles compétences techniques sont utilisées sur StudiServ ?",
        'answer': (
            "StudiServ couvre toute une gamme de compétences techniques modernes : "
            "développement web (React, Django, REST API), "
            "communication temps réel (WebSockets, Django Channels), "
            "intelligence artificielle (chatbot RAG avec LangChain), "
            "base de données SQL relationnelle, "
            "authentification sécurisée (JWT), "
            "gestion de fichiers et uploads, "
            "et déploiement d'applications full-stack."
        ),
        'category': 'technical',
        'tags': 'compétences,techniques,développement,stack',
    },
    {
        'title': "Contact support",
        'question': "Comment contacter le support StudiServ ?",
        'answer': (
            "Pour contacter l'équipe StudiServ : "
            "1. Via le formulaire de contact dans ton tableau de bord. "
            "2. Par email à support@studiserv.tn pour les questions générales. "
            "3. Via la messagerie interne pour les questions sur une commande spécifique. "
            "4. Via le chatbot IA pour les questions courantes (24/7). "
            "L'équipe répond généralement dans les 24h en jours ouvrés."
        ),
        'category': 'general',
        'tags': 'contact,support,aide,équipe',
    },
]


class Command(BaseCommand):
    help = (
        'Charge la base de connaissances complète de StudiServ (issue du PDF officiel) '
        'et indexe dans ChromaDB pour le chatbot RAG.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer toutes les FAQ existantes avant de charger',
        )
        parser.add_argument(
            '--reindex-only',
            action='store_true',
            help='Réindexer uniquement sans charger les FAQ',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = FAQDocument.objects.count()
            FAQDocument.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'🗑  {count} FAQ existantes supprimées.'
            ))

        if not options['reindex_only']:
            self.stdout.write('📚 Chargement de la base de connaissances StudiServ...')
            created_count = 0
            updated_count = 0
            for faq_data in STUDISERV_KNOWLEDGE_BASE:
                obj, created = FAQDocument.objects.update_or_create(
                    title=faq_data['title'],
                    defaults=faq_data,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'✓ {created_count} nouvelles FAQ chargées, {updated_count} mises à jour.'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'📊 Total : {FAQDocument.objects.filter(is_active=True).count()} FAQ actives.'
            ))

        # Indexation dans ChromaDB
        self.stdout.write('\n🔍 Indexation dans ChromaDB...')
        try:
            from chatbot.rag_engine import index_faq_documents
            count = index_faq_documents()
            self.stdout.write(self.style.SUCCESS(
                f'✓ {count} documents indexés dans ChromaDB.\n'
                f'🤖 Le chatbot est prêt à répondre aux questions sur StudiServ !'
            ))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Dépendances RAG manquantes : {e}\n'
                'Installe : pip install langchain langchain-community chromadb sentence-transformers'
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'⚠ ChromaDB non disponible : {e}\n'
                'Les FAQ sont chargées en base mais pas encore indexées vectoriellement.'
            ))