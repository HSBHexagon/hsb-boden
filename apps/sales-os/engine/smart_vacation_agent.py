#!/usr/bin/env python3
"""
HSB Sales OS - Smart Vacation Follow-up Agent.
Verarbeitet Abwesenheitsnotizen (Out of Office / Urlaub), berechnet automatisch
das nächste Werktags-Wiedervorlagedatum und generiert einen freundlichen,
bezugnehmenden Follow-up-Entwurf für den Tag nach der Rückkehr.

Sicherheits-Invariante: REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Reine Entwurfserstellung & Terminierung).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
import html
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from hsb_core import assert_asset_gate, normalize_owner, sanitize_company_name
from inbound_classifier import extract_return_date
from run_100_batch import anrede_fuer, signatur_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("smart_vacation_agent")

REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


@dataclass
class VacationFollowupResult:
    lead_id: str
    company_name: str
    recipient_email: str
    return_date: Optional[str]
    followup_date: str
    subject: str
    body_html: str
    status: str  # SCHEDULED, FALLBACK_DEFAULT


def calculate_next_business_day(date_iso: Optional[str], default_days: int = 14) -> str:
    """Berechnet den nächsten Werktag (Mo-Fr) nach dem Rückkehrdatum."""
    today = datetime.date.today()
    if date_iso:
        try:
            d = datetime.date.fromisoformat(date_iso)
            # Wenn Rückkehrdatum in der Vergangenheit, ab heute rechnen
            if d < today:
                d = today + datetime.timedelta(days=1)
        except ValueError:
            d = today + datetime.timedelta(days=default_days)
    else:
        d = today + datetime.timedelta(days=default_days)

    # Wochenende überspringen (5 = Samstag, 6 = Sonntag)
    if d.weekday() == 5:
        d += datetime.timedelta(days=2)
    elif d.weekday() == 6:
        d += datetime.timedelta(days=1)

    return d.isoformat()


def build_vacation_followup_email(
    owner: str,
    lead: Dict[str, Any],
    return_date: Optional[str] = None
) -> Dict[str, Any]:
    norm_owner = normalize_owner(owner)
    flyer = assert_asset_gate(norm_owner)
    email = (lead.get("E-Mail") or lead.get("Email") or "").strip().lower()
    raw_comp = str(lead.get("Firma") or lead.get("Company") or "").strip()
    company = sanitize_company_name(raw_comp, email)

    lead_copy = dict(lead)
    lead_copy["Firma"] = company
    lead_copy["Company"] = company
    anrede = anrede_fuer(lead_copy)
    anrede_esc = html.escape(anrede)

    mailbox = f"j-cherino@hsb-boden.com" if flyer.owner_key == "JOEL" else f"j-post@hsb-boden.com"
    lead_id = str(lead.get("Lead_ID") or lead.get("Lead-ID") or "")
    sig = signatur_html(flyer.display_name, mailbox, flyer.mobile, lead_id=lead_id, to_email=email)

    subject = f"Re: Industrieböden für {company} – Willkommen zurück / Kurze Rückfrage"

    body_html = (
        f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:11pt;color:#222222;line-height:1.5;">'
        f'<p style="margin:0 0 12px 0;">{anrede_esc}</p>'
        f'<p style="margin:0 0 12px 0;">ich hoffe, Sie hatten eine erholsame Urlaubs- bzw. Abwesenheitszeit und '
        f'konnten gut wieder in den Betrieb starten.</p>'
        f'<p style="margin:0 0 12px 0;">Ich knüpfe kurz an meine Nachricht vor Ihrer Abwesenheit bezüglich der '
        f'säurefesten und hygienischen Industrieböden für {company} an. Da im Produktionsalltag oft wenig Zeit bleibt, '
        f'wollte ich mich kurz erkundigen, ob das Thema Bodenbelastung oder Sanierung aktuell bei Ihnen im Fokus steht.</p>'
        f'<p style="margin:0 0 12px 0;">Unser kompakter Online-Flyer mit Referenzflächen aus der Lebensmittel-, '
        f'Brauerei- und Chemiebranche steht Ihnen hier zur Verfügung:<br>'
        f'<a href="https://www.hsb-boden.de/flyer?utm_source=vacation_followup&utm_medium=email&utm_campaign=industrieboden_2026-10" '
        f'style="color:#1d4ed8;font-weight:600;text-decoration:underline;">www.hsb-boden.de/flyer</a></p>'
        f'<p style="margin:0 0 16px 0;">Gerne besprechen wir Ihr Anforderungsprofil in einem kurzen Telefonat oder '
        f'unverbindlich bei Ihnen vor Ort.</p>'
        f'<p style="margin:0 0 4px 0;">Mit freundlichen Grüßen</p>'
        f'{sig}'
        f'</div>'
    )

    return {
        "subject": subject,
        "body_html": body_html,
        "to_email": email,
        "company": company,
        "lead_id": lead_id
    }


class SmartVacationAgent:
    """Agent für automatisierte Urlaubserkennung und Follow-up Generierung."""

    def process_reply(
        self,
        lead: Dict[str, Any],
        reply_body: str,
        owner: str = "JOEL",
        reference_date: Optional[datetime.date] = None
    ) -> VacationFollowupResult:
        ret_date = extract_return_date(reply_body, reference_date=reference_date)
        followup_date = calculate_next_business_day(ret_date)

        email_data = build_vacation_followup_email(owner, lead, return_date=ret_date)
        status = "SCHEDULED" if ret_date else "FALLBACK_DEFAULT"

        logger.info(f"[{owner}] Lead {lead.get('Lead_ID')}: Rückkehr={ret_date or 'nicht genannt'} -> Wiedervorlage am {followup_date}")

        return VacationFollowupResult(
            lead_id=email_data["lead_id"],
            company_name=email_data["company"],
            recipient_email=email_data["to_email"],
            return_date=ret_date,
            followup_date=followup_date,
            subject=email_data["subject"],
            body_html=email_data["body_html"],
            status=status
        )


def main():
    agent = SmartVacationAgent()
    lead = {
        "Lead_ID": "HSB-2026-TEST",
        "Firma": "Molkerei Allgäu GmbH",
        "E-Mail": "einkauf@molkerei-allgaeu.de",
        "Ansprechpartner": "Herr Huber"
    }
    reply = "Guten Tag, ich bin bis einschließlich 14.11.2026 im Betriebsurlaub und danach wieder erreichbar."
    res = agent.process_reply(lead, reply, owner="JOEL")
    logger.info(f"Test-Ergebnis: Status={res.status} | Wiedervorlage={res.followup_date} | Betreff={res.subject}")


if __name__ == "__main__":
    main()
