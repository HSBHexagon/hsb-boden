"""
HSB Sales OS - Sichere Konfiguration & Secret Management.
Laedt sensible Verbindungswerte aus Umgebungsvariablen oder lokaler .env-Datei.
Keine Klartext-Secrets im Quelltext.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"

def _load_env_file():
    """Einfacher, robuster .env Loader ohne externe Abhaengigkeit."""
    if not ENV_FILE.exists():
        return
    try:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        print(f"Warnung: .env konnte nicht gelesen werden: {e}")

_load_env_file()

def get_joel_url() -> str:
    url = os.getenv("HSB_ADAPTER_URL_JOEL", "").strip()
    if not url:
        raise RuntimeError(
            "HSB_ADAPTER_URL_JOEL ist nicht gesetzt. Bitte in .env oder Umgebungsvariablen eintragen."
        )
    return url

def get_jordi_connector_url() -> str:
    return os.getenv(
        "JORDI_CONNECTOR_URL",
        "https://default-8adbbf2e-fd2c-4857-8540-bbcdb3a20f30.06.common.germany.azure-apihub.net/apim/logicflows/47ee3d7a-626c-4fff-9e16-6d938949e4bd/triggers/manual/run?api-version=2016-11-01"
    ).strip()

def get_fc_refresh_token() -> str:
    token = os.getenv("HSB_FC_REFRESH_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "HSB_FC_REFRESH_TOKEN ist nicht gesetzt. Bitte in .env oder Umgebungsvariablen eintragen."
        )
    return token

FC_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
FC_TENANT_ID = "8adbbf2e-fd2c-4857-8540-bbcdb3a20f30"
FC_SCOPE = "https://apihub.azure.com/.default offline_access"

def get_com_mailbox_config(owner: str) -> dict:
    """
    Gibt die IMAP/SMTP-Zugangsdaten für die .com-Postfächer (All-Inkl / KASServer) zurück.
    Unterstützt JOEL und JORDI (bzw. JORDIE).
    """
    norm = owner.strip().upper() if owner else 'JOEL'
    if norm in ('JORDIE', 'JORDI', 'J-POST'):
        owner_key = 'JORDI'
        email = os.getenv('HSB_COM_JORDI_EMAIL', 'j-post@hsb-boden.com').strip()
        user = os.getenv('HSB_COM_JORDI_USER', '').strip()
        pwd = os.getenv('HSB_COM_JORDI_PASS', '').strip()
        display_name = 'Jordie Post'
        reply_to = os.getenv('HSB_COM_JORDI_REPLY_TO', 'Jordie Post <j-post@hsb-boden.de>').strip()
    elif norm in ('JOEL', 'J-CHERINO'):
        owner_key = 'JOEL'
        email = os.getenv('HSB_COM_JOEL_EMAIL', 'j-cherino@hsb-boden.com').strip()
        user = os.getenv('HSB_COM_JOEL_USER', '').strip()
        pwd = os.getenv('HSB_COM_JOEL_PASS', '').strip()
        display_name = 'Joel Cherino Diaz'
        reply_to = os.getenv('HSB_COM_JOEL_REPLY_TO', 'Joel Cherino Diaz <j-cherino@hsb-boden.de>').strip()
    else:
        raise ValueError(f'Unbekannter Owner: {owner}. Erlaubt sind JOEL oder JORDI.')

    imap_server = os.getenv('HSB_COM_IMAP_SERVER', 'w0221a9f.kasserver.com').strip()
    imap_port = int(os.getenv('HSB_COM_IMAP_PORT', '993'))
    smtp_server = os.getenv('HSB_COM_SMTP_SERVER', 'w0221a9f.kasserver.com').strip()
    smtp_port = int(os.getenv('HSB_COM_SMTP_PORT', '465'))

    if not user or not pwd:
        raise RuntimeError(f'KASServer Zugangsdaten fuer {owner_key} fehlen in der .env-Datei.')

    return {
        'owner': owner_key,
        'display_name': display_name,
        'email': email,
        'username': user,
        'password': pwd,
        'imap_server': imap_server,
        'imap_port': imap_port,
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'drafts_folder': '"Entw&APw-rfe"',
        'sent_folder': '"Gesendet"',
        'inbox_folder': '"INBOX"',
        'reply_to': reply_to,
    }
