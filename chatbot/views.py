# apps/chatbot/views.py
# M9 — API endpoints du chatbot RAG

import uuid
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import FAQDocument, ChatSession, ChatMessage
from .rag_engine import get_chatbot_response, index_faq_documents


# ─────────────────────────────────────────────────────────────────────────────
# Chatbot — Endpoint principal
# ─────────────────────────────────────────────────────────────────────────────

class ChatView(APIView):
    """
    POST /api/chatbot/chat/
    Envoyer un message et recevoir une réponse du chatbot RAG.

    Body: {
        "message": "Comment créer une annonce ?",
        "session_key": "uuid-optionnel"  ← pour maintenir l'historique
    }
    
    Réponse: {
        "answer": "Pour créer une annonce...",
        "session_key": "...",
        "sources": [...],
        "history": [...]
    }
    """
    permission_classes = [permissions.AllowAny]  # Accessible aux non-connectés aussi

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Le message ne peut pas être vide.'}, status=400)

        if len(message) > 1000:
            return Response({'error': 'Message trop long (max 1000 caractères).'}, status=400)

        # Récupérer ou créer la session
        session_key = request.data.get('session_key')
        if not session_key:
            session_key = str(uuid.uuid4())

        session, _ = ChatSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user': request.user if request.user.is_authenticated else None
            }
        )

        # Historique de la session (5 derniers échanges pour le contexte)
        recent_messages = session.messages.order_by('-created_at')[:10]
        history = [
            {'role': m.role, 'content': m.content}
            for m in reversed(list(recent_messages))
        ]

        # Appel au moteur RAG
        result = get_chatbot_response(
            question=message,
            conversation_history=history,
            session_key=session_key
        )

        # Sauvegarder la question et la réponse
        ChatMessage.objects.create(
            session=session, role='user', content=message
        )
        bot_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=result['answer'],
            sources_used=[s.get('faq_id') for s in result.get('sources', []) if s.get('faq_id')]
        )

        # Mettre à jour la session
        session.save(update_fields=['updated_at'])
        if request.user.is_authenticated and not session.user:
            session.user = request.user
            session.save(update_fields=['user'])

        return Response({
            'answer': result['answer'],
            'session_key': session_key,
            'sources': result.get('sources', []),
            'fallback': result.get('fallback', False),
            'message_id': bot_msg.id,
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def chat_history(request, session_key):
    """
    GET /api/chatbot/history/<session_key>/
    Récupère l'historique d'une session.
    """
    session = get_object_or_404(ChatSession, session_key=session_key)

    # Sécurité : seul le propriétaire peut voir son historique
    if session.user and request.user.is_authenticated:
        if session.user != request.user and not request.user.is_staff:
            return Response({'error': 'Accès interdit.'}, status=403)

    messages = session.messages.order_by('created_at')
    return Response({
        'session_key': session_key,
        'messages': [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'created_at': m.created_at.isoformat(),
            }
            for m in messages
        ]
    })


# ─────────────────────────────────────────────────────────────────────────────
# Admin — Gestion des FAQ
# ─────────────────────────────────────────────────────────────────────────────

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class FAQDocumentListCreateView(APIView):
    """
    GET  /api/chatbot/faq/          — liste tous les documents FAQ (admin)
    POST /api/chatbot/faq/          — créer un nouveau document FAQ
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        category = request.query_params.get('category')
        qs = FAQDocument.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)

        data = [
            {
                'id': doc.id,
                'title': doc.title,
                'question': doc.question,
                'answer': doc.answer,
                'category': doc.category,
                'category_display': doc.get_category_display(),
                'tags': doc.tags,
                'updated_at': doc.updated_at.isoformat(),
            }
            for doc in qs
        ]
        return Response(data)

    def post(self, request):
        required = ['title', 'question', 'answer']
        for field in required:
            if not request.data.get(field):
                return Response({'error': f'{field} est requis.'}, status=400)

        doc = FAQDocument.objects.create(
            title=request.data['title'],
            question=request.data['question'],
            answer=request.data['answer'],
            category=request.data.get('category', 'general'),
            tags=request.data.get('tags', ''),
            created_by=request.user,
        )

        # Réindexer dans ChromaDB
        _reindex_async()

        return Response({
            'id': doc.id,
            'title': doc.title,
            'message': 'Document créé et indexé.'
        }, status=201)


class FAQDocumentDetailView(APIView):
    """
    GET    /api/chatbot/faq/<id>/   — détail
    PUT    /api/chatbot/faq/<id>/   — modifier
    DELETE /api/chatbot/faq/<id>/   — supprimer (désactiver)
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        doc = get_object_or_404(FAQDocument, pk=pk)
        return Response({
            'id': doc.id,
            'title': doc.title,
            'question': doc.question,
            'answer': doc.answer,
            'category': doc.category,
            'tags': doc.tags,
            'is_active': doc.is_active,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
        })

    def put(self, request, pk):
        doc = get_object_or_404(FAQDocument, pk=pk)
        doc.title = request.data.get('title', doc.title)
        doc.question = request.data.get('question', doc.question)
        doc.answer = request.data.get('answer', doc.answer)
        doc.category = request.data.get('category', doc.category)
        doc.tags = request.data.get('tags', doc.tags)
        doc.is_active = request.data.get('is_active', doc.is_active)
        doc.save()

        # Réindexer
        _reindex_async()

        return Response({'message': 'Document mis à jour et réindexé.'})

    def delete(self, request, pk):
        doc = get_object_or_404(FAQDocument, pk=pk)
        doc.is_active = False
        doc.save(update_fields=['is_active'])

        # Réindexer (retire le doc désactivé)
        _reindex_async()

        return Response({'message': 'Document désactivé.'}, status=204)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reindex_faq(request):
    """
    POST /api/chatbot/reindex/
    Force la réindexation complète des FAQ dans ChromaDB.
    """
    try:
        count = index_faq_documents()
        return Response({
            'message': f'{count} documents réindexés avec succès.',
            'count': count
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def chatbot_stats(request):
    """
    GET /api/chatbot/stats/
    Statistiques d'utilisation du chatbot.
    """
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    last_7 = now - timedelta(days=7)

    total_sessions = ChatSession.objects.count()
    total_messages = ChatMessage.objects.filter(role='user').count()
    sessions_7d = ChatSession.objects.filter(created_at__gte=last_7).count()
    faq_count = FAQDocument.objects.filter(is_active=True).count()

    # Questions les plus posées (approximation par mots fréquents)
    recent_questions = ChatMessage.objects.filter(
        role='user', created_at__gte=last_7
    ).values_list('content', flat=True)[:100]

    return Response({
        'total_sessions': total_sessions,
        'total_user_messages': total_messages,
        'sessions_last_7_days': sessions_7d,
        'faq_documents_active': faq_count,
        'recent_questions_sample': list(recent_questions[:10]),
    })


def _reindex_async():
    """Réindexe en arrière-plan (thread simple pour éviter de bloquer la réponse)."""
    import threading
    thread = threading.Thread(target=index_faq_documents, daemon=True)
    thread.start()
