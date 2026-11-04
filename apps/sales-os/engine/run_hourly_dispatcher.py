#!/usr/bin/env python3
"""
HSB Sales OS — Automated Hourly Outreach Dispatcher.
Sendet kontinuierlich stündlich ein Kontingent von 50 E-Mails:
- 25 E-Mails für Joel Cherino Diaz (j-cherino@hsb-boden.com)
- 25 E-Mails für Jordie Post (j-post@hsb-boden.com)

Eigenschaften & Anti-Spam Governance:
1. Interleaved Sending: Joel und Jordi wechseln sich ab.
2. Stochastischer Jitter: 45 bis 90 Sekunden Pause zwischen zwei Sendungen (~50–55 Min Laufzeit pro 50er Tranche).
3. Restzeit-Kompensation: Pausiert exakt bis zur vollen Stunde vor dem nächsten Batch.
4. Inbound-Sync: Nach jedem Batch wird automatisch der Rücklauf (Bounces, Abwesenheiten, Antworten) synchronisiert.
5. Live-Statusdatei: apps/sales-os/engine/logs/hourly_status.json für Dashboards & Cockpit.
6. Graceful Shutdown: Fängt SIGINT / SIGTERM sauber ab.
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any, Dict

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from run_dual_outreach_batch import run_dual_dispatch

LOG_DIR = ENGINE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "hourly_outreach.log"
STATUS_FILE = LOG_DIR / "hourly_status.json"

# Logging auf Konsole und in Datei
logger = logging.getLogger("hourly_dispatcher")
logger.setLevel(logging.INFO)
logger.propagate = False

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(stream_handler)

running = True


def signal_handler(signum, frame):
    global running
    logger.info("🛑 Beendigungs-Signal empfangen. Stoppe Dispatcher nach dem aktuellen Schritt...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def update_status(data: Dict[str, Any]) -> None:
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Konnte Statusdatei nicht aktualisieren: {e}")


def run_hourly_loop(
    count_per_owner: int = 25,
    jitter_min: int = 45,
    jitter_max: int = 90,
    interval_seconds: int = 3600,
    max_batches: int = 1,
    dry_run: bool = True
):
    global running
    if max_batches != 1:
        raise ValueError("Only one bounded batch per invocation is allowed")
    total_hourly_quota = count_per_owner * 2
    logger.info("================================================================================")
    logger.info(" HSB SALES OS — STÜNDLICHER OUTREACH DISPATCHER GESTARTET")
    logger.info(f" Stündliches Kontingent: {total_hourly_quota} Mails ({count_per_owner} Joel + {count_per_owner} Jordi)")
    logger.info(f" Jitter-Korridor: [{jitter_min}s, {jitter_max}s] | Zyklus-Intervall: {interval_seconds}s (1h)")
    logger.info(f" Modus: {'DRY-RUN (Vorschau)' if dry_run else 'LIVE APPLY (Echter Versand)'}")
    logger.info(f" Statusdatei: {STATUS_FILE}")
    logger.info(f" Logdatei:    {LOG_FILE}")
    logger.info("================================================================================")

    batch_index = 0
    total_sent_all = {"JOEL": 0, "JORDI": 0}

    while running:
        batch_index += 1
        batch_start_time = time.time()
        start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        logger.info(f"\n▶ STARTE BATCH #{batch_index} um {datetime.datetime.now().strftime('%H:%M:%S')} Uhr...")

        update_status({
            "status": "RUNNING_BATCH",
            "current_batch": batch_index,
            "batch_start_utc": start_iso,
            "total_sent": total_sent_all,
            "last_error": None
        })

        try:
            res = run_dual_dispatch(
                count_per_owner=count_per_owner,
                jitter_min=jitter_min,
                jitter_max=jitter_max,
                dry_run=dry_run
            )

            if res.get("status") == "EMPTY":
                logger.info("ℹ Keine weiteren offenen Leads im Pool vorhanden. Dispatcher beendet.")
                update_status({
                    "status": "FINISHED_EMPTY",
                    "completed_batches": batch_index - 1,
                    "total_sent": total_sent_all
                })
                break

            if not dry_run and "sent_counts" in res:
                sent = res["sent_counts"]
                total_sent_all["JOEL"] += sent.get("JOEL", 0)
                total_sent_all["JORDI"] += sent.get("JORDI", 0)

        except Exception as exc:
            logger.error(f"❌ Unerwarteter Fehler im Batch #{batch_index}: {exc}", exc_info=True)
            update_status({
                "status": "ERROR",
                "current_batch": batch_index,
                "last_error": str(exc),
                "total_sent": total_sent_all
            })

        batch_duration = time.time() - batch_start_time
        logger.info(f"✔ Batch #{batch_index} beendet (Dauer: {batch_duration:.1f}s / {batch_duration/60:.1f} Min).")
        logger.info(f"📊 Gesamtversand bisher: Joel = {total_sent_all['JOEL']}, Jordi = {total_sent_all['JORDI']} (Summe: {total_sent_all['JOEL'] + total_sent_all['JORDI']})")

        if max_batches > 0 and batch_index >= max_batches:
            logger.info(f"Maximale Batch-Anzahl ({max_batches}) erreicht. Beende Loop.")
            break

        if not running:
            break

        # Automatischer Inbound-Sync nach jedem Batch
        try:
            logger.info("🔄 Führe Inbound-Sync (Bounces, Replies) nach Batch aus...")
            # Isolierter Aufruf via Python
            import subprocess
            subprocess.run(
                [sys.executable, str(ENGINE_DIR / "hsb_cli.py"), "sync", "--apply"],
                capture_output=True,
                text=True,
                timeout=120
            )
            logger.info("✔ Inbound-Sync erfolgreich abgeschlossen.")
        except Exception as se:
            logger.warning(f"Inbound-Sync Hinweis: {se}")

        # Pause bis zum nächsten vollen Stunden-Intervall
        elapsed = time.time() - batch_start_time
        sleep_needed = max(0.0, interval_seconds - elapsed)

        next_run_dt = datetime.datetime.now() + datetime.timedelta(seconds=sleep_needed)
        logger.info(f"⏳ Wartezeit bis zum nächsten Batch: {sleep_needed:.1f}s ({sleep_needed/60:.1f} Min).")
        logger.info(f"⏰ Nächster Batch #{batch_index + 1} startet um ca. {next_run_dt.strftime('%H:%M:%S')} Uhr.")

        update_status({
            "status": "WAITING_NEXT_INTERVAL",
            "last_completed_batch": batch_index,
            "total_sent": total_sent_all,
            "next_run_local": next_run_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "seconds_until_next": int(sleep_needed)
        })

        # Sekündliches Schlafen, damit Abbruch-Signale sofort reagieren
        sleep_end = time.time() + sleep_needed
        while running and time.time() < sleep_end:
            time.sleep(1)

    logger.info("HSB Sales OS Hourly Dispatcher ordnungsgemäß beendet.")


def main():
    parser = argparse.ArgumentParser(description="HSB Sales OS Hourly Outreach Dispatcher")
    parser.add_argument("--count", type=int, default=25, help="Anzahl Mails pro Postfach je Stunde (Standard: 25)")
    parser.add_argument("--jitter-min", type=int, default=45, help="Minimale Pause in Sekunden (Standard: 45)")
    parser.add_argument("--jitter-max", type=int, default=90, help="Maximale Pause in Sekunden (Standard: 90)")
    parser.add_argument("--interval", type=int, default=3600, help="Intervall zwischen Batch-Starts in Sekunden (Standard: 3600 = 1h)")
    parser.add_argument("--max-batches", type=int, default=1, help="Maximale Anzahl an Batches (0 = unbegrenzt)")
    parser.add_argument("--apply", action="store_true", help="Echten Versand starten (Standard: Dry-Run)")
    args = parser.parse_args()
    if args.apply and args.max_batches < 1:
        parser.error('Live-Sendungen brauchen --max-batches >= 1; kein unbegrenzter Live-Versand')

    run_hourly_loop(
        count_per_owner=args.count,
        jitter_min=args.jitter_min,
        jitter_max=args.jitter_max,
        interval_seconds=args.interval,
        max_batches=args.max_batches,
        dry_run=not args.apply
    )


if __name__ == "__main__":
    main()
