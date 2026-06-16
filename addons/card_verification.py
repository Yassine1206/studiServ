# addons/card_verification.py
# Vérification automatique (best-effort) qu'une image téléversée ressemble
# bien à une CARTE ÉTUDIANTE, et non à n'importe quelle image.
#
# Stratégie en cascade (chaque étape est optionnelle et dégradée proprement) :
#   1. Type de fichier et taille plausibles.
#   2. Dimensions / ratio d'aspect cohérents avec une carte (si Pillow dispo).
#   3. Pour les PDF : extraction du texte via pypdf.
#      Pour les images : OCR du texte (si pytesseract + tesseract dispo).
#      Puis recherche de signaux forts : le mot « carte », un terme "étudiant",
#      ET un numéro de matricule (≥5 chiffres). Ces 3 doivent être présents
#      pour reconnaître automatiquement la carte.
#
# Dépendances optionnelles :
#   pip install pillow pytesseract pypdf
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


def _pdf_text(uploaded_file):
    """Extrait le texte d'un PDF via pypdf. Retourne None si pypdf indisponible
    ou si le PDF est illisible / vide."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # repli legacy
        except ImportError:
            logger.info("Extraction PDF indisponible (pypdf non installé).")
            return None

    try:
        uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)
        parts = []
        for page in reader.pages[:3]:  # 3 premières pages suffisent
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(parts)
    except Exception as e:
        logger.warning("Échec extraction texte PDF: %s", e)
        return None
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def _ocr_text(uploaded_file):
    """Retourne le texte OCR ou None si l'OCR n'est pas disponible.
    Pour les PDF, utilise pypdf au lieu de l'OCR image."""
    # Cas PDF : extraction directe du texte
    if getattr(uploaded_file, "content_type", "") == "application/pdf":
        return _pdf_text(uploaded_file)

    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        logger.info("OCR indisponible (Pillow/pytesseract non installés).")
        return None

    try:
        uploaded_file.seek(0)
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

    # 2) Extraction de texte (OCR image ou pypdf pour les PDF)
    text = _ocr_text(uploaded_file)
    if text is not None:
        text_lower = _normalize(text)
        matricule = _has_matricule(text)

        # Signaux forts d'une vraie carte étudiante
        has_card_word = bool(re.search(r"\b(carte|card)\b", text_lower))
        has_student_word = bool(re.search(
            r"\b(étudiant|etudiant|étudiante|etudiante|student|studiant)\b",
            text_lower,
        ))

        details.update({"has_matricule": matricule,
                        "ocr_chars": len(text.strip()),
                        "has_card_word": has_card_word,
                        "has_student_word": has_student_word})

        # Carte reconnue : doit contenir "carte" + un terme étudiant + un matricule.
        if has_card_word and has_student_word and matricule:
            return {"ok": True, "reason": "Carte étudiante reconnue automatiquement.",
                    "confidence": "high", "details": details}

        # Texte extrait mais signaux insuffisants → rejet explicite.
        if len(text.strip()) >= 15:
            missing = []
            if not has_card_word:
                missing.append("le mot « carte »")
            if not has_student_word:
                missing.append("le mot « étudiant »")
            if not matricule:
                missing.append("un numéro de matricule")
            return {"ok": False,
                    "reason": "Ce document ne ressemble pas à une carte étudiante "
                              f"(manque : {', '.join(missing)}). "
                              "Téléverse une photo nette du recto de ta carte.",
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
