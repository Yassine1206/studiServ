# apps/messaging/views.py
# M4 — REST endpoints pour la messagerie

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Notification
from .serializers import ConversationSerializer, MessageSerializer, FileMessageSerializer

User = get_user_model()


class ConversationListView(generics.ListAPIView):
    """
    GET /api/messaging/conversations/
    Liste toutes les conversations de l'utilisateur connecté.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants', 'messages', 'notifications')

        archived = self.request.query_params.get('archived', 'false')
        qs = qs.filter(is_archived=(archived == 'true'))
        return qs


class ConversationCreateView(generics.CreateAPIView):
    """
    POST /api/messaging/conversations/create/
    Créer ou retrouver une conversation avec un autre utilisateur.
    Body: { "recipient_id": <int>, "order_id": <int|null> }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        recipient_id = request.data.get('recipient_id')
        order_id = request.data.get('order_id')

        if not recipient_id:
            return Response({'error': 'recipient_id requis.'}, status=400)

        recipient = get_object_or_404(User, pk=recipient_id)
        if recipient == request.user:
            return Response({'error': 'Impossible de créer une conversation avec soi-même.'}, status=400)

        # Chercher une conversation existante entre ces deux utilisateurs
        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        )
        if order_id:
            existing = existing.filter(order_id=order_id)

        if existing.exists():
            conv = existing.first()
            created = False
        else:
            conv = Conversation.objects.create(order_id=order_id)
            conv.participants.add(request.user, recipient)
            created = True

        serializer = ConversationSerializer(conv, context={'request': request})
        return Response(serializer.data, status=201 if created else 200)


class ConversationDetailView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/messaging/conversations/<id>/  — détail + messages
    PATCH /api/messaging/conversations/<id>/  — archiver
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        conv = get_object_or_404(
            Conversation, pk=self.kwargs['pk'], participants=self.request.user
        )
        return conv

    def patch(self, request, *args, **kwargs):
        conv = self.get_object()
        archive = request.data.get('is_archived')
        if archive is not None:
            conv.is_archived = archive
            conv.save(update_fields=['is_archived'])
        return Response(ConversationSerializer(conv, context={'request': request}).data)


class MessageListView(generics.ListAPIView):
    """
    GET /api/messaging/conversations/<id>/messages/?page=1
    Historique paginé des messages (50 par page).
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv = get_object_or_404(
            Conversation, pk=self.kwargs['pk'], participants=self.request.user
        )
        # Marquer comme lus
        Message.objects.filter(
            conversation=conv, is_read=False
        ).exclude(sender=self.request.user).update(is_read=True)
        Notification.objects.filter(
            user=self.request.user, conversation=conv
        ).update(unread_count=0)
        return conv.messages.select_related('sender')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_file_message(request, pk):
    """
    POST /api/messaging/conversations/<id>/upload/
    Envoyer un fichier (PDF, image) dans une conversation.
    """
    conv = get_object_or_404(
        Conversation, pk=pk, participants=request.user
    )
    serializer = FileMessageSerializer(data=request.data)
    if serializer.is_valid():
        file = request.FILES.get('file')
        msg_type = 'image' if file and file.content_type.startswith('image/') else 'file'
        msg = Message.objects.create(
            conversation=conv,
            sender=request.user,
            message_type=msg_type,
            content=request.data.get('content', ''),
            file=file
        )
        conv.save(update_fields=['updated_at'])
        return Response(MessageSerializer(msg).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notifications_count(request):
    """
    GET /api/messaging/notifications/
    Nombre total de messages non lus toutes conversations confondues.
    """
    from django.db.models import Sum
    total = Notification.objects.filter(
        user=request.user
    ).aggregate(total=Sum('unread_count'))['total'] or 0
    return Response({'unread_total': total})
