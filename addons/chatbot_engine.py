# addons/chatbot_engine.py
# Moteur de chatbot ROBUSTE pour StudiServ.
#
# Objectifs (corrige "le chatbot ne répond pas") :
#   1. Toujours répondre — même si Ollama/OpenAI n'est pas disponible :
#      on retombe alors sur une réponse EXTRACTIVE construite directement
#      à partir des documents retrouvés dans ChromaDB (vos data_level0.bin).
#   2. Répondre sur "tout" le contenu de la plateforme (FAQ + PDF indexés).
#   3. Recommander des prestataires quand l'utilisateur le demande.
#
# Ce module RÉUTILISE le pipeline existant chatbot.rag_engine
# (retrieve_relevant_docs, build_rag_prompt, get_llm) sans le casser.

import logging
import re

logger = logging.getLogger(__name__)

# Intentions de recommandation
_RECO_PATTERNS = [
    r"recommand", r"conseill", r"sugg[eè]r", r"meilleur", r"top\b",
    r"quel prestataire", r"quels prestataires", r"qui peut", r"trouve[r]?\s+un",
    r"besoin d'un", r"cherche un", r"recommend", r"best provider", r"suggest",
]


def _wants_recommendation(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _RECO_PATTERNS)


def _extract_category(text: str) -> str:
    """Devine une catégorie/mot-clé de service depuis la question (best-effort)."""
    t = (text or "").lower()
    # quelques catégories fréquentes — adaptez à vos catégories réelles
    known = ["math", "informatique", "design", "rédaction", "redaction", "traduction",
             "cours", "tutoring", "développement", "developpement", "web", "anglais",
             "comptabilité", "comptabilite", "physique", "chimie", "marketing"]
    for k in known:
        if k in t:
            return k
    return ""


def _format_providers(providers) -> str:
    """Formate une liste de prestataires recommandés (anonymisée par #id)."""
    if not providers:
        return ("Je n'ai pas encore trouvé de prestataire correspondant. "
                "Essaie une catégorie précise (ex. « maths », « design », « traduction »).")
    lines = ["Voici des prestataires recommandés sur StudiServ :"]
    for i, p in enumerate(providers, 1):
        # get_top_providers peut renvoyer des objets ReputationScore ou Service.
        ref = getattr(p, "prestataire_id", None) or getattr(p, "id", None)
        note = (getattr(p, "score_global", None)
                or getattr(p, "note_moyenne", None)
                or getattr(p, "avg_score", None))
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


def _recommend_providers(question: str, user=None, limit: int = 5) -> dict:
    """Construit une réponse de recommandation via le moteur marketplace."""
    try:
        from marketplace.recommendation_engine import (
            get_top_providers, get_recommendations_for_user,
        )
    except Exception as e:
        logger.warning("Moteur de reco indisponible: %s", e)
        return None

    providers = []
    # Reco personnalisée si l'utilisateur est connecté
    try:
        if user is not None and getattr(user, "is_authenticated", False):
            providers = list(get_recommendations_for_user(user, limit=limit) or [])
    except Exception as e:
        logger.info("Reco perso échouée: %s", e)

    if not providers:
        try:
            providers = list(get_top_providers(limit=limit) or [])
        except TypeError:
            # signature sans 'limit'
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


def _extractive_answer(question: str, docs) -> str:
    """
    Réponse SANS LLM : on renvoie le(s) passage(s) les plus pertinents
    retrouvés dans ChromaDB. Garantit une réponse même hors-ligne.
    """
    if not docs:
        return ("Je n'ai pas trouvé d'information précise sur ce point dans ma base. "
                "Reformule ta question, ou consulte ton tableau de bord / contacte un administrateur.")
    # docs = liste de (Document, score)
    best = docs[0][0]
    content = (getattr(best, "page_content", "") or "").strip()
    # Nettoyage léger : enlève les préfixes "Question:/Réponse:/Tags:"
    content = re.sub(r"^\s*(Question|Réponse|Reponse|Tags)\s*:\s*", "", content, flags=re.I | re.M)
    if len(content) > 900:
        content = content[:900].rsplit(" ", 1)[0] + "…"
    return content


def get_chatbot_response(question, conversation_history=None, session_key=None, user=None):
    """
    Pipeline robuste. Signature compatible avec l'ancien get_chatbot_response,
    avec un paramètre optionnel `user` pour la personnalisation.

    Retour: { 'answer', 'sources', 'fallback', 'intent'? }
    """
    # 1) Intention de recommandation → moteur marketplace
    if _wants_recommendation(question):
        reco = _recommend_providers(question, user=user)
        if reco is not None:
            return reco

    # 2) Récupération de contexte (réutilise le store ChromaDB existant)
    try:
        from chatbot.rag_engine import retrieve_relevant_docs, build_rag_prompt, get_llm
    except Exception as e:
        logger.error("Import rag_engine impossible: %s", e)
        return {"answer": "Le moteur de connaissances est indisponible pour le moment.",
                "sources": [], "fallback": True}

    try:
        docs = retrieve_relevant_docs(question)
    except Exception as e:
        logger.error("Retrieval ChromaDB échoué: %s", e)
        docs = []

    sources = []
    for doc, score in docs:
        md = getattr(doc, "metadata", {}) or {}
        sources.append({
            "faq_id": md.get("faq_id"),
            "title": md.get("title"),
            "category": md.get("category"),
            "relevance_score": round(float(score), 3),
        })

    # 3) Génération via LLM si dispo, sinon réponse extractive
    try:
        llm = get_llm()
        messages = build_rag_prompt(question, docs)
        response = llm.invoke(messages)
        answer = getattr(response, "content", None) or str(response)
        return {"answer": answer, "sources": sources, "fallback": len(docs) == 0}
    except Exception as e:
        # LLM non configuré / Ollama hors-ligne / quota… → fallback extractif
        logger.warning("LLM indisponible (%s) — réponse extractive.", e)
        return {
            "answer": _extractive_answer(question, docs),
            "sources": sources,
            "fallback": len(docs) == 0,
            "intent": "extractive",
        }


# Alias rétro-compatible
get_chatbot_response_robust = get_chatbot_response
