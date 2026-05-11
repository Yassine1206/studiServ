from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Compte, Utilisateur, Consommateur, Prestataire,
    Profil, Service, Demande, Recommendation, RoleUser, EtatCompte,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ─── Auth ─────────────────────────────────────────────────────────────────────

class SignUpSerializer(serializers.Serializer):
    first_name   = serializers.CharField(max_length=100)
    last_name    = serializers.CharField(max_length=100)
    email        = serializers.EmailField()
    password     = serializers.CharField(write_only=True, validators=[validate_password])
    role         = serializers.ChoiceField(choices=["consumer", "provider"])
    # Optionnels — requis seulement pour les prestataires (validé dans validate())
    university   = serializers.CharField(max_length=200, required=False, allow_blank=True)
    student_card = serializers.FileField(required=False)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value.lower()

    def validate(self, data):
        if data["role"] == "provider":
            if not data.get("university"):
                raise serializers.ValidationError(
                    {"university": "L'université est requise pour les prestataires."}
                )
            if "student_card" not in data:
                raise serializers.ValidationError(
                    {"student_card": "La carte étudiante est requise pour les prestataires."}
                )
        return data

    def create(self, validated_data):
        role_str     = validated_data.pop("role")
        university   = validated_data.pop("university", "")
        student_card = validated_data.pop("student_card", None)

        # 1. Créer le User Django
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )

        # 2. Créer le Compte
        role_map = {
            "consumer": RoleUser.CONSOMMATEUR,
            "provider": RoleUser.PRESTATAIRE,
        }
        compte = Compte.objects.create(
            user=user,
            etat=EtatCompte.ACTIF if role_str == "consumer" else EtatCompte.EN_ATTENTE,
        )

        # 3. Créer l'Utilisateur
        utilisateur = Utilisateur.objects.create(
            compte=compte,
            nom=validated_data["last_name"],
            prenom=validated_data["first_name"],
            role=role_map[role_str],
        )

        # 4. Créer le Profil
        Profil.objects.create(utilisateur=utilisateur, universite=university)

        # 5. Créer le profil de rôle
        if role_str == "consumer":
            Consommateur.objects.create(utilisateur=utilisateur)
        else:
            prestataire = Prestataire.objects.create(utilisateur=utilisateur)
            if student_card:
                prestataire.carte_etudiant = student_card
                prestataire.save()

        return user

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ─── Profil ───────────────────────────────────────────────────────────────────

class ProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profil
        fields = ["photo", "biographie", "note_moyenne",
                  "score_reputation", "nb_commandes_total",
                  "universite", "telephone"]


class UserProfileSerializer(serializers.Serializer):
    """Retourne toutes les infos du profil connecté."""
    id = serializers.IntegerField(source="pk")
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.SerializerMethodField()
    profil = serializers.SerializerMethodField()

    def get_role(self, user):
        try:
            role = user.compte.utilisateur.role
            role_map = {
                RoleUser.ADMIN: "admin",
                RoleUser.CONSOMMATEUR: "consumer",
                RoleUser.PRESTATAIRE: "provider",
            }
            return role_map.get(role, "consumer")
        except Exception:
            return "consumer"

    def get_profil(self, user):
        try:
            profil = user.compte.utilisateur.profil
            return ProfilSerializer(profil).data
        except Exception:
            return {}


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    biographie = serializers.CharField(required=False, allow_blank=True)
    universite = serializers.CharField(max_length=200, required=False, allow_blank=True)
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def update(self, user, validated_data):
        if "first_name" in validated_data:
            user.first_name = validated_data["first_name"]
        if "last_name" in validated_data:
            user.last_name = validated_data["last_name"]
        user.save()

        try:
            utilisateur = user.compte.utilisateur
            if "first_name" in validated_data:
                utilisateur.prenom = validated_data["first_name"]
            if "last_name" in validated_data:
                utilisateur.nom = validated_data["last_name"]
            utilisateur.save()

            profil = utilisateur.profil
            for field in ["biographie", "universite", "telephone"]:
                if field in validated_data:
                    setattr(profil, field, validated_data[field])
            profil.save()
        except Exception:
            pass

        return user


# ─── Services ─────────────────────────────────────────────────────────────────

class ServiceSerializer(serializers.ModelSerializer):
    provider_name = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "titre", "description", "categorie",
            "prix", "delai_livraison", "actif",
            "provider_name", "rating", "reviews_count",
            "date_creation",
        ]

    def get_provider_name(self, obj):
        return str(obj.prestataire.utilisateur)

    def get_rating(self, obj):
        recs = obj.recommendations.all()
        if not recs.exists():
            return 0
        return round(sum(r.score for r in recs) / recs.count(), 1)

    def get_reviews_count(self, obj):
        return obj.recommendations.count()


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["titre", "description", "categorie", "prix", "delai_livraison"]

    def create(self, validated_data):
        user = self.context["request"].user
        prestataire = user.compte.utilisateur.prestataire
        return Service.objects.create(prestataire=prestataire, **validated_data)


# ─── Demandes ─────────────────────────────────────────────────────────────────

class DemandeSerializer(serializers.ModelSerializer):
    service_titre = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Demande
        fields = [
            "id", "titre", "description", "statut",
            "date_creation", "service_titre", "provider_name",
        ]

    def get_service_titre(self, obj):
        return obj.service.titre if obj.service else None

    def get_provider_name(self, obj):
        if obj.service:
            return str(obj.service.prestataire.utilisateur)
        return None


class DemandeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = ["titre", "description", "service"]

    def create(self, validated_data):
        user = self.context["request"].user
        consommateur = user.compte.utilisateur.consommateur
        return Demande.objects.create(consommateur=consommateur, **validated_data)


# ─── Recommendations ──────────────────────────────────────────────────────────

class RecommendationSerializer(serializers.ModelSerializer):
    service_titre = serializers.SerializerMethodField()
    consumer_name = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id", "commentaire", "score", "date_creation",
            "service_titre", "consumer_name",
        ]

    def get_service_titre(self, obj):
        return obj.service.titre

    def get_consumer_name(self, obj):
        return str(obj.consommateur.utilisateur)


# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    joined = serializers.DateTimeField(source="date_joined", format="%Y-%m-%d")
    card_status = serializers.SerializerMethodField()

    def get_name(self, user):
        return user.get_full_name() or user.username

    def get_role(self, user):
        try:
            role = user.compte.utilisateur.role
            return role.lower()
        except Exception:
            return "inconnu"

    def get_status(self, user):
        try:
            etat = user.compte.etat
            return etat.lower()
        except Exception:
            return "inconnu"

    def get_card_status(self, user):
        try:
            prestataire = user.compte.utilisateur.prestataire
            return "verified" if prestataire.carte_verifiee else "pending"
        except Exception:
            return "n/a"
