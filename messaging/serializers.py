# apps/messaging/serializers.py
# REMPLACEMENT COMPLET — version ANONYMISÉE.
# Les participants ne voient plus le nom/email de l'autre : uniquement un
# identifiant pseudonymisé stable ("Prestataire #12" / "Étudiant #5" /
# "Utilisateur #7"). Corrige aussi un bug latent : l'ancien serializer
# exposait un champ `avatar` inexistant sur le modèle User par défaut,
# et `order` au lieu de `order_id`.

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Notification

User = get_user_model()


def anon_handle(user):
    """
    Pseudonyme stable et anonyme pour un utilisateur, basé sur son rôle + id.
    N'expose jamais le nom réel ni l'email.
    """
    if user is None:
        return "Utilisateur"
    try:
        role = user.compte.utilisateur.role  # RoleUser: 'PRESTATAIRE'/'CONSOMMATEUR'/'ADMIN'
        role = (role or "").upper()
    except Exception:
        role = ""
    if "PRESTA" in role:
        label = "Prestataire"
    elif "CONSO" in role:
        label = "Étudiant"
    elif "ADMIN" in role:
        label = "Admin"
    else:
        label = "Utilisateur"
    return f"{label} #{user.pk}"


class UserBriefSerializer(serializers.ModelSerializer):
    """Identité ANONYME d'un participant."""
    handle = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "handle"]   # ← plus de full_name, plus d'email, plus d'avatar

    def get_handle(self, obj):
        return anon_handle(obj)


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_handle = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "sender_id", "sender_handle",
            "message_type", "content", "file", "is_read", "created_at",
        ]
        read_only_fields = ["sender_id", "sender_handle", "is_read", "created_at"]

    def get_sender_handle(self, obj):
        return anon_handle(obj.sender)


class FileMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "message_type", "content", "file", "created_at"]

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Fichier trop volumineux (max 10 MB).")
        allowed_types = ["application/pdf", "image/jpeg", "image/png",
                         "image/gif", "image/webp", "application/zip",
                         "application/x-zip-compressed"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé.")
        return value


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserBriefSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "participants", "other_participant",
            "last_message", "unread_count", "order_id",   # ← order_id (réel)
            "is_archived", "created_at", "updated_at",
        ]

    def get_last_message(self, obj):
        msg = obj.messages.last()
        return MessageSerializer(msg).data if msg else None

    def get_unread_count(self, obj):
        user = self.context["request"].user
        notif = obj.notifications.filter(user=user).first()
        return notif.unread_count if notif else 0

    def get_other_participant(self, obj):
        user = self.context["request"].user
        other = obj.get_other_participant(user)
        return UserBriefSerializer(other).data if other else None
