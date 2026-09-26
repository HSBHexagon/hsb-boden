#!/usr/bin/env python3
"""
HSB Sales OS - Smart Reply Intent Classifier & Cadence Engine (UG-ENT-04).
Klassifiziert eingehende Kunden-E-Mails in Outlook / IMAP automatisch in 4 Handlungskategorien:
1. POSITIVE_INTEREST (Interesse, Angebot, Termin, Muster, Rueckruf)
2. OUT_OF_OFFICE (Abwesenheitsnotiz, Urlaub, Vertretung)
3. OPT_OUT (Abmeldung, kein Bedarf, DSGVO-Loeschung)
4. NEEDS_REVIEW (Sonstige Nachrichten zur manuellen Pruefung)

Zusaetzlich: Smart Cadence Tracker (Identifiziert Leads fuer Follow-Up nach 7-10 Tagen).
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple


POSITIVE_KEYWORDS = [
    r"angebot", r"interesse", r"termin", r"rueckruf", r"rückruf", r"muster",
    r"flaeche", r"fläche", r"quadratmeter", r"m²", r"kosten", r"preis",
    r"anfrage", r"vorbeikommen", r"besichtigung", r"beratung", r"zeitfenster",
    r"hsb-hexagon", r"industrieestrich", r"beschichtung", r"sanierung"
]

OPT_OUT_KEYWORDS = [
    r"abmelden", r"kein bedarf", r"kein interesse", r"loeschen", r"löschen",
    r"austragen", r"verteiler", r"werbung", r"datenschutz", r"unterlassen",
    r"widerspruch", r"stopp", r"nicht kontaktieren"
]

OOO_KEYWORDS = [
    r"abwesend", r"urlaub", r"out of office", r"automatische antwort",
    r"nicht im buero", r"nicht im büro", r"vertreten durch", r"wieder erreichbar",
    r"ab dem", r"bis einschliesslich", r"bis einschließlich"
]


def classify_reply_intent(subject: str, body: str) -> Dict[str, Any]:
    """
    Klassifiziert den Intent einer eingehenden Antwort.
    Gibt ein Dict mit classification, confidence, keywords, stop_followup zurueck.
    """
    subj_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    full_text = f"{subj_lower} {body_lower}"

    # 1. Pruefe Opt-Out
    opt_hits = [k for k in OPT_OUT_KEYWORDS if re.search(r"\b" + k + r"\b", full_text)]
    if opt_hits:
        return {
            "classification": "OPT_OUT",
            "confidence": 0.95,
            "matched_keywords": opt_hits,
            "stop_followup": True,
            "recommended_action": "Lead sperren (Pipeline: Abgemeldet)"
        }

    # 2. Pruefe Out-of-Office / Abwesenheit
    ooo_hits = [k for k in OOO_KEYWORDS if re.search(r"\b" + k + r"\b", full_text)]
    if ooo_hits:
        return {
            "classification": "OUT_OF_OFFICE",
            "confidence": 0.90,
            "matched_keywords": ooo_hits,
            "stop_followup": False,
            "recommended_action": "Wiedervorlage nach Rueckkehr setzen"
        }

    # 3. Pruefe Positives Interesse
    pos_hits = [k for k in POSITIVE_KEYWORDS if re.search(r"\b" + k + r"\b", full_text)]
    if pos_hits:
        return {
            "classification": "POSITIVE_INTEREST",
            "confidence": 0.85,
            "matched_keywords": pos_hits,
            "stop_followup": True,
            "recommended_action": "Prioritaet HOCH: Angebot erstellen / Anrufen"
        }

    return {
        "classification": "NEEDS_REVIEW",
        "confidence": 0.50,
        "matched_keywords": [],
        "stop_followup": False,
        "recommended_action": "Manuelle Pruefung im Tab POSTEINGANG"
    }


def evaluate_cadence_due(
    sent_date_str: str,
    reply_status: str = "",
    min_days: int = 7,
    max_days: int = 14
) -> Tuple[bool, str]:
    """
    Prueft, ob ein Lead fuer einen 2-Step Follow-Up (Schritt 2) faellig ist.
    Bedingungen:
    - Versendet vor mindestens min_days Tagen
    - Noch keine Antwort erhalten (reply_status leer)
    - Noch innerhalb des max_days Zeitfensters
    """
    if not sent_date_str or reply_status:
        return False, "Kein Follow-up (Bereits beantwortet oder kein Sendedatum)"

    # Parse sent date
    date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d.%m.%Y %H:%M"]
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.datetime.strptime(sent_date_str.split(".")[0], fmt)
            break
        except ValueError:
            continue

    if not parsed_date:
        return False, "Ungueltiges Datumsformat"

    now = datetime.datetime.now()
    delta_days = (now - parsed_date).days

    if min_days <= delta_days <= max_days:
        return True, f"Faellig fuer Schritt 2 Follow-Up (Versendet vor {delta_days} Tagen)"
    elif delta_days < min_days:
        return False, f"Zu frueh (Versendet vor {delta_days} Tagen, Wartezeit {min_days} Tage)"
    else:
        return False, f"Abgelaufen (Versendet vor {delta_days} Tagen, Maximum {max_days} Tage)"
