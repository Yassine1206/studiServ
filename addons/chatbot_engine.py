# addons/chatbot_engine.py
# Moteur de chatbot INTELLIGENT pour StudiServ.
#
# Architecture :
#   1. Base de connaissances intégrée (répond sans LLM ni ChromaDB)
#   2. Matching sémantique par mots-clés + intentions
#   3. Recommandation de prestataires (moteur marketplace)
#   4. Fallback vers ChromaDB + LLM si disponibles
#
# Ce module fonctionne 100% hors-ligne et répond à toutes les questions
# relatives à StudiServ : commandes, services, compte, messagerie, etc.

import logging
import re

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# BASE DE CONNAISSANCES INTÉGRÉE — StudiServ
# Chaque entrée : { patterns, answer, category }
# ═══════════════════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = [
    # ─── COMMANDES ───────────────────────────────────────────────────────────
    {
        "patterns": [
            r"passer\s+une?\s+commande", r"commander\s+un\s+service",
            r"comment\s+commander", r"passer\s+commande",
            r"how\s+to\s+order", r"place\s+an?\s+order",
            r"acheter\s+un\s+service", r"je\s+veux\s+commander",
        ],
        "answer": (
            "🛒 **Comment passer une commande sur StudiServ :**\n\n"
            "1. **Trouve le service** : utilise la barre de recherche ou parcours les catégories\n"
            "2. **Consulte la fiche** : clique sur le service pour voir tous les détails, le profil du prestataire et les avis\n"
            "3. **Clique sur « Commander »** : bouton disponible sur la page du service\n"
            "4. **Confirme ta commande** : choisis les options si disponibles\n"
            "5. **Effectue le paiement simulé** : entre une carte fictive (aucun argent réel)\n\n"
            "✅ Le prestataire est notifié immédiatement et ta commande passe à l'état **« En attente »**.\n"
            "Tu peux suivre ta commande depuis *Mes commandes* dans ton tableau de bord."
        ),
        "category": "orders",
    },
    {
        "patterns": [
            r"état\s+(d[eu]|la)\s+commande", r"statut\s+(d[eu]|la)\s+commande",
            r"états?\s+(possible|commande)", r"suivi\s+(de\s+)?commande",
            r"cycle\s+(de\s+)?commande", r"workflow\s+(de\s+)?commande",
        ],
        "answer": (
            "📦 **Cycle de vie d'une commande StudiServ :**\n\n"
            "Une commande passe par **4 états** dans cet ordre :\n\n"
            "1. **⏳ En attente** — commande passée, le prestataire ne l'a pas encore acceptée\n"
            "2. **🔨 En cours** — le prestataire a accepté et travaille dessus\n"
            "3. **📬 Livré** — le prestataire a terminé et soumis son travail\n"
            "4. **✅ Terminé** — tu as validé la réception (tu peux maintenant laisser un avis)\n\n"
            "⚠️ Ce cycle est **non réversible** : impossible de revenir en arrière une fois une étape franchie."
        ),
        "category": "orders",
    },
    {
        "patterns": [
            r"annuler\s+(ma\s+)?commande", r"annulation\s+(de\s+)?commande",
            r"cancel\s+(an?\s+)?order",
        ],
        "answer": (
            "❌ **Annuler une commande :**\n\n"
            "L'annulation est possible **uniquement** si la commande est au statut **« En attente »** "
            "(avant que le prestataire ne commence le travail).\n\n"
            "➡️ Va dans *Mes commandes* → clique sur la commande → bouton « Annuler ».\n\n"
            "⚠️ Une fois à l'état **« En cours »**, l'annulation directe n'est plus possible. "
            "Dans ce cas, contacte le prestataire via la messagerie ou ouvre un litige auprès de l'administrateur."
        ),
        "category": "orders",
    },
    {
        "patterns": [
            r"mes\s+commandes", r"historique\s+(des\s+)?commandes",
            r"voir\s+(mes\s+)?commandes", r"retrouver\s+(une\s+)?commande",
            r"anciennes?\s+commandes?",
        ],
        "answer": (
            "📋 **Consulter tes commandes :**\n\n"
            "Va dans ton **tableau de bord** → section **« Mes commandes »**.\n\n"
            "Tu y trouveras :\n"
            "• Toutes tes commandes avec leur statut actuel\n"
            "• La date, le montant et les détails de chaque commande\n"
            "• Le fil de messagerie lié à chaque commande\n\n"
            "💡 **Côté prestataire :** tu peux voir les commandes reçues dans l'onglet *Mes commandes* de ton tableau de bord prestataire."
        ),
        "category": "orders",
    },

    # ─── PAIEMENT ─────────────────────────────────────────────────────────────
    {
        "patterns": [
            r"paiement", r"payer", r"comment\s+payer", r"système\s+de\s+paiement",
            r"carte\s+(?:bancaire|fictive|de\s+crédit)", r"payment", r"argent\s+réel",
            r"transaction", r"prix\s+service",
        ],
        "answer": (
            "💳 **Système de paiement StudiServ :**\n\n"
            "StudiServ utilise un **paiement 100% simulé** à des fins académiques.\n\n"
            "• Tu entres les données d'une **carte bancaire fictive** pour simuler l'expérience\n"
            "• **Aucune transaction réelle** n'a lieu — aucun argent n'est débité\n"
            "• Les revenus affichés dans les tableaux de bord sont également simulés\n\n"
            "📚 C'est un projet académique qui démontre l'architecture complète d'une marketplace, "
            "y compris le flux de paiement."
        ),
        "category": "orders",
    },

    # ─── SERVICES / ANNONCES ──────────────────────────────────────────────────
    {
        "patterns": [
            r"créer\s+(une?\s+)?annonce", r"publier\s+(un\s+)?service",
            r"nouvelle\s+annonce", r"comment\s+publier",
            r"create\s+(an?\s+)?listing", r"post\s+(a\s+)?service",
            r"je\s+veux\s+proposer\s+un\s+service",
        ],
        "answer": (
            "📢 **Créer une annonce de service (prestataires uniquement) :**\n\n"
            "1. **Assure-toi d'être prestataire vérifié** (carte étudiante validée)\n"
            "2. Va dans ton **tableau de bord prestataire**\n"
            "3. Clique sur **« Publier un service »** ou **« Nouvelle annonce »**\n"
            "4. Remplis les champs obligatoires :\n"
            "   • 📝 Titre clair et accrocheur\n"
            "   • 📄 Description détaillée de ta prestation\n"
            "   • 🏷️ Catégorie (cours, design, traduction, etc.)\n"
            "   • 💰 Prix (en dinars)\n"
            "   • ⏰ Délai de livraison estimé\n"
            "5. Ajoute des **photos** pour illustrer ton service\n"
            "6. Clique sur **« Publier »**\n\n"
            "✅ Ton annonce est immédiatement visible par tous les utilisateurs."
        ),
        "category": "services",
    },
    {
        "patterns": [
            r"modifier\s+(une?\s+)?annonce", r"éditer\s+(un\s+)?service",
            r"supprimer\s+(une?\s+)?annonce", r"changer\s+(une?\s+)?annonce",
            r"update\s+(a\s+)?listing",
        ],
        "answer": (
            "✏️ **Modifier ou supprimer une annonce :**\n\n"
            "**Modifier :**\n"
            "➡️ Tableau de bord → *Mes services* → clique sur l'annonce → **« Modifier »**\n\n"
            "**Supprimer :**\n"
            "➡️ Tableau de bord → *Mes services* → clique sur l'annonce → **« Supprimer »**\n\n"
            "⚠️ **Remarque :** Tu ne peux pas supprimer une annonce qui a des commandes en cours. "
            "Attends que toutes les commandes actives soient terminées."
        ),
        "category": "services",
    },
    {
        "patterns": [
            r"rechercher\s+(un\s+)?service", r"trouver\s+(un\s+)?service",
            r"chercher\s+(un\s+)?service", r"search\s+(for\s+a\s+)?service",
            r"comment\s+trouver", r"trouver\s+un\s+prestataire",
        ],
        "answer": (
            "🔍 **Rechercher un service sur StudiServ :**\n\n"
            "**Méthode 1 — Barre de recherche :**\n"
            "→ Tape des mots-clés dans la barre en haut de page (ex: « cours maths », « design logo »)\n\n"
            "**Méthode 2 — Filtres avancés :**\n"
            "→ Affine par : catégorie, fourchette de prix, note minimum\n\n"
            "**Méthode 3 — Page d'accueil :**\n"
            "→ *Services populaires*, *Nouveaux prestataires*, *Recommandations pour toi*\n\n"
            "💡 Les résultats sont triés par **score de réputation** du prestataire."
        ),
        "category": "services",
    },
    {
        "patterns": [
            r"types?\s+de\s+services?", r"quels?\s+services?", r"catégories?\s+de\s+services?",
            r"quoi\s+proposer", r"genre\s+de\s+services?",
        ],
        "answer": (
            "🎓 **Types de services disponibles sur StudiServ :**\n\n"
            "• 📚 **Cours particuliers** : maths, physique, langues, informatique...\n"
            "• 🎨 **Design graphique** : logos, affiches, identité visuelle, UI/UX\n"
            "• 🌐 **Développement web** : front-end, back-end, full-stack\n"
            "• 📝 **Rédaction & correction** : textes académiques, CV, lettres\n"
            "• 🔤 **Traduction** : français, anglais, arabe\n"
            "• 🎬 **Montage vidéo** : création de contenu multimédia\n"
            "• 📊 **Comptabilité & gestion** : aide aux devoirs, projets\n"
            "• Et bien d'autres selon les compétences des étudiants !"
        ),
        "category": "services",
    },

    # ─── INSCRIPTION / COMPTE ──────────────────────────────────────────────────
    {
        "patterns": [
            r"créer\s+(un\s+)?compte", r"s'inscrire", r"inscription",
            r"sign\s*up", r"register", r"comment\s+m'inscrire",
            r"comment\s+créer\s+un\s+compte", r"nouveau\s+compte",
        ],
        "answer": (
            "🎉 **Créer un compte sur StudiServ :**\n\n"
            "1. Clique sur **« S'inscrire »** en haut à droite\n"
            "2. Entre ton **email universitaire** (obligatoire)\n"
            "3. Renseigne ton **nom, prénom** et un **mot de passe sécurisé**\n"
            "4. Choisis ton **rôle** :\n"
            "   • 🛒 **Consommateur** : pour acheter des services\n"
            "   • 💼 **Prestataire** : pour vendre tes services (upload de carte étudiante requis)\n"
            "5. Valide le formulaire\n\n"
            "📧 L'inscription est réservée aux étudiants avec un **email universitaire valide**."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"se\s+connecter", r"connexion", r"login", r"sign\s*in",
            r"comment\s+me\s+connecter", r"mot\s+de\s+passe\s+incorrect",
        ],
        "answer": (
            "🔑 **Se connecter à StudiServ :**\n\n"
            "1. Va sur la **page de connexion**\n"
            "2. Entre ton **email universitaire** et ton **mot de passe**\n"
            "3. Clique sur **« Se connecter »**\n\n"
            "🔒 StudiServ utilise **JWT (JSON Web Token)** pour une session sécurisée.\n"
            "Ta session reste active **2 heures**, avec un refresh token valable **7 jours**.\n\n"
            "⚠️ Après **5 tentatives échouées**, ton compte est temporairement bloqué (15 min) pour ta sécurité."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"mot\s+de\s+passe\s+oublié", r"réinitialiser\s+(le\s+)?mot\s+de\s+passe",
            r"oublié\s+mon\s+mot\s+de\s+passe", r"forgot\s+password", r"reset\s+password",
        ],
        "answer": (
            "🔐 **Mot de passe oublié :**\n\n"
            "1. Sur la page de connexion, clique sur **« Mot de passe oublié »**\n"
            "2. Entre ton **email universitaire**\n"
            "3. Reçois un **lien de réinitialisation** par email (valable 1 heure)\n"
            "4. Clique sur le lien et choisis un **nouveau mot de passe**\n\n"
            "📥 Si tu ne reçois pas l'email, vérifie ton **dossier spam**."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"devenir\s+prestataire", r"comment\s+(être|devenir)\s+prestataire",
            r"prestataire\s+vérifié", r"vendre\s+mes\s+services",
        ],
        "answer": (
            "💼 **Devenir prestataire sur StudiServ :**\n\n"
            "1. **Inscris-toi** avec ton email universitaire et choisis le rôle **Prestataire**\n"
            "2. **Upload ta carte étudiante** depuis ton tableau de bord\n"
            "3. **Attends la validation** par l'administrateur (délai : 24 à 48h)\n"
            "4. Une fois validé, tu obtiens le statut **« Prestataire vérifié »** ✅\n"
            "5. **Publie tes annonces** et commence à recevoir des commandes !\n\n"
            "📌 La carte étudiante garantit que seuls de vrais étudiants peuvent vendre sur StudiServ."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"carte\s+étudiante", r"upload\s+(ma\s+)?carte", r"vérification\s+carte",
            r"valider\s+(ma\s+)?carte", r"student\s+card",
        ],
        "answer": (
            "🪪 **Carte étudiante sur StudiServ :**\n\n"
            "La carte étudiante est **obligatoire pour les prestataires** seulement.\n\n"
            "**Comment l'uploader :**\n"
            "→ Tableau de bord → section profil → bouton **« Upload ma carte étudiante »**\n\n"
            "**Validation :**\n"
            "• L'administrateur examine ta carte manuellement\n"
            "• Délai : **24 à 48 heures**\n"
            "• Tu reçois une notification du résultat par email\n\n"
            "✅ Une fois validée → statut **Prestataire vérifié** → tu peux publier des annonces."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"modifier\s+(mon\s+)?profil", r"changer\s+(mon\s+)?profil",
            r"photo\s+de\s+profil", r"biographie", r"mes\s+compétences",
            r"mettre\s+à\s+jour\s+(mon\s+)?profil",
        ],
        "answer": (
            "👤 **Modifier ton profil :**\n\n"
            "➡️ Tableau de bord → **« Mon profil »**\n\n"
            "Tu peux modifier :\n"
            "• 📷 Photo de profil\n"
            "• 📝 Biographie\n"
            "• 🎓 Université\n"
            "• 💡 Compétences\n"
            "• 📞 Informations personnelles\n\n"
            "Clique sur **« Enregistrer »** pour sauvegarder tes modifications."
        ),
        "category": "account",
    },

    # ─── MESSAGERIE ──────────────────────────────────────────────────────────
    {
        "patterns": [
            r"messagerie", r"envoyer\s+un\s+message", r"contacter\s+(le\s+)?prestataire",
            r"comment\s+communiquer", r"chat\s+(avec|internal)", r"conversation",
        ],
        "answer": (
            "💬 **Messagerie StudiServ :**\n\n"
            "StudiServ dispose d'une messagerie **temps réel** basée sur **WebSockets**.\n\n"
            "**Comment démarrer une conversation :**\n"
            "• Sur la page d'un service → bouton **« Contacter le prestataire »**\n"
            "• Depuis *Mes commandes* → bouton **« Messagerie »**\n"
            "• Depuis l'onglet **Messages** → bouton **« + »**\n\n"
            "**Fonctionnalités :**\n"
            "• 📨 Messages texte en temps réel\n"
            "• 📎 Partage de fichiers (PDF, images jusqu'à 10 MB)\n"
            "• 🔔 Notifications push pour les nouveaux messages\n"
            "• 📚 Historique archivé et accessible à tout moment"
        ),
        "category": "messaging",
    },
    {
        "patterns": [
            r"partager\s+(des\s+)?fichiers?", r"envoyer\s+(un\s+)?fichier",
            r"pièce\s+jointe", r"upload\s+(un\s+)?fichier\s+dans\s+le\s+chat",
            r"types?\s+de\s+fichiers?\s+(?:autorisés?|acceptés?|supportés?)",
        ],
        "answer": (
            "📎 **Partage de fichiers dans la messagerie :**\n\n"
            "Tu peux partager dans une conversation :\n"
            "• 📄 Fichiers **PDF**\n"
            "• 🖼️ Images **JPEG, PNG, GIF, WEBP**\n\n"
            "**Limite :** 10 MB maximum par fichier\n\n"
            "**Comment faire :** Clique sur l'icône **trombone 📎** dans la conversation → sélectionne ton fichier.\n\n"
            "Le fichier est envoyé instantanément et reste accessible dans l'historique."
        ),
        "category": "messaging",
    },
    {
        "patterns": [
            r"notifications?\s+(messages?|messagerie)", r"badge\s+non\s+lu",
            r"messages?\s+non\s+lus?", r"alertes?\s+messages?",
        ],
        "answer": (
            "🔔 **Notifications de messagerie :**\n\n"
            "• Un **badge rouge** avec le nombre de messages non lus apparaît sur l'onglet Messages\n"
            "• Tu reçois des **notifications push en temps réel** pour chaque nouveau message\n"
            "• Les notifications fonctionnent même quand tu navigues sur d'autres pages\n"
            "• Ouvre la conversation pour marquer les messages comme **lus**"
        ),
        "category": "messaging",
    },

    # ─── AVIS ET RÉPUTATION ───────────────────────────────────────────────────
    {
        "patterns": [
            r"laisser\s+(un\s+)?avis", r"donner\s+(une?\s+)?note", r"évaluer",
            r"commentaire\s+(sur\s+)?prestataire", r"noter\s+un\s+service",
            r"review", r"avis\s+après\s+(commande|prestation)",
        ],
        "answer": (
            "⭐ **Laisser un avis :**\n\n"
            "1. Va dans **Mes commandes** → trouve une commande au statut **« Terminé »**\n"
            "2. Clique sur **« Laisser un avis »**\n"
            "3. Donne une note de **1 à 5 étoiles**\n"
            "4. Rédige un **commentaire** décrivant ton expérience\n"
            "5. Valide\n\n"
            "⚠️ **Règles :**\n"
            "• Un avis est possible **uniquement** après une commande **Terminée**\n"
            "• Tu ne peux laisser qu'**UN SEUL avis** par commande"
        ),
        "category": "reputation",
    },
    {
        "patterns": [
            r"badge\s+(de\s+)?confiance", r"prestataire\s+de\s+confiance",
            r"obtenir\s+(le\s+)?badge", r"trusted\s+provider", r"comment\s+obtenir\s+le\s+badge",
        ],
        "answer": (
            "🏅 **Badge « Prestataire de confiance » :**\n\n"
            "Ce badge est attribué **automatiquement** aux prestataires qui remplissent **2 conditions** :\n\n"
            "✅ Note moyenne ≥ **4.5 étoiles**\n"
            "✅ Au moins **10 commandes terminées**\n\n"
            "**Avantages du badge :**\n"
            "• Apparaît sur ton profil et tes annonces 🏅\n"
            "• Te propulse **en haut des résultats** de recherche\n"
            "• Signal fort de qualité pour les consommateurs\n\n"
            "💡 **Conseil :** Offre un excellent service, réponds vite aux messages, et complète toutes tes commandes !"
        ),
        "category": "reputation",
    },
    {
        "patterns": [
            r"score\s+de\s+réputation", r"réputation", r"calcul\s+(de\s+)?(?:la\s+)?note",
            r"comment\s+est\s+calculé", r"note\s+moyenne",
        ],
        "answer": (
            "📊 **Score de réputation :**\n\n"
            "Le score est calculé à partir de **2 critères** :\n"
            "1. ⭐ **Note moyenne** (de 1 à 5 étoiles) basée sur tous les avis reçus\n"
            "2. ✅ **Taux de complétion** (% de commandes menées à terme)\n\n"
            "Ce score influence directement ton **classement dans les recherches** : "
            "plus ton score est élevé, plus tu apparais en haut des résultats.\n\n"
            "L'historique du score est visible sur ton profil public."
        ),
        "category": "reputation",
    },
    {
        "patterns": [
            r"signaler\s+(un\s+)?avis", r"avis\s+abusif", r"faux\s+avis",
            r"avis\s+frauduleux", r"report\s+(a\s+)?review",
        ],
        "answer": (
            "🚩 **Signaler un avis abusif :**\n\n"
            "1. Sur l'avis problématique, clique sur **« Signaler »**\n"
            "2. Indique la raison (abus, contenu inapproprié, avis frauduleux)\n"
            "3. L'administrateur examine le signalement\n"
            "4. Si l'avis est jugé abusif → il est **supprimé** et tu es notifié\n\n"
            "Ce système garantit l'**authenticité des avis** sur la plateforme."
        ),
        "category": "reputation",
    },

    # ─── LITIGE ───────────────────────────────────────────────────────────────
    {
        "patterns": [
            r"litige", r"problème\s+avec\s+(un\s+)?prestataire", r"conflit",
            r"travail\s+non\s+livré", r"dispute", r"médiation",
            r"qualité\s+insatisfaisante", r"prestataire\s+ne\s+répond\s+pas",
        ],
        "answer": (
            "⚖️ **Ouvrir un litige :**\n\n"
            "En cas de problème avec une commande :\n\n"
            "1. Va dans **Mes commandes** → clique sur la commande concernée\n"
            "2. Clique sur **« Ouvrir un litige »**\n"
            "3. Décris le problème (travail non livré, qualité insatisfaisante...)\n"
            "4. L'administrateur examine les preuves et la conversation\n"
            "5. Il prend une décision : **résolution, remboursement, ou rejet**\n"
            "6. Les deux parties sont notifiées du résultat\n\n"
            "💡 Tente d'abord de résoudre le problème via la **messagerie** directement avec le prestataire."
        ),
        "category": "orders",
    },

    # ─── PRÉSENTATION GÉNÉRALE ────────────────────────────────────────────────
    {
        "patterns": [
            r"c'est\s+quoi\s+studiserv", r"présente[r]?\s+studiserv",
            r"qu'est[- ]ce\s+que\s+studiserv", r"what\s+is\s+studiserv",
            r"studiserv\s+c'est\s+quoi", r"présentation\s+(?:de\s+)?studiserv",
        ],
        "answer": (
            "🎓 **StudiServ — La marketplace étudiante :**\n\n"
            "StudiServ est une plateforme **marketplace** dédiée exclusivement à la **communauté étudiante tunisienne**.\n\n"
            "Elle permet aux étudiants de :\n"
            "• 💼 **Proposer leurs compétences** sous forme de services payants (côté prestataire)\n"
            "• 🛒 **Accéder aux services** proposés par leurs pairs (côté consommateur)\n\n"
            "**Développée par :** Eya Boiguerra, Amine Hasnaoui et Rayen Hammi\n"
            "**Encadrant :** Slim Abbes (SESAME)\n\n"
            "La plateforme garantit la **sécurité**, la **traçabilité** et la **confiance** dans chaque échange."
        ),
        "category": "general",
    },
    {
        "patterns": [
            r"page\s+d'accueil", r"sections?\s+accueil", r"accueil\s+studiserv",
            r"home\s+page",
        ],
        "answer": (
            "🏠 **Page d'accueil StudiServ :**\n\n"
            "La page d'accueil propose plusieurs sections :\n\n"
            "1. 🔥 **Services populaires** — les services les plus commandés\n"
            "2. 🆕 **Nouveaux prestataires** — derniers inscrits sur la plateforme\n"
            "3. 💡 **Recommandations pour toi** — services personnalisés selon ton profil\n"
            "4. 🏷️ **Catégories** — navigation par type de service\n\n"
            "Utilise la **barre de recherche** en haut pour trouver rapidement ce que tu cherches."
        ),
        "category": "general",
    },
    {
        "patterns": [
            r"tableau\s+de\s+bord", r"dashboard", r"mon\s+espace",
            r"espace\s+personnel", r"section\s+dashboard",
        ],
        "answer": (
            "📊 **Tableau de bord StudiServ :**\n\n"
            "Le tableau de bord te donne accès à toutes tes fonctionnalités depuis un seul endroit :\n\n"
            "**Côté Consommateur :**\n"
            "• 📦 Mes commandes (suivi, historique)\n"
            "• ⭐ Mes avis (évaluations laissées)\n"
            "• 💬 Messages (conversations)\n"
            "• 👤 Mon profil\n\n"
            "**Côté Prestataire :**\n"
            "• 📢 Mes services (gestion des annonces)\n"
            "• 📦 Commandes reçues\n"
            "• ⭐ Mes avis reçus\n"
            "• 📈 Statistiques (revenus simulés, performance)\n"
            "• 💬 Messages"
        ),
        "category": "general",
    },
    {
        "patterns": [
            r"système\s+de\s+recommandation", r"recommandations?\s+personnalisées?",
            r"comment\s+studiserv\s+(?:me\s+)?recommande", r"algorithme\s+reco",
        ],
        "answer": (
            "🤖 **Système de recommandation :**\n\n"
            "StudiServ utilise un moteur de recommandation intelligent basé sur :\n\n"
            "1. 📋 **Ton historique** de commandes passées\n"
            "2. 🔗 **Services similaires** à ceux que tu consultes\n"
            "3. ❤️ **Tes catégories préférées** (la plus fréquentée par toi)\n"
            "4. ⭐ **Popularité** des services (notes et nombre de commandes)\n\n"
            "Les recommandations apparaissent dans ton **tableau de bord** et sur la **page d'accueil**."
        ),
        "category": "general",
    },

    # ─── ADMINISTRATION ───────────────────────────────────────────────────────
    {
        "patterns": [
            r"administrateur", r"admin\b", r"rôle\s+admin",
            r"que\s+fait\s+l'admin", r"droits?\s+admin",
        ],
        "answer": (
            "👨‍💼 **Rôle de l'administrateur :**\n\n"
            "L'administrateur gère la plateforme et peut :\n\n"
            "• 👥 **Gérer les utilisateurs** : activer, désactiver, supprimer des comptes\n"
            "• 🪪 **Valider les cartes étudiantes** des prestataires\n"
            "• 📢 **Modérer les annonces** : valider ou supprimer les contenus signalés\n"
            "• ⭐ **Modérer les avis** : supprimer les avis abusifs\n"
            "• ⚖️ **Gérer les litiges** entre consommateurs et prestataires\n"
            "• 📊 **Surveiller les statistiques** globales de la plateforme"
        ),
        "category": "general",
    },

    # ─── TECHNIQUE ────────────────────────────────────────────────────────────
    {
        "patterns": [
            r"technologie", r"stack\s+technique", r"développé\s+avec",
            r"react", r"django", r"python", r"framework",
        ],
        "answer": (
            "⚙️ **Stack technique de StudiServ :**\n\n"
            "• **Frontend :** React.js (SPA)\n"
            "• **Backend :** Python avec Django\n"
            "• **API :** Django REST Framework (endpoints RESTful)\n"
            "• **Temps réel :** WebSockets via Django Channels (messagerie instantanée)\n"
            "• **Base de données :** MySQL / MariaDB\n"
            "• **Authentification :** JWT (JSON Web Tokens)\n"
            "• **Chatbot :** RAG avec LangChain + ChromaDB\n\n"
            "C'est une architecture **full-stack moderne** démontrant une marketplace complète."
        ),
        "category": "technical",
    },
    {
        "patterns": [
            r"messagerie\s+ne\s+fonctionne\s+pas", r"websocket\s+(?:error|problème)",
            r"message[s]?\s+ne\s+(?:s'envoient|arrivent)\s+pas",
            r"connexion\s+temps\s+réel",
        ],
        "answer": (
            "🔧 **Problème de messagerie temps réel :**\n\n"
            "Si la messagerie ne fonctionne pas :\n\n"
            "1. **Actualise la page** (F5 ou Ctrl+R)\n"
            "2. **Vérifie ta connexion internet**\n"
            "3. **Désactive les extensions** de navigateur (VPN, bloqueurs de pubs)\n"
            "4. **Essaie un autre navigateur** (Chrome ou Firefox recommandé)\n"
            "5. Si le problème persiste, le serveur WebSocket peut être temporairement indisponible\n\n"
            "📬 Tes messages sont conservés et livrés dès le rétablissement de la connexion."
        ),
        "category": "technical",
    },

    # ─── AIDE GÉNÉRALE ────────────────────────────────────────────────────────
    {
        "patterns": [
            r"aide", r"help\b", r"besoin\s+d'aide", r"assistance",
            r"comment\s+(?:fonctionne|marche|utiliser)", r"guide",
            r"tutoriel", r"expliquer", r"bonjour", r"salut",
        ],
        "answer": (
            "👋 **Bienvenue sur l'assistant StudiServ !**\n\n"
            "Je peux t'aider avec :\n\n"
            "• 🛒 **Passer une commande** sur un service\n"
            "• 📢 **Créer/publier une annonce** de service\n"
            "• 👤 **Gérer ton compte** (inscription, profil, carte étudiante)\n"
            "• 💬 **Utiliser la messagerie** interne\n"
            "• ⭐ **Laisser un avis** ou comprendre les badges\n"
            "• 🔍 **Rechercher des services** ou prestataires\n"
            "• ⚖️ **Ouvrir un litige** ou gérer une commande\n\n"
            "Pose-moi ta question et je t'aiderai ! 😊"
        ),
        "category": "general",
    },
    {
        "patterns": [
            r"email\s+universitaire", r"pourquoi\s+email\s+universitaire",
            r"email\s+obligatoire", r".edu\b", r"adresse\s+mail\s+étudiant",
        ],
        "answer": (
            "📧 **Pourquoi un email universitaire ?**\n\n"
            "StudiServ est réservé **exclusivement** à la communauté étudiante.\n"
            "L'email universitaire garantit que seuls les **vrais étudiants** peuvent s'inscrire.\n\n"
            "**Domaines acceptés :** `.edu`, `.ens.tn`, `.essai.tn`, et autres domaines universitaires tunisiens.\n\n"
            "C'est une mesure de sécurité pour préserver la **qualité** et l'**esprit de la communauté**."
        ),
        "category": "account",
    },
    {
        "patterns": [
            r"qui\s+a\s+(?:développé|créé)\s+studiserv", r"équipe\s+studiserv",
            r"développeurs?\s+studiserv", r"auteurs?\s+studiserv",
        ],
        "answer": (
            "👨‍💻 **Équipe StudiServ :**\n\n"
            "StudiServ a été développé par **3 étudiants** :\n"
            "• Eya Boiguerra\n"
            "• Amine Hasnaoui\n"
            "• Rayen Hammi\n\n"
            "**Encadrant :** Slim Abbes (SESAME)\n\n"
            "C'est un projet académique réalisé durant l'année universitaire **2025-2026**."
        ),
        "category": "general",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# MATCHER — Recherche dans la base de connaissances
# ═══════════════════════════════════════════════════════════════════════════════

def _find_best_match(question: str) -> dict | None:
    """
    Cherche la meilleure réponse dans la base de connaissances intégrée.
    Retourne l'entrée avec le plus de patterns matchés, ou None si aucun match.
    """
    q = (question or "").lower().strip()
    if not q:
        return None

    best_entry = None
    best_count = 0

    for entry in KNOWLEDGE_BASE:
        count = sum(1 for pat in entry["patterns"] if re.search(pat, q))
        if count > best_count:
            best_count = count
            best_entry = entry

    # Seuil minimum : au moins 1 pattern doit matcher
    return best_entry if best_count >= 1 else None


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMANDATION DE PRESTATAIRES
# ═══════════════════════════════════════════════════════════════════════════════

_RECO_PATTERNS = [
    r"recommand", r"conseill", r"sugg[eè]r", r"meilleur", r"top\b",
    r"quel\s+prestataire", r"quels\s+prestataires", r"qui\s+peut",
    r"trouver\s+un", r"besoin\s+d'un", r"cherche\s+un",
    r"recommend", r"best\s+provider", r"suggest",
]


def _wants_recommendation(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _RECO_PATTERNS)


def _format_providers(providers) -> str:
    if not providers:
        return (
            "Je n'ai pas encore trouvé de prestataire correspondant. "
            "Essaie une catégorie précise (ex. « maths », « design », « traduction »)."
        )
    lines = ["Voici des prestataires recommandés sur StudiServ :"]
    for i, p in enumerate(providers, 1):
        ref = getattr(p, "prestataire_id", None) or getattr(p, "id", None)
        note = (
            getattr(p, "score_global", None)
            or getattr(p, "note_moyenne", None)
            or getattr(p, "avg_score", None)
        )
        titre = getattr(p, "titre", None)
        label = f"Prestataire #{ref}" if ref else "Prestataire"
        extra = []
        if titre:
            extra.append(f"service « {titre} »")
        if note:
            try:
                extra.append(f"note {round(float(note), 1)}/5")
            except (TypeError, ValueError):
                pass
        suffix = f" — {', '.join(extra)}" if extra else ""
        lines.append(f"{i}. {label}{suffix}")
    lines.append("Ouvre la fiche d'un prestataire pour voir ses services et le contacter.")
    return "\n".join(lines)


def _recommend_providers(question: str, user=None, limit: int = 5) -> dict | None:
    try:
        from marketplace.recommendation_engine import (
            get_top_providers, get_recommendations_for_user,
        )
    except Exception as e:
        logger.warning("Moteur de reco indisponible: %s", e)
        return None

    providers = []
    try:
        if user is not None and getattr(user, "is_authenticated", False):
            providers = list(get_recommendations_for_user(user, limit=limit) or [])
    except Exception as e:
        logger.info("Reco perso échouée: %s", e)

    if not providers:
        try:
            providers = list(get_top_providers(limit=limit) or [])
        except TypeError:
            try:
                providers = list(get_top_providers() or [])[:limit]
            except Exception as e:
                logger.warning("get_top_providers a échoué: %s", e)
        except Exception as e:
            logger.warning("get_top_providers a échoué: %s", e)

    return {
        "answer": _format_providers(providers),
        "sources": [],
        "fallback": False,
        "intent": "recommendation",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RÉPONSE EXTRACTIVE (depuis ChromaDB si disponible)
# ═══════════════════════════════════════════════════════════════════════════════

def _extractive_answer(question: str, docs: list) -> str:
    if not docs:
        return (
            "Je n'ai pas trouvé d'information précise sur ce point dans ma base. "
            "Reformule ta question, ou consulte ton tableau de bord / contacte un administrateur."
        )
    best = docs[0][0]
    content = (getattr(best, "page_content", "") or "").strip()
    content = re.sub(r"^\s*(Question|Réponse|Reponse|Tags)\s*:\s*", "", content, flags=re.I | re.M)
    if len(content) > 900:
        content = content[:900].rsplit(" ", 1)[0] + "…"
    return content


def _try_chromadb_response(question: str) -> dict | None:
    """Tente une réponse via ChromaDB (ne bloque jamais si indisponible)."""
    try:
        from chatbot.rag_engine import retrieve_relevant_docs
        docs = retrieve_relevant_docs(question)
        if not docs:
            return None
        sources = []
        for doc, score in docs:
            md = getattr(doc, "metadata", {}) or {}
            sources.append({
                "faq_id": md.get("faq_id"),
                "title": md.get("title"),
                "category": md.get("category"),
                "relevance_score": round(float(score), 3),
            })
        # Tente d'abord le LLM
        try:
            from chatbot.rag_engine import build_rag_prompt, get_llm
            llm = get_llm()
            messages = build_rag_prompt(question, docs)
            response = llm.invoke(messages)
            answer = getattr(response, "content", None) or str(response)
            return {"answer": answer, "sources": sources, "fallback": False, "intent": "rag_llm"}
        except Exception:
            pass
        # Fallback extractif
        answer = _extractive_answer(question, docs)
        return {"answer": answer, "sources": sources, "fallback": True, "intent": "rag_extractive"}
    except Exception as e:
        logger.debug("ChromaDB indisponible: %s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def get_chatbot_response(question, conversation_history=None, session_key=None, user=None):
    """
    Pipeline de chatbot robuste pour StudiServ.

    Ordre de priorité :
    1. Recommandation de prestataires (si intention détectée)
    2. Base de connaissances intégrée (répond immédiatement, sans LLM)
    3. ChromaDB + LLM (si disponibles)
    4. Message de fallback gracieux

    Retour: { 'answer', 'sources', 'fallback', 'intent'? }
    """
    if not question or not question.strip():
        return {
            "answer": "Pose-moi une question sur StudiServ et je ferai de mon mieux pour t'aider ! 😊",
            "sources": [],
            "fallback": False,
        }

    # 1) Intention de recommandation
    if _wants_recommendation(question):
        reco = _recommend_providers(question, user=user)
        if reco is not None:
            return reco

    # 2) Base de connaissances intégrée — toujours disponible, répond instantanément
    match = _find_best_match(question)
    if match:
        return {
            "answer": match["answer"],
            "sources": [],
            "fallback": False,
            "intent": "knowledge_base",
        }

    # 3) ChromaDB + LLM en option
    chroma_result = _try_chromadb_response(question)
    if chroma_result:
        return chroma_result

    # 4) Fallback gracieux
    return {
        "answer": (
            "🤔 Je n'ai pas trouvé de réponse précise à ta question dans ma base de connaissances.\n\n"
            "Tu peux essayer de :\n"
            "• Reformuler ta question différemment\n"
            "• Consulter ton **tableau de bord** pour les informations sur tes commandes\n"
            "• Contacter directement le prestataire via la **messagerie**\n"
            "• Ouvrir un **litige** si tu as un problème avec une commande\n\n"
            "Exemples de questions que je peux répondre :\n"
            "• « Comment passer une commande ? »\n"
            "• « Comment créer une annonce ? »\n"
            "• « Comment obtenir le badge de confiance ? »"
        ),
        "sources": [],
        "fallback": True,
        "intent": "no_match",
    }


# Alias rétro-compatible
get_chatbot_response_robust = get_chatbot_response
