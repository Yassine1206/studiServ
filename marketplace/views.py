from django.apps import apps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import EmailAuthForm, InscriptionCompteForm
from .models import Compte, Consommateur, EtatCompte, Prestataire, Profil, RoleUser, Utilisateur


MODEL_NAMES = [
    "Compte",
    "Utilisateur",
    "Consommateur",
    "Prestataire",
    "Profil",
    "Competence",
    "Service",
    "Demande",
    "Discussion",
    "Recommendation",
]

MODEL_LABELS = {
    "compte": "Comptes",
    "utilisateur": "Utilisateurs",
    "consommateur": "Consommateurs",
    "prestataire": "Prestataires",
    "profil": "Profils",
    "competence": "Competences",
    "service": "Services",
    "demande": "Demandes",
    "discussion": "Discussions",
    "recommendation": "Recommendations",
}

DASHBOARD_CONFIG = {
    "etudiant": {
        "title": "Espace etudiant",
        "subtitle": "Publiez vos services, suivez les demandes et consultez les avis recus.",
        "primary_action": "Publier un service",
        "primary_url": "marketplace:service_create",
        "cards": [
            {"label": "Mes annonces", "slug": "service", "tone": "mint"},
            {"label": "Demandes recues", "slug": "demande", "tone": "blue"},
            {"label": "Discussions", "slug": "discussion", "tone": "coral"},
            {"label": "Avis et recommandations", "slug": "recommendation", "tone": "gold"},
        ],
    },
    "prestatire": {
        "title": "Espace prestataire",
        "subtitle": "Recherchez un service, suivez son evolution, puis ajoutez une note ou un avis.",
        "primary_action": "Publier un besoin",
        "primary_url": "marketplace:demande_create",
        "cards": [
            {"label": "Services disponibles", "slug": "service", "tone": "mint"},
            {"label": "Mes demandes", "slug": "demande", "tone": "blue"},
            {"label": "Conversations", "slug": "discussion", "tone": "coral"},
            {"label": "Ajouter un avis", "slug": "recommendation", "tone": "gold"},
        ],
    },
}

ENTITY_CONFIG = {
    "compte": {
        "singular": "Compte",
        "label": "Comptes",
        "description": "Acces de connexion et etat du compte.",
        "tone": "mint",
    },
    "utilisateur": {
        "singular": "Utilisateur",
        "label": "Utilisateurs",
        "description": "Identite, role et rattachement a un compte.",
        "tone": "blue",
    },
    "consommateur": {
        "singular": "Consommateur",
        "label": "Consommateurs",
        "description": "Personnes qui demandent, achetent et evaluent les services.",
        "tone": "coral",
    },
    "prestataire": {
        "singular": "Prestataire",
        "label": "Prestataires",
        "description": "Etudiants qui publient des annonces et traitent les demandes.",
        "tone": "violet",
    },
    "profil": {
        "singular": "Profil",
        "label": "Profils",
        "description": "Photo, biographie, note moyenne et reputation.",
        "tone": "gold",
    },
    "competence": {
        "singular": "Competence",
        "label": "Competences",
        "description": "Matieres et domaines de service proposes.",
        "tone": "slate",
    },
    "service": {
        "singular": "Service",
        "label": "Services",
        "description": "Annonces publiees par les etudiants prestataires.",
        "tone": "mint",
    },
    "demande": {
        "singular": "Demande",
        "label": "Demandes",
        "description": "Besoins exprimes par les consommateurs.",
        "tone": "blue",
    },
    "discussion": {
        "singular": "Discussion",
        "label": "Discussions",
        "description": "Conversations entre consommateurs et prestataires.",
        "tone": "coral",
    },
    "recommendation": {
        "singular": "Recommendation",
        "label": "Recommendations",
        "description": "Avis, notes et recommandations sur les services.",
        "tone": "gold",
    },
}


def get_model(slug):
    model = apps.get_model("marketplace", slug)
    if model is None:
        raise LookupError(slug)
    return model


def get_entity_config(slug):
    config = ENTITY_CONFIG[slug].copy()
    config["slug"] = slug
    config["initial"] = config["singular"][0]
    return config


def get_nav_items():
    return [get_entity_config(name.lower()) for name in MODEL_NAMES]


def format_field_name(field):
    return field.verbose_name.replace("_", " ").title()


def format_value(value):
    if value is None or value == "":
        return "-"
    return value


def get_display_fields(model, obj, limit=None):
    fields = []
    for field in model._meta.fields:
        value = getattr(obj, field.name)
        if limit and field.name == "id":
            continue
        fields.append((format_field_name(field), format_value(value)))
        if limit and len(fields) >= limit:
            break
    return fields


def get_rows(model, objects):
    return [
        {
            "object": obj,
            "summary": get_display_fields(model, obj, limit=3),
        }
        for obj in objects
    ]


def get_form_class(model):
    base_form = modelform_factory(model, fields="__all__")

    class StyledForm(base_form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields.values():
                existing_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_class} form-control".strip()
                field.widget.attrs.setdefault("placeholder", field.label)

    return StyledForm


