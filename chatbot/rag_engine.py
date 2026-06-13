# apps/chatbot/rag_engine.py
# M9 — Moteur RAG (Retrieval-Augmented Generation)
#
# Architecture :
#   1. FAQDocument en base → ChromaDB (vector store)
#   2. Question utilisateur → embedding → recherche top-k dans ChromaDB
#   3. Contexte récupéré + question → LLM (OpenAI ou Ollama) → réponse
#
# Dépendances : pip install langchain langchain-openai langchain-community
#               chromadb sentence-transformers

import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

SETTINGS = settings.CHATBOT_SETTINGS

# ─── Embedding model (sentence-transformers, gratuit, multilingue) ───────────

def get_embedding_function():
    """
    Retourne la fonction d'embedding.
    Utilise sentence-transformers (local, gratuit, supporte le français).
    """
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=SETTINGS['EMBEDDING_MODEL'],
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except ImportError:
        raise ImportError(
            "Installe sentence-transformers : pip install sentence-transformers langchain-community"
        )


# ─── Vector store (ChromaDB) ─────────────────────────────────────────────────

_chroma_client = None
_vector_store = None

def get_vector_store(force_rebuild=False):
    """
    Retourne le vector store ChromaDB.
    Singleton — rechargé uniquement si force_rebuild=True.
    """
    global _chroma_client, _vector_store

    if _vector_store is not None and not force_rebuild:
        return _vector_store

    try:
        import chromadb
        from langchain_community.vectorstores import Chroma

        persist_dir = SETTINGS['CHROMA_PERSIST_DIR']
        embedding_fn = get_embedding_function()

        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _vector_store = Chroma(
            client=_chroma_client,
            collection_name='studiServ_faq',
            embedding_function=embedding_fn,
            persist_directory=persist_dir
        )
        logger.info(f"Vector store chargé depuis {persist_dir}")
        return _vector_store

    except ImportError:
        raise ImportError(
            "Installe chromadb : pip install chromadb langchain-community"
        )


def index_faq_documents(documents=None):
    """
    Indexe les FAQDocuments dans ChromaDB.
    Si documents=None → indexe tous les documents actifs.
    Appelé par le signal post_save et la commande management.
    """
    from .models import FAQDocument
    from langchain.schema import Document as LangchainDoc

    if documents is None:
        documents = FAQDocument.objects.filter(is_active=True)

    if not documents:
        logger.warning("Aucun document FAQ à indexer.")
        return 0

    vs = get_vector_store(force_rebuild=True)

    # Supprimer et reconstruire (simple pour 2 semaines)
    try:
        vs.delete_collection()
    except Exception:
        pass

    # Recréer le vector store
    global _vector_store
    _vector_store = None
    vs = get_vector_store(force_rebuild=True)

    langchain_docs = []
    for doc in documents:
        langchain_docs.append(
            LangchainDoc(
                page_content=doc.to_text(),
                metadata={
                    'faq_id': doc.id,
                    'title': doc.title,
                    'category': doc.category,
                    'tags': doc.tags,
                }
            )
        )

    vs.add_documents(langchain_docs)
    logger.info(f"{len(langchain_docs)} documents FAQ indexés dans ChromaDB.")
    return len(langchain_docs)


def retrieve_relevant_docs(question: str, k: int = None) -> list:
    """
    Recherche les documents les plus pertinents pour une question.
    Retourne une liste de (document, score).
    """
    k = k or SETTINGS['TOP_K_RESULTS']
    vs = get_vector_store()

    try:
        results = vs.similarity_search_with_score(question, k=k)
        # Filtrer les résultats peu pertinents (score > 1.5 = trop loin)
        filtered = [(doc, score) for doc, score in results if score < 1.5]
        return filtered
    except Exception as e:
        logger.error(f"Erreur de recherche ChromaDB: {e}")
        return []


# ─── LLM ─────────────────────────────────────────────────────────────────────

