"""
HSB Sales OS - Kern: Flyer-Registry, Compliance-Gate, Feldmodell.

Wahrheitsordnung fuer Assets:
    sender -> exakte Drive-ID -> exakter SHA-256

Niemals nach Dateiname, Datum oder "neuester Datei" aufloesen.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "assets" / "canonical"

# --------------------------------------------------------------------------
# 1. Kanonische Flyer - IMMUTABLE RELEASE ASSETS
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FlyerMaster:
    owner_key: str
    display_name: str
    mailbox: str
    filename: str
    drive_id: str
    sha256: str

    @property
    def path(self) -> Path:
        return CANONICAL_DIR / self.filename


FLYERS: dict[str, FlyerMaster] = {
    "JORDI": FlyerMaster(
        owner_key="JORDI",
        display_name="Jordi Post",
        mailbox="j-post@hsb-boden.de",
        filename="HSB-Flyer-Jordi-Post_FINAL.pdf",
        drive_id="1UMX-fi2lJ9bo14KwuClqgfZQWECdE_XV",
        sha256="f343ff05d1e7353a3a91a60f5475c054e1af958ea72e466445e60b9f69059a21",
    ),
    "JOEL": FlyerMaster(
        owner_key="JOEL",
        display_name="Joel Cherino Diaz",
        mailbox="j-cherino@hsb-boden.de",
        filename="HSB-Flyer-Joel-Cherino_FINAL.pdf",
        drive_id="16Kt-eRk1uY0HorZCrEmGt3QfGcRpYadS",
        sha256="2bccadacc77b531057583d2d650963c30deceed36c8be1fd90ca64e8b8cde5fb",
    ),
}

# Bekannte fehlerhafte / veraltete Flyer-Fassungen. Treffer => Quarantaene.
KNOWN_BAD_HASHES: dict[str, str] = {
    "8b7309694b300c29a399af9940defc7515121598e6a18143e73a62420de33762":
        "Jordi alt: verschmutztes Einzelbild + Name im weissen Patch-Kasten",
    "a737acbcdd0916c7cc9918327e5f8dc1373358e4903479181af7de99fcc0cb8f":
        "Joel alt: verschmutztes Einzelbild",
    "494465232dd6e563907ca72cbdfe197ead0cc3b5b4b9e41b6771a08d187607cf":
        "Jordi alt: git main Fassung",
    "763ea1784fe83f0d0fd5ab5214e7fc219f1a3ae203e58987cfbdf56a4c22bd88":
        "Jordi alt: Tippfehler-Fassung 'Jordie Post'",
    "1745c05de9958f1c1646498a6ebc6e0a17d2aefb3a0e57ec98d8636859fe8dd0":
        "Jordi Zwischenstand: helles Einzelbild, nicht die 4-Bilder-Referenzseite",
    "7c72e93262a8524d2e90b4ea931bf1ee90f5f5321af1b859ba6ff62ce865549e":
        "Joel Zwischenstand: helles Einzelbild, nicht die 4-Bilder-Referenzseite",
}


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_flyer(owner_key: str) -> FlyerMaster:
    """Loest den Flyer ausschliesslich ueber den Absender-Schluessel auf."""
    key = normalize_owner(owner_key)
    if key not in FLYERS:
        raise AssetGateError(f"Unbekannter Absender: {owner_key!r}")
    return FLYERS[key]


class AssetGateError(RuntimeError):
    """ASSET_GATE=FAIL - blockiert jeden Versand. Keine Auto-Reparatur."""


def assert_asset_gate(owner_key: str) -> FlyerMaster:
    """Prueft den kanonischen Master gegen seinen Soll-Hash. Fail-closed."""
    flyer = resolve_flyer(owner_key)
    if not flyer.path.exists():
        raise AssetGateError(
            f"ASSET_GATE=FAIL - Master fehlt: {flyer.path}"
        )
    actual = sha256_file(flyer.path)
    if actual != flyer.sha256:
        reason = KNOWN_BAD_HASHES.get(actual, "unbekannte Fassung")
        raise AssetGateError(
            f"ASSET_GATE=FAIL fuer {flyer.owner_key}: "
            f"erwartet {flyer.sha256[:12]}..., gefunden {actual[:12]}... ({reason}). "
            "Kein automatischer Ersatz durch eine andere PDF."
        )
    return flyer


# --------------------------------------------------------------------------
# 2. Feldmodell - Mapping auf die real vorhandenen Sheet-Spalten
# --------------------------------------------------------------------------

# Links: logischer Name laut Zielarchitektur. Rechts: reale Sheet-Spalte.
FIELD_MAP: dict[str, str] = {
    "Lead_ID": "Lead-ID",
    "Owner": "Verantwortlicher",
    "Email": "E-Mail",
    "Company": "Firma",
    "Contact": "Ansprechpartner",
    "Industry": "Branche",
    "Tier": "Tier",
    "Campaign_ID": "Kampagne_ID",
    "Versandfreigabe": "Versandfreigabe",
    "Opt_Out": "Opt-out-Status",
    "Opt_In": "Opt-in-Status",
    "Batch_ID": "Batch_ID",
    "Send_Status": "Send_Status",
    "Sent_At": "Send_Datum",
    "Bounce_Status": "Bounce_Status",
    "Reply_Status": "Reply_Status",
    "Next_Action_At": "Follow-up-Datum",
    "Notes": "Notizen",
}

# Felder, die im Sheet ergaenzt werden muessen (Spalte 45+).
ADDITIONAL_FIELDS: list[str] = [
    "Legal_Basis",
    "Suppressed",
    "Batch_Status",
    "Prepared_At",
    "Draft_ID",
    "Drafted_At",
    "Approved_At",
    "Outlook_Message_ID",
    "Internet_Message_ID",
    "Conversation_ID",
    "Last_Reply_At",
    "Last_Error",
]

# --------------------------------------------------------------------------
# 3. Compliance-Gate - fail-closed, §7 UWG
# --------------------------------------------------------------------------

LEGAL_BASIS_SENDABLE = {"OPT_IN", "EXISTING_CUSTOMER_7_3", "OWNER_APPROVED"}
LEGAL_BASIS_ALL = LEGAL_BASIS_SENDABLE | {"BLOCKED", "UNKNOWN"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$")


@dataclass
class EligibilityResult:
    eligible: bool
    reasons: list[str] = field(default_factory=list)


def normalize_owner(value: str | None) -> str:
    """'Jordi Post' / 'jordi' / 'JORDI' -> 'JORDI'."""
    if not value:
        return ""
    v = str(value).strip().upper()
    if v in FLYERS:
        return v
    if "JORDI" in v or "POST" in v:
        return "JORDI"
    if "JOEL" in v or "CHERINO" in v:
        return "JOEL"
    return v


def _norm(value) -> str:
    return str(value or "").strip().lower()


def check_eligibility(lead: dict) -> EligibilityResult:
    """
    Technischer Sendefilter. Ein Lead ist nur sendefaehig, wenn ALLE
    Bedingungen erfuellt sind. UNKNOWN/BLOCKED => nicht sendefaehig.

    Das Gate darf weder durch Batchgroesse noch UI noch CLI umgangen werden.
    """
    reasons: list[str] = []

    legal = str(lead.get("Legal_Basis") or "").strip().upper()
    if not legal:
        # Kein explizites Legal_Basis: aus Opt-in-Status ableiten, fail-closed.
        opt_in = _norm(lead.get("Opt_In"))
        legal = "OPT_IN" if opt_in in {"yes", "ja", "true", "opt_in"} else "UNKNOWN"
    if legal not in LEGAL_BASIS_SENDABLE:
        reasons.append(f"Legal_Basis={legal or 'UNKNOWN'}")

    if _norm(lead.get("Versandfreigabe")) not in {"yes", "ja", "true"}:
        reasons.append(f"Versandfreigabe={lead.get('Versandfreigabe') or 'leer'}")

    if _norm(lead.get("Suppressed")) in {"yes", "ja", "true"}:
        reasons.append("Suppressed=YES")

    if _norm(lead.get("Opt_Out")) in {"yes", "ja", "true", "opt_out"}:
        reasons.append("Opt_Out=YES")

    if _norm(lead.get("Bounce_Status")) in {"hard_bounce", "hard", "hardbounce"}:
        reasons.append("Hard Bounce")

    if _norm(lead.get("Send_Status")) in {"sent", "gesendet"}:
        reasons.append("bereits gesendet")

    email = str(lead.get("Email") or "").strip()
    if not EMAIL_RE.match(email):
        reasons.append(f"E-Mail ungueltig ({email or 'leer'})")

    if not normalize_owner(lead.get("Owner")) in FLYERS:
        reasons.append(f"Owner unklar ({lead.get('Owner') or 'leer'})")

    return EligibilityResult(eligible=not reasons, reasons=reasons)


# --------------------------------------------------------------------------
# 4. Batch-ID
# --------------------------------------------------------------------------

def make_batch_id(owner_key: str, seq: int, when: datetime | None = None) -> str:
    when = when or datetime.now(timezone.utc)
    return f"HSB-{when:%Y%m%d}-{normalize_owner(owner_key)}-{seq:04d}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