# ──────────────────────────────────────────────
#  Helpers d'authentification
# ──────────────────────────────────────────────

def _get_role(user):
    """Retourne le role de l'utilisateur connecte, ou None."""
    try:
        return user.utilisateur.role
    except Utilisateur.DoesNotExist:
        return None


def _redirect_after_login(user):
    """Redirige selon le role apres connexion."""
    role = _get_role(user)
    if role == RoleUser.PRESTATAIRE:
        return redirect("marketplace:prestatire_dashboard")
    if role == RoleUser.CONSOMMATEUR:
        return redirect("marketplace:etudiant_dashboard")
    return redirect("marketplace:index")


def require_role(*roles):
    """Decorateur qui restreint une vue a certains roles."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("marketplace:login")
            role = _get_role(request.user)
            if role not in roles and not request.user.is_staff:
                messages.error(request, "Acces non autorise pour votre role.")
                return redirect("marketplace:index")
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


# ──────────────────────────────────────────────
#  Connexion (par email)
# ──────────────────────────────────────────────

class MainLoginView(LoginView):
    template_name = "marketplace/login.html"
    authentication_form = EmailAuthForm
    redirect_authenticated_user = True
    extra_context = {
        "role_title": "Connexion",
        "role_name": "StudiServ",
        "role_description": "Connectez-vous avec votre adresse e-mail pour acceder a votre espace.",
        "show_register_link": True,
    }

    def get_success_url(self):
        return self.get_redirect_url() or self._get_role_url()

    def _get_role_url(self):
        role = _get_role(self.request.user)
        if role == RoleUser.PRESTATAIRE:
            return reverse_lazy("marketplace:prestatire_dashboard")
        return reverse_lazy("marketplace:etudiant_dashboard")


class StudentLoginView(LoginView):
    template_name = "marketplace/login.html"
    authentication_form = EmailAuthForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("marketplace:etudiant_dashboard")
    extra_context = {
        "role_title": "Connexion consommateur",
        "role_name": "Consommateur",
        "role_description": "Accedez aux services disponibles, suivez vos demandes et ajoutez vos evaluations.",
        "show_register_link": True,
    }


class ProviderLoginView(LoginView):
    template_name = "marketplace/login.html"
    authentication_form = EmailAuthForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("marketplace:prestatire_dashboard")
    extra_context = {
        "role_title": "Connexion prestataire",
        "role_name": "Prestataire",
        "role_description": "Accedez a vos annonces, demandes, conversations, avis et recommandations.",
        "show_register_link": True,
    }


# ──────────────────────────────────────────────
#  Inscription
# ──────────────────────────────────────────────

def inscription(request):
    """Cree un User Django + Compte + Utilisateur + Consommateur/Prestataire + Profil."""
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)

    form = InscriptionCompteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        email = data["email"]
        password = data["mot_de_passe"]
        role = data["role"]

        # 1. User Django (gere la session et le hachage)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=data["prenom"],
            last_name=data["nom"],
        )

        # 2. Compte (modele metier existant)
        compte = Compte.objects.create(
            email=email,
            mot_de_passe=user.password,   # hache par Django
            etat=EtatCompte.ACTIF,
        )

        # 3. Utilisateur
        utilisateur = Utilisateur.objects.create(
            user=user,
            compte=compte,
            nom=data["nom"],
            prenom=data["prenom"],
            role=role,
        )

        # 4. Profil
        Profil.objects.create(utilisateur=utilisateur)

        # 5. Role specifique
        if role == RoleUser.PRESTATAIRE:
            Prestataire.objects.create(
                utilisateur=utilisateur,
                carte_etudiant=data.get("carte_etudiant", ""),
            )
        else:
            Consommateur.objects.create(utilisateur=utilisateur)

        # 6. Connexion automatique
        login(request, user, backend="marketplace.backends.EmailBackend")
        messages.success(request, f"Bienvenue {data['prenom']} ! Votre compte a ete cree avec succes.")
        return _redirect_after_login(user)

    return render(
        request,
        "marketplace/inscription.html",
        {
            "form": form,
            "nav_items": get_nav_items(),
        },
    )


# ──────────────────────────────────────────────
#  Deconnexion
# ──────────────────────────────────────────────

def deconnexion(request):
    logout(request)
    messages.info(request, "Vous avez ete deconnecte.")
    return redirect("marketplace:index")


def get_dashboard_context(role):
    config = DASHBOARD_CONFIG[role].copy()
    cards = []
    for card in config["cards"]:
        model = get_model(card["slug"])
        entity = get_entity_config(card["slug"])
        cards.append(
            {
                "label": card["label"],
                "slug": card["slug"],
                "tone": card["tone"],
                "initial": entity["initial"],
                "count": model.objects.count(),
                "description": entity["description"],
            }
        )
    config["cards"] = cards
    return config


@require_role(RoleUser.CONSOMMATEUR)
def etudiant_dashboard(request):
    utilisateur = getattr(request.user, "utilisateur", None)
    return render(
        request,
        "marketplace/dashboard.html",
        {
            "dashboard": get_dashboard_context("etudiant"),
            "nav_items": get_nav_items(),
            "utilisateur": utilisateur,
        },
    )


@require_role(RoleUser.PRESTATAIRE)
def prestatire_dashboard(request):
    utilisateur = getattr(request.user, "utilisateur", None)
    return render(
        request,
        "marketplace/dashboard.html",
        {
            "dashboard": get_dashboard_context("prestatire"),
            "nav_items": get_nav_items(),
            "utilisateur": utilisateur,
        },
    )


def index(request):
    cards = []
    counts = {}
    for name in MODEL_NAMES:
        model = get_model(name)
        slug = name.lower()
        count = model.objects.count()
        counts[slug] = count
        cards.append(
            {
                "slug": slug,
                "label": ENTITY_CONFIG[slug]["label"],
                "singular": ENTITY_CONFIG[slug]["singular"],
                "description": ENTITY_CONFIG[slug]["description"],
                "tone": ENTITY_CONFIG[slug]["tone"],
                "initial": ENTITY_CONFIG[slug]["singular"][0],
                "count": count,
            }
        )
    dashboard_stats = [
        {"label": "Services publies", "value": counts["service"]},
        {"label": "Demandes ouvertes", "value": counts["demande"]},
        {"label": "Avis et notes", "value": counts["recommendation"]},
        {"label": "Utilisateurs", "value": counts["utilisateur"]},
    ]
    quick_actions = [
        {
            "label": "Publier un service",
            "description": "Creer une annonce pour une matiere ou un domaine.",
            "url_name": "marketplace:service_create",
            "tone": "mint",
        },
        {
            "label": "Publier un besoin",
            "description": "Ajouter une demande de service cote consommateur.",
            "url_name": "marketplace:demande_create",
            "tone": "blue",
        },
        {
            "label": "Ajouter un avis",
            "description": "Noter un service et laisser une recommandation.",
            "url_name": "marketplace:recommendation_create",
            "tone": "gold",
        },
        {
            "label": "Gerer les utilisateurs",
            "description": "Administrer les comptes, roles et profils.",
            "url_name": "marketplace:utilisateur_list",
            "tone": "violet",
        },
    ]
    return render(
        request,
        "marketplace/index.html",
        {
            "cards": cards,
            "dashboard_stats": dashboard_stats,
            "quick_actions": quick_actions,
            "nav_items": get_nav_items(),
        },
    )


def entity_list(request, model_slug):
    model = get_model(model_slug)
    objects = model.objects.all()
    return render(
        request,
        "marketplace/entity_list.html",
        {
            "model_slug": model_slug,
            "model_label": ENTITY_CONFIG[model_slug]["label"],
            "entity": get_entity_config(model_slug),
            "objects": objects,
            "rows": get_rows(model, objects),
            "total_count": objects.count(),
            "nav_items": get_nav_items(),
        },
    )


def entity_detail(request, model_slug, pk):
    model = get_model(model_slug)
    obj = get_object_or_404(model, pk=pk)
    fields = get_display_fields(model, obj)
    many_to_many = [
        (format_field_name(field), field.value_from_object(obj))
        for field in model._meta.many_to_many
    ]
    return render(
        request,
        "marketplace/entity_detail.html",
        {
            "model_slug": model_slug,
            "model_label": ENTITY_CONFIG[model_slug]["label"],
            "entity": get_entity_config(model_slug),
            "object": obj,
            "fields": fields,
            "many_to_many": many_to_many,
            "nav_items": get_nav_items(),
        },
    )


def entity_create(request, model_slug):
    model = get_model(model_slug)
    form_class = get_form_class(model)
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Element ajoute avec succes.")
        return redirect(obj.get_absolute_url())
    return render(
        request,
        "marketplace/entity_form.html",
        {
            "model_slug": model_slug,
            "model_label": ENTITY_CONFIG[model_slug]["label"],
            "entity": get_entity_config(model_slug),
            "form": form,
            "action": "Ajouter",
            "nav_items": get_nav_items(),
        },
    )


def entity_update(request, model_slug, pk):
    model = get_model(model_slug)
    obj = get_object_or_404(model, pk=pk)
    form_class = get_form_class(model)
    form = form_class(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Element modifie avec succes.")
        return redirect(obj.get_absolute_url())
    return render(
        request,
        "marketplace/entity_form.html",
        {
            "model_slug": model_slug,
            "model_label": ENTITY_CONFIG[model_slug]["label"],
            "entity": get_entity_config(model_slug),
            "form": form,
            "action": "Modifier",
            "object": obj,
            "nav_items": get_nav_items(),
        },
    )


def entity_delete(request, model_slug, pk):
    model = get_model(model_slug)
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Element supprime avec succes.")
        return redirect("marketplace:%s_list" % model_slug)
    return render(
        request,
        "marketplace/entity_confirm_delete.html",
        {
            "model_slug": model_slug,
            "model_label": ENTITY_CONFIG[model_slug]["label"],
            "entity": get_entity_config(model_slug),
            "object": obj,
            "nav_items": get_nav_items(),
        },
    )