def get_llm():
    """
    Retourne le LLM configuré (OpenAI ou Ollama).
    """
    provider = SETTINGS.get('LLM_PROVIDER', 'openai')

    if provider == 'openai':
        api_key = SETTINGS.get('OPENAI_API_KEY', '')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY manquant. Configure-le dans les variables d'environnement "
                "ou change LLM_PROVIDER='ollama' pour utiliser un modèle local."
            )
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=SETTINGS['OPENAI_MODEL'],
                openai_api_key=api_key,
                max_tokens=SETTINGS['MAX_TOKENS_RESPONSE'],
                temperature=0.3,  # Réponses factuelles et cohérentes
            )
        except ImportError:
            raise ImportError("pip install langchain-openai")

    elif provider == 'ollama':
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=SETTINGS['OLLAMA_MODEL'],
                base_url=SETTINGS['OLLAMA_BASE_URL'],
                num_predict=SETTINGS['MAX_TOKENS_RESPONSE'],
                temperature=0.3,
            )
        except ImportError:
            raise ImportError("pip install langchain-community")

    else:
        raise ValueError(f"LLM_PROVIDER inconnu : {provider}. Utilise 'openai' ou 'ollama'.")


# ─── Pipeline RAG complet ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es l'assistant virtuel de StudiServ, une marketplace de services entre étudiants tunisiens.
Tu aides les utilisateurs à comprendre la plateforme, à créer des annonces, passer des commandes, et résoudre leurs problèmes.

Règles :
- Réponds toujours en français, de manière claire et concise.
- Base-toi uniquement sur le contexte fourni. Si tu ne sais pas, dis-le honnêtement.
- Ne fais pas de suppositions sur des fonctionnalités non mentionnées dans le contexte.
- Sois amical et professionnel, comme un assistant étudiant bienveillant.
- Si la question est hors sujet (non liée à StudiServ), redirige poliment l'utilisateur.
"""

def build_rag_prompt(question: str, context_docs: list) -> list:
    """
    Construit le prompt RAG avec le contexte récupéré.
    """
    from langchain.schema import SystemMessage, HumanMessage

    if context_docs:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in context_docs])
        user_content = f"""Contexte de la base de connaissances StudiServ :

{context_text}

---

Question de l'utilisateur : {question}

Réponds en te basant sur le contexte ci-dessus."""
    else:
        user_content = f"""Question de l'utilisateur : {question}

Note : Je n'ai pas trouvé de réponse spécifique dans ma base de connaissances pour cette question."""

    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]


def get_chatbot_response(
    question: str,
    conversation_history: Optional[list] = None,
    session_key: Optional[str] = None
) -> dict:
    """
    Pipeline RAG complet :
    1. Retrieval → trouve les docs pertinents
    2. Augmentation → construit le prompt avec contexte
    3. Generation → appelle le LLM
    
    Retourne: {
        'answer': str,
        'sources': list[dict],
        'fallback': bool  # True si pas de contexte trouvé
    }
    """
    try:
        # 1. Retrieval
        relevant_docs = retrieve_relevant_docs(question)
        fallback = len(relevant_docs) == 0

        # 2. Build prompt
        messages = build_rag_prompt(question, relevant_docs)

        # 3. Generation
        llm = get_llm()
        response = llm.invoke(messages)
        answer = response.content

        # Extraire les sources
        sources = []
        for doc, score in relevant_docs:
            sources.append({
                'faq_id': doc.metadata.get('faq_id'),
                'title': doc.metadata.get('title'),
                'category': doc.metadata.get('category'),
                'relevance_score': round(float(score), 3),
            })

        return {
            'answer': answer,
            'sources': sources,
            'fallback': fallback,
        }

    except ValueError as e:
        # LLM non configuré
        logger.error(f"Erreur configuration LLM: {e}")
        return {
            'answer': "Le chatbot n'est pas encore configuré. Contacte l'équipe StudiServ.",
            'sources': [],
            'fallback': True,
            'error': str(e),
        }
    except Exception as e:
        logger.error(f"Erreur RAG: {e}", exc_info=True)
        return {
            'answer': "Désolé, je rencontre un problème technique. Réessaie dans quelques instants.",
            'sources': [],
            'fallback': True,
            'error': str(e),
        }
