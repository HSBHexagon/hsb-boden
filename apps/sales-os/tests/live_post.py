#!/usr/bin/env python3
"""Fuehrt genau den POST aus, den UrlFetchApp im Apps Script macht.

Node kann kein synchrones HTTP; das Apps-Script-Modell ist aber synchron.
Deshalb dieser kleine Helfer statt einer umgebauten Aufrufkette.

Aufruf: live_post.py <arbeitsverzeichnis>
Erwartet dort `live_url.txt` und `live_payload.json`, gibt die Antwort als
JSON auf der Standardausgabe zurueck.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

if len(sys.argv) < 2:
    raise SystemExit("Aufruf: live_post.py <arbeitsverzeichnis>")

hier = pathlib.Path(sys.argv[1])
url = (hier / "live_url.txt").read_text().strip()
payload = (hier / "live_payload.json").read_bytes()

req = urllib.request.Request(url, data=payload, method="POST")
req.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print(json.dumps({"code": r.getcode(),
                          "text": r.read().decode("utf-8", "replace")}))
except urllib.error.HTTPError as e:
    print(json.dumps({"code": e.code,
                      "text": e.read().decode("utf-8", "replace")}))
