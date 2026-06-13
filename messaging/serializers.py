# apps/messaging/serializers.py

from rest_framework import serializers
from .models import Conversation, Message, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'avatar']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBriefSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'message_type', 'content', 'file', 'is_read', 'created_at']
        read_only_fields = ['sender', 'is_read', 'created_at']


class FileMessageSerializer(serializers.ModelSerializer):
    """Sérialiseur spécial pour l'upload de fichiers via REST."""
    class Meta:
        model = Message
        fields = ['id', 'message_type', 'content', 'file', 'created_at']

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Fichier trop volumineux (max 10 MB).")
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé (PDF, JPEG, PNG, GIF, WEBP).")
        return value


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserBriefSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'other_participant',
            'last_message', 'unread_count', 'order',
            'is_archived', 'created_at', 'updated_at'
        ]

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return MessageSerializer(msg).data
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        notif = obj.notifications.filter(user=user).first()
        return notif.unread_count if notif else 0

    def get_other_participant(self, obj):
        user = self.context['request'].user
        other = obj.get_other_participant(user)
        return UserBriefSerializer(other).data if other else None
