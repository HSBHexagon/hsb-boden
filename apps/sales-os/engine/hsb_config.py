"""
HSB Sales OS - Sichere Konfiguration & Secret Management.
Laedt sensible Verbindungswerte aus Umgebungsvariablen oder lokaler .env-Datei.
Keine Klartext-Secrets im Quelltext.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
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

def get_jordi_token() -> str:
    """Ruft ein frisches OAuth2-Token fuer Jordi ab mit automatischer Wiederholung bei Netzwerkfehlern."""
    refresh_token = get_fc_refresh_token()

    token_url = f"https://login.microsoftonline.com/{FC_TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": FC_CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": FC_SCOPE
    }).encode("utf-8")

    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(token_url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                tokens = json.loads(resp.read().decode("utf-8"))
                return tokens["access_token"]
        except Exception as ex:
            last_err = ex
            if attempt < 3:
                time.sleep(1.5 * attempt)
                continue
            raise last_err
