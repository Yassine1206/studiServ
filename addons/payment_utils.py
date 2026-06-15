# addons/payment_utils.py
# Validation et passerelle de paiement SIMULÉE mais réaliste.
# Aucune vraie transaction — mais les entrées sont réellement validées
# (Luhn, expiration, CVV, marque). Le paiement échoue si la carte est invalide.

import re
import uuid
from datetime import datetime


def _digits(s):
    return re.sub(r"\D", "", s or "")


def luhn_valid(card_number: str) -> bool:
    """Algorithme de Luhn — valide la cohérence d'un numéro de carte."""
    num = _digits(card_number)
    if not (12 <= len(num) <= 19):
        return False
    total = 0
    reverse = num[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def detect_brand(card_number: str) -> str:
    num = _digits(card_number)
    if num.startswith("4"):
        return "Visa"
    if re.match(r"^5[1-5]", num) or re.match(r"^2(2[2-9]|[3-6]|7[01]|720)", num):
        return "Mastercard"
    if re.match(r"^3[47]", num):
        return "Amex"
    return "Carte"


def expiry_valid(month, year) -> bool:
    try:
        month = int(month)
        year = int(year)
    except (TypeError, ValueError):
        return False
    if not (1 <= month <= 12):
        return False
    if year < 100:
        year += 2000
    now = datetime.utcnow()
    # Valide jusqu'à la fin du mois d'expiration
    if year < now.year:
        return False
    if year == now.year and month < now.month:
        return False
    return True


def cvv_valid(cvv, brand="Carte") -> bool:
    cvv = _digits(cvv)
    expected = 4 if brand == "Amex" else 3
    return len(cvv) == expected


def validate_card(data: dict) -> dict:
    """
    Valide les données de carte.
    Retourne {'ok': bool, 'error': str, 'brand': str, 'last4': str}.
    """
    number = _digits(data.get("card_number"))
    name = (data.get("card_name") or "").strip()
    month = data.get("exp_month")
    year = data.get("exp_year")
    cvv = data.get("cvv")

    if not name:
        return {"ok": False, "error": "Nom du titulaire requis."}
    if not luhn_valid(number):
        return {"ok": False, "error": "Numéro de carte invalide."}

    brand = detect_brand(number)

    if not expiry_valid(month, year):
        return {"ok": False, "error": "Date d'expiration invalide ou dépassée."}
    if not cvv_valid(cvv, brand):
        return {"ok": False, "error": "Code CVV invalide."}

    return {"ok": True, "error": "", "brand": brand, "last4": number[-4:]}


def process_payment(amount, card_data: dict) -> dict:
    """
    Passerelle simulée. Valide la carte puis "autorise" le paiement.
    Carte de test refusée : 4000000000000002 (simule un refus banque).
    Retourne {'success': bool, 'error': str, 'reference': str, 'brand', 'last4'}.
    """
    check = validate_card(card_data)
    if not check["ok"]:
        return {"success": False, "error": check["error"]}

    number = _digits(card_data.get("card_number"))
    if number == "4000000000000002":
        return {"success": False, "error": "Paiement refusé par la banque émettrice."}

    if float(amount) <= 0:
        return {"success": False, "error": "Montant invalide."}

    return {
        "success": True,
        "error": "",
        "reference": f"TX-{uuid.uuid4().hex[:16].upper()}",
        "brand": check["brand"],
        "last4": check["last4"],
    }
