# apps/messaging/consumers.py
# M4 — Consumer WebSocket : chat temps réel

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Notification

User = get_user_model()


def _anon_handle(user):
    try:
        role = (user.compte.utilisateur.role or "").upper()
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


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer pour le chat temps réel.

    URL: ws://host/ws/chat/<conversation_id>/
    Requiert JWT dans le header ou query param ?token=...
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Vérifier que l'utilisateur est bien participant
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        is_participant = await self.check_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        # Rejoindre le groupe de la conversation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Marquer les messages non lus comme lus à la connexion
        await self.mark_messages_read()

        # Envoyer l'historique des 50 derniers messages
        history = await self.get_message_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': history
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Réception d'un message depuis le client."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'text')

        if msg_type == 'text':
            content = data.get('content', '').strip()
            if not content:
                return
            message = await self.save_message(content, 'text')
            await self.broadcast_message(message)

        elif msg_type == 'typing':
            # Notifier l'autre participant que l'utilisateur tape
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': _anon_handle(self.user),
                    'is_typing': data.get('is_typing', True)
                }
            )

        elif msg_type == 'read':
            # Marquer comme lu
            await self.mark_messages_read()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'user_id': self.user.id,
                }
            )

    async def chat_message(self, event):
        """Diffuser un message au groupe."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Diffuser l'indicateur de frappe."""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def read_receipt(self, event):
        """Confirmer la lecture."""
        await self.send(text_data=json.dumps({
            'type': 'read',
            'user_id': event['user_id']
        }))

    # ── Helpers DB (sync → async) ─────────────────────────────────────────────

    @database_sync_to_async
    def check_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content, msg_type='text'):
        conv = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conv,
            sender=self.user,
            message_type=msg_type,
            content=content
        )
        # Mettre à jour updated_at de la conversation
        conv.save(update_fields=['updated_at'])
        # Incrémenter la notification pour l'autre participant
        for participant in conv.participants.exclude(pk=self.user.pk):
            Notification.objects.update_or_create(
                user=participant,
                conversation=conv,
                defaults={},
            )
            Notification.objects.filter(
                user=participant, conversation=conv
            ).update(unread_count=models.F('unread_count') + 1)
        return msg

    @database_sync_to_async
    def mark_messages_read(self):
        Message.objects.filter(
            conversation_id=self.conversation_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)
        Notification.objects.filter(
            user=self.user,
            conversation_id=self.conversation_id
        ).update(unread_count=0)

    @database_sync_to_async
    def get_message_history(self):
        messages = Message.objects.filter(
            conversation_id=self.conversation_id
        ).select_related('sender').order_by('-created_at')[:50]
        return [
            {
                'id': m.id,
                'sender_id': m.sender.id,
                'sender_handle': _anon_handle(m.sender),
                'content': m.content,
                'message_type': m.message_type,
                'file_url': m.file_url,
                'is_read': m.is_read,
                'created_at': m.created_at.isoformat(),
            }
            for m in reversed(list(messages))
        ]

    async def broadcast_message(self, message):
        """Envoyer le message à tous les participants connectés."""
        from django.contrib.auth import get_user_model
        msg_data = {
            'id': message.id,
            'sender_id': self.user.id,
            'sender_handle': _anon_handle(self.user),
            'content': message.content,
            'message_type': message.message_type,
            'file_url': message.file_url,
            'is_read': message.is_read,
            'created_at': message.created_at.isoformat(),
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': msg_data
            }
        )


# Import manquant pour le F()
from django.db import models
