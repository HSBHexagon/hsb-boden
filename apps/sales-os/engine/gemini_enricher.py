#!/usr/bin/env python3
"""
HSB Sales OS — Gemini 2.5 Flash Lead Enrichment Engine

Nutzt die authentifizierten Google Cloud Application Default Credentials (ADC)
auf dem GCP-Projekt 'hsb-boden' und die Vertex AI Model API.

Standardbibliothek only (urllib.request, json, subprocess, sys, argparse).
Keine externen Paket-Abhaengigkeiten.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error

PROJECT_ID = "hsb-boden"
LOCATION = "global"
MODEL_ID = "gemini-2.5-flash"
API_ENDPOINT = f"https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"

# Sicherheits-Invariante: Absolutes Sende-Verbot
REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0


def get_adc_access_token() -> str:
    """Holt einen gueltigen OAuth2-Access-Token ueber das lokale gcloud ADC-Setup."""
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            text=True,
            stderr=subprocess.PIPE
        ).strip()
        if not token:
            raise ValueError("Leerer Token zurueckgegeben.")
        return token
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Fehler beim Abruf des ADC-Tokens: {e.stderr}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("Fehler: 'gcloud' CLI nicht im PATH gefunden.\n")
        sys.exit(1)


def call_gemini(prompt: str, token: str) -> str:
    """Ruft die Vertex AI Model API synchron via REST auf."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0}
        }
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_ENDPOINT, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Vertex AI HTTP {e.code}: {err_msg}")


def parse_json_response(raw_text: str) -> dict:
    """Extrahiert sauberes JSON, auch falls Markdown-Codeblocks enthalten sind."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def enrich_lead(company_name: str, website: str, branch: str, token: str) -> dict:
    """Reichert einen Lead mit B2B-Industrieboden-Kontext fuer HSB Bodenbelaege an."""
    prompt = f"""
Du bist der KI-Recherche-Spezialist fuer die HSB Bodenbelaege GmbH (Fachbetrieb fuer hochbelastbare Reaktionsharz-, PU- und Epoxidharzböden in Industrie, Gewerbe, Käsereien, Molkereien, Pharma, Logistik und Lebensmittelbetrieben).

Analysiere das folgende Zielunternehmen:
- Firma: {company_name}
- Website: {website}
- Bisherige Branche: {branch}

Erzeuge ein valides JSON-Objekt mit exakt den folgenden Feldern:
1. "standort": Hauptsitz oder massgeblicher Produktionsstandort (Stadt, PLZ, Land z.B. "CH-9050 Appenzell"). Falls unklar, "Unbekannt".
2. "region": Region / Bundesland / Kanton (z.B. "Ostschweiz", "Thurgau", "Bayern").
3. "spezifische_branche": Praezise Industrie-Klassifizierung (z.B. "Käserei / Milchverarbeitung", "Getränkeabfüllung", "Präzisionsfertigung").
4. "belastungsart": Typische physische/chemische Belastung fuer Boeden in dieser Branche (z.B. "Nassbereich, Heisswasser, Milchsäure, Thermoschock", "Staplerverkehr, hohe Punktlasten", "Hygienezone, fugenlose Versiegelung").
5. "ansprechpartner_fokus": Relevante Ziel-Rolle fuer Kaltakquise (z.B. "Betriebsleitung / technischer Leiter", "Instandhaltung / Facility Management").
6. "bezugssatz": Ein hochprofessioneller, praegnanter Bezugssatz fuer die E-Mail-Einleitung, der das konkrete Arbeitsumfeld des Betriebs wertschaetzend aufgreift (max. 1 Satz, seriös, keine Floskeln).

Antworte ausschliesslich mit dem JSON-Objekt.
"""
    raw_response = call_gemini(prompt, token)
    return parse_json_response(raw_response)


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS - Gemini Lead Enricher")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Standard: Reine Konsolenausgabe ohne Sheet-Schreibzugriff")
    parser.add_argument("--limit", type=int, default=3, help="Anzahl zu verarbeitender Test-Leads (Standard: 3)")
    parser.add_argument("--company", type=str, help="Einzelnes Unternehmen testen")
    parser.add_argument("--website", type=str, default="", help="Website des Unternehmens")
    parser.add_argument("--branch", type=str, default="Molkerei / Lebensmittelproduktion", help="Branche")

    args = parser.parse_args()

    print("=" * 70)
    print("HSB SALES OS — GEMINI 2.5 FLASH LEAD ENRICHER (ADC & VERTEX AI)")
    print(f"GCP Project: {PROJECT_ID} | Model: {MODEL_ID}")
    print(f"Modus: {'DRY-RUN (Simulationsmodus)' if args.dry_run else 'LIVE-UPDATE'}")
    print("=" * 70)

    print("1. Authentifizierung ueber Application Default Credentials (ADC)...")
    token = get_adc_access_token()
    print("   [OK] ADC-Token erfolgreich bezogen.")

    test_leads = []
    if args.company:
        test_leads.append({
            "lead_id": "MANUAL-TEST-001",
            "firma": args.company,
            "website": args.website,
            "branche": args.branch
        })
    else:
        # Repraesentative Stichprobe aus ALL_LEADS (unvollstaendige Molkereien)
        test_leads = [
            {
                "lead_id": "HSB-20260708-00001",
                "firma": "Bodensee Kaese",
                "website": "https://bodensee-kaese.ch",
                "branche": "Molkerei / Lebensmittelproduktion"
            },
            {
                "lead_id": "HSB-20260708-00002",
                "firma": "Fuchsmilch",
                "website": "https://fuchsmilch.ch",
                "branche": "Molkerei / Lebensmittelproduktion"
            },
            {
                "lead_id": "HSB-20260708-00004",
                "firma": "Hardegger Kaese",
                "website": "https://hardegger-kaese.ch",
                "branche": "Molkerei / Lebensmittelproduktion"
            }
        ][:args.limit]

    print(f"\n2. Starte Anreicherung fuer {len(test_leads)} Lead(s) via Gemini 2.5 Flash...\n")

    results = []
    for idx, lead in enumerate(test_leads, 1):
        print(f"--- [{idx}/{len(test_leads)}] {lead['firma']} ({lead['lead_id']}) ---")
        try:
            enriched = enrich_lead(lead["firma"], lead["website"], lead["branche"], token)
            results.append({
                "lead": lead,
                "enriched": enriched
            })
            print(f"  Standort:             {enriched.get('standort')}")
            print(f"  Region:               {enriched.get('region')}")
            print(f"  Spezifische Branche:  {enriched.get('spezifische_branche')}")
            print(f"  Boden-Belastungsart:  {enriched.get('belastungsart')}")
            print(f"  Ziel-Rolle:           {enriched.get('ansprechpartner_fokus')}")
            print(f"  Personalisierungs-Satz:")
            print(f"    \"{enriched.get('bezugssatz')}\"")
            print()
        except Exception as e:
            print(f"  [FEHLER] {e}\n")

    print("=" * 70)
    print(f"FERTIG: {len(results)}/{len(test_leads)} Leads erfolgreich durch Gemini 2.5 Flash angereichert.")
    print("REAL_EXTERNAL_PROSPECT_SEND_COUNT = 0 (Human-in-the-Loop strikt gewahrt)")
    print("=" * 70)


if __name__ == "__main__":
    main()
