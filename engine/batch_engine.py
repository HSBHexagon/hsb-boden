"""
HSB Sales OS - Batch-Engine.

Kein Hardcoding von Mengen. Input: owner + count (+ Filter).
Output: ein immutable Batch mit eigener Batch_ID.

PREPARE != SEND. Diese Engine sendet niemals extern.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from datetime import datetime, timezone
from pathlib import Path

from hsb_core import (
    FLYERS,
    REPO_ROOT,
    AssetGateError,
    assert_asset_gate,
    check_eligibility,
    make_batch_id,
    normalize_owner,
    sha256_bytes,
    utc_now_iso,
)

BATCH_ROOT = REPO_ROOT / "batches"

# --------------------------------------------------------------------------


@dataclass
class BatchStats:
    requested_count: int = 0
    total_pool: int = 0
    eligible_count: int = 0
    selected_count: int = 0
    excluded_count: int = 0
    already_contacted_count: int = 0
    suppressed_count: int = 0
    optout_count: int = 0
    bounce_count: int = 0
    invalid_email_count: int = 0
    no_legal_basis_count: int = 0
    no_release_count: int = 0
    in_active_batch_count: int = 0
    shortfall: int = 0
    exclusion_reasons: dict = field(default_factory=dict)


@dataclass
class Batch:
    batch_id: str
    owner_key: str
    owner_display: str
    mailbox: str
    campaign: str
    created_at: str
    asset_filename: str
    asset_drive_id: str
    asset_sha256: str
    status: str
    stats: BatchStats
    leads: list = field(default_factory=list)

    def to_manifest(self) -> dict:
        d = asdict(self)
        d["stats"] = asdict(self.stats)
        d["leads"] = [
            {"Lead_ID": l.get("Lead_ID"), "Email": l.get("Email"),
             "Company": l.get("Company")} for l in self.leads
        ]
        return d


# --------------------------------------------------------------------------
# Auswahl
# --------------------------------------------------------------------------

def prepare_batch(
    leads: list[dict],
    owner: str,
    count: int,
    campaign: str = "",
    industry: str | None = None,
    tier: str | None = None,
    seq: int = 1,
    active_batch_lead_ids: set | None = None,
    when: datetime | None = None,
) -> Batch:
    """
    Waehlt deterministisch die naechsten `count` sendefaehigen Leads.

    Kein Lead landet gleichzeitig in mehreren aktiven Batches.
    Bereits gesendete, opt-out, hard-bounced, suppressed werden ausgeschlossen.
    """
    if count < 0:
        raise ValueError("count darf nicht negativ sein")

    owner_key = normalize_owner(owner)
    flyer = assert_asset_gate(owner_key)          # fail-closed vor jeder Auswahl
    active_batch_lead_ids = active_batch_lead_ids or set()

    stats = BatchStats(requested_count=count)
    reasons_counter: dict[str, int] = {}
    pool: list[dict] = []

    for lead in leads:
        if normalize_owner(lead.get("Owner")) != owner_key:
            continue
        if industry and str(lead.get("Industry") or "").strip() != industry:
            continue
        if tier and str(lead.get("Tier") or "").strip().upper() != tier.strip().upper():
            continue
        stats.total_pool += 1

        if lead.get("Lead_ID") in active_batch_lead_ids:
            stats.in_active_batch_count += 1
            stats.excluded_count += 1
            reasons_counter["bereits in aktivem Batch"] = (
                reasons_counter.get("bereits in aktivem Batch", 0) + 1)
            continue

        result = check_eligibility(lead)
        if result.eligible:
            stats.eligible_count += 1
            pool.append(lead)
            continue

        stats.excluded_count += 1
        for r in result.reasons:
            key = re.sub(r"\(.*?\)", "", r).strip()
            reasons_counter[key] = reasons_counter.get(key, 0) + 1
            if key.startswith("Legal_Basis"):
                stats.no_legal_basis_count += 1
            elif key.startswith("Versandfreigabe"):
                stats.no_release_count += 1
            elif key == "Suppressed=YES":
                stats.suppressed_count += 1
            elif key == "Opt_Out=YES":
                stats.optout_count += 1
            elif key == "Hard Bounce":
                stats.bounce_count += 1
            elif key == "bereits gesendet":
                stats.already_contacted_count += 1
            elif key.startswith("E-Mail ungueltig"):
                stats.invalid_email_count += 1

    # Deterministische Reihenfolge: Tier A vor B, dann Lead-ID aufsteigend.
    pool.sort(key=lambda l: (
        0 if str(l.get("Tier") or "").upper() == "A" else 1,
        str(l.get("Lead_ID") or ""),
    ))

    selected = pool[:count]
    stats.selected_count = len(selected)
    stats.shortfall = max(0, count - len(selected))
    stats.exclusion_reasons = dict(
        sorted(reasons_counter.items(), key=lambda kv: -kv[1]))

    status = "PREPARED" if selected else "EMPTY_NO_ELIGIBLE_LEADS"

    return Batch(
        batch_id=make_batch_id(owner_key, seq, when),
        owner_key=owner_key,
        owner_display=flyer.display_name,
        mailbox=flyer.mailbox,
        campaign=campaign,
        created_at=utc_now_iso(),
        asset_filename=flyer.filename,
        asset_drive_id=flyer.drive_id,
        asset_sha256=flyer.sha256,
        status=status,
        stats=stats,
        leads=selected,
    )


def explain_batch(batch: Batch) -> str:
    """Klartext-Erklaerung - auch und gerade fuer den leeren Batch."""
    s = batch.stats
    lines = [
        f"Batch {batch.batch_id} | Absender {batch.owner_display} <{batch.mailbox}>",
        f"Angefordert: {s.requested_count} | Ausgewaehlt: {s.selected_count} "
        f"| Sendefaehig im Pool: {s.eligible_count} von {s.total_pool}",
    ]
    if s.shortfall:
        lines.append(
            f"FEHLBETRAG: {s.shortfall} - es gibt nicht genug sendefaehige Leads.")
    if s.exclusion_reasons:
        lines.append("Ausschlussgruende:")
        for reason, n in s.exclusion_reasons.items():
            lines.append(f"  - {n}x {reason}")
    if s.selected_count == 0:
        lines.append("")
        lines.append(
            "NAECHSTER SCHRITT: Leads muessen zuerst rechtlich qualifiziert werden "
            "(Legal_Basis=OPT_IN oder EXISTING_CUSTOMER_7_3 UND Versandfreigabe=YES). "
            "Das ist eine bewusste Entscheidung im Sheet, keine technische Huerde.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# EML-Erzeugung
# --------------------------------------------------------------------------

SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe(value: str, maxlen: int = 48) -> str:
    return SAFE_RE.sub("-", str(value or "")).strip("-")[:maxlen] or "lead"


def render_email(lead: dict, batch: Batch, template: str | None = None) -> tuple[str, str]:
    """Gibt (subject, body) zurueck."""
    company = str(lead.get("Company") or "Ihr Unternehmen").strip()
    contact = str(lead.get("Contact") or "").strip()
    greeting = f"Guten Tag {contact}," if contact else "Guten Tag,"
    owner = batch.owner_display
    subject = f"Industrieboeden fuer {company} - Beratung von {owner}"

    body = template or (
        "{greeting}\n\n"
        "mein Name ist {owner} von der HSB Hexagon Saeurebau GmbH. Wir planen, "
        "bauen und sanieren saeurebestaendige, hygienische Industrieboeden - "
        "ausgelegt auf das reale Belastungsprofil statt auf ein Standardprodukt.\n\n"
        "Typische Themen bei Produktionsbetrieben:\n"
        "- Risse, Abloesungen und offene Fugen\n"
        "- Keimnester in Nassbereichen\n"
        "- stehendes Wasser durch falsches Gefaelle\n"
        "- defekte Rinnen und Ablaeufe\n\n"
        "Im angehaengten Flyer sehen Sie ausgefuehrte Projektflaechen und unser "
        "Vorgehen von der Analyse bis zur dokumentierten Uebergabe.\n\n"
        "Gerne pruefen wir Ihr Belastungsprofil unverbindlich und vor Ort.\n\n"
        "Mit freundlichen Gruessen\n"
        "{owner}\n"
        "HSB Hexagon Saeurebau GmbH\n"
        "{mailbox}\n"
        "Tel. +49 (0)2562 9463030\n\n"
        "---\n"
        "Wenn Sie keine weiteren Informationen erhalten moechten, antworten Sie "
        "bitte mit dem Betreff \"Abmelden\" auf diese E-Mail."
    )
    body = body.format(greeting=greeting, owner=owner, mailbox=batch.mailbox,
                       company=company)
    return subject, body


def build_eml(lead: dict, batch: Batch, pdf_bytes: bytes) -> bytes:
    """Erzeugt genau eine EML mit genau einem korrekten PDF-Anhang."""
    subject, body = render_email(lead, batch)

    msg = EmailMessage()
    msg["From"] = f"{batch.owner_display} <{batch.mailbox}>"
    msg["To"] = str(lead.get("Email") or "").strip()
    msg["Reply-To"] = batch.mailbox
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    msg["Message-ID"] = make_msgid(domain="hsb-boden.de")
    # X-Unsent=1 => Outlook oeffnet die Datei als unversendeten Entwurf.
    msg["X-Unsent"] = "1"
    msg["X-HSB-Lead-ID"] = str(lead.get("Lead_ID") or "")
    msg["X-HSB-Batch-ID"] = batch.batch_id
    msg["X-HSB-Owner"] = batch.owner_key
    msg["X-HSB-Asset-SHA256"] = batch.asset_sha256

    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf",
                       filename=batch.asset_filename)
    return msg.as_bytes()


def write_batch(batch: Batch, root: Path | None = None) -> Path:
    """
    Schreibt batches/<BATCH_ID>/ mit drafts/, manifest.json, status.csv.
    Prueft den Anhang-Hash pro Datei - Cross-Sender ist unmoeglich.
    """
    root = root or BATCH_ROOT
    out = root / batch.batch_id
    drafts = out / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)

    flyer = FLYERS[batch.owner_key]
    pdf_bytes = flyer.path.read_bytes()
    actual = sha256_bytes(pdf_bytes)
    if actual != batch.asset_sha256:
        raise AssetGateError(
            f"ASSET_GATE=FAIL beim Schreiben: {actual[:12]} != {batch.asset_sha256[:12]}")

    rows = ["Lead_ID,Email,Company,Batch_ID,Owner,EML_File,Attachment_SHA256,Status"]
    for lead in batch.leads:
        eml = build_eml(lead, batch, pdf_bytes)
        fname = f"{batch.owner_key.lower()}_{_safe(lead.get('Lead_ID'))}_{_safe(lead.get('Company'))}.eml"
        (drafts / fname).write_bytes(eml)
        rows.append(",".join([
            str(lead.get("Lead_ID") or ""),
            str(lead.get("Email") or ""),
            '"' + str(lead.get("Company") or "").replace('"', "'") + '"',
            batch.batch_id, batch.owner_key, fname, actual, "PREPARED",
        ]))

    (out / "manifest.json").write_text(
        json.dumps(batch.to_manifest(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out / "status.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (out / "README.txt").write_text(
        f"Batch {batch.batch_id}\n"
        f"Absender: {batch.owner_display} <{batch.mailbox}>\n"
        f"Entwuerfe: {len(batch.leads)}\n"
        f"Anhang: {batch.asset_filename} (SHA-256 {batch.asset_sha256})\n\n"
        "Import in neues Outlook: Einstellungen > Dateien > Import,\n"
        "Ordner 'drafts' waehlen, Zielordner 'Entwuerfe'.\n"
        "Jeden Entwurf vor dem Senden pruefen.\n", encoding="utf-8")
    return out
