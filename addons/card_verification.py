# addons/card_verification.py
# Vérification automatique (best-effort) qu'une image téléversée ressemble
# bien à une CARTE ÉTUDIANTE, et non à n'importe quelle image.
#
# Stratégie en cascade (chaque étape est optionnelle et dégradée proprement) :
#   1. Type de fichier et taille plausibles.
#   2. Dimensions / ratio d'aspect cohérents avec une carte (si Pillow dispo).
#   3. OCR du texte (si pytesseract + tesseract dispo) → recherche de mots-clés
#      ("étudiant", "université", "carte", "student", "matricule", ...) et/ou
#      d'un numéro de matricule.
#
# Si NI Pillow NI pytesseract ne sont installés, on retombe sur une validation
# de base (type + taille) afin de ne jamais bloquer l'inscription par erreur
# technique — la vérification fine reste alors à l'admin.
#
# Dépendances optionnelles :
#   pip install pillow pytesseract
#   + le binaire système tesseract-ocr  (apt-get install tesseract-ocr tesseract-ocr-fra)

import logging
import re

logger = logging.getLogger(__name__)

KEYWORDS = [
    "etudiant", "étudiant", "etudiante", "étudiante", "student",
    "universite", "université", "university", "faculte", "faculté",
    "carte", "card", "matricule", "inscription", "scolaire",
    "institut", "ecole", "école", "campus", "studiant",
]

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf",
}

MAX_BYTES = 8 * 1024 * 1024  # 8 MB


def _normalize(text: str) -> str:
    return (text or "").lower()


def _keyword_hits(text: str) -> int:
    t = _normalize(text)
    return sum(1 for kw in KEYWORDS if kw in t)


def _has_matricule(text: str) -> bool:
    # Un identifiant d'au moins 5 chiffres consécutifs (matricule / n° carte)
    return bool(re.search(r"\d{5,}", text or ""))


def _ocr_text(uploaded_file):
    """Retourne le texte OCR ou None si l'OCR n'est pas disponible."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        logger.info("OCR indisponible (Pillow/pytesseract non installés).")
        return None

    try:
        uploaded_file.seek(0)
        # Les PDF ne sont pas gérés par Pillow directement → on saute l'OCR.
        if getattr(uploaded_file, "content_type", "") == "application/pdf":
            return None
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img, lang="fra+eng")
        return text
    except Exception as e:  # tesseract absent, image illisible, etc.
        logger.warning("Échec OCR carte étudiante: %s", e)
        return None
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def _aspect_ratio_ok(uploaded_file):
    """True si le ratio ressemble à une carte (entre ~1.2 et ~2.2). None si inconnu."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        uploaded_file.seek(0)
        if getattr(uploaded_file, "content_type", "") == "application/pdf":
            return None
        img = Image.open(uploaded_file)
        w, h = img.size
        if w == 0 or h == 0:
            return False
        ratio = max(w, h) / min(w, h)
        return 1.15 <= ratio <= 2.4
    except Exception:
        return None
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def verify_student_card(uploaded_file) -> dict:
    """
    Vérifie l'image/PDF d'une carte étudiante.
    Retourne {'ok': bool, 'reason': str, 'confidence': 'high'|'low'|'manual', 'details': {...}}.
    'manual' = on n'a pas pu trancher automatiquement → à valider par l'admin.
    """
    # 1) Garde-fous de base
    content_type = getattr(uploaded_file, "content_type", "") or ""
    size = getattr(uploaded_file, "size", 0) or 0

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return {"ok": False, "reason": "Format non accepté (JPEG, PNG, WEBP ou PDF).",
                "confidence": "high", "details": {"content_type": content_type}}
    if size and size > MAX_BYTES:
        return {"ok": False, "reason": "Fichier trop volumineux (max 8 Mo).",
                "confidence": "high", "details": {"size": size}}

    details = {"content_type": content_type, "size": size}

    # 2) OCR (si disponible)
    text = _ocr_text(uploaded_file)
    if text is not None:
        hits = _keyword_hits(text)
        matricule = _has_matricule(text)
        details.update({"keyword_hits": hits, "has_matricule": matricule,
                        "ocr_chars": len(text.strip())})

        # Une carte étudiante contient typiquement plusieurs de ces mots
        # et/ou un matricule.
        if hits >= 2 or (hits >= 1 and matricule):
            return {"ok": True, "reason": "Carte étudiante reconnue automatiquement.",
                    "confidence": "high", "details": details}

        # Image lisible mais sans aucun indice de carte étudiante → rejet.
        if len(text.strip()) >= 15 and hits == 0 and not matricule:
            return {"ok": False,
                    "reason": "Cette image ne ressemble pas à une carte étudiante. "
                              "Téléverse une photo nette de ta carte (recto).",
                    "confidence": "high", "details": details}

    # 3) Ratio d'aspect (indice secondaire)
    ratio_ok = _aspect_ratio_ok(uploaded_file)
    details["aspect_ratio_ok"] = ratio_ok
    if ratio_ok is False and text is None:
        return {"ok": False,
                "reason": "L'image ne ressemble pas à une carte (format inattendu).",
                "confidence": "low", "details": details}

    # 4) Indécis (OCR indispo, PDF, etc.) → on accepte mais en attente admin.
    return {"ok": True,
            "reason": "Carte reçue. Vérification finale par un administrateur.",
            "confidence": "manual", "details": details}
