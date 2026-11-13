"""Summe der versendeten Nachrichten aus der Ausgabe von `hsb_cli.py send-batch` (stdin -> Zahl).

Die Ausgabe mischt Protokollzeilen mit einem mehrzeilig eingerückten JSON-Ergebnis; gewertet wird das letzte
JSON-Objekt mit `sent_counts`. Ohne ein solches Objekt ist das Ergebnis 0.
"""
from __future__ import annotations

import json
import sys


def total_sent(text: str) -> int:
    decoder = json.JSONDecoder()
    total, pos = 0, text.find('{')
    while pos != -1:
        try:
            obj, end = decoder.raw_decode(text, pos)
        except ValueError:
            pos = text.find('{', pos + 1)
            continue
        if isinstance(obj, dict) and isinstance(obj.get('sent_counts'), dict):
            total = sum(int(v) for v in obj['sent_counts'].values())
        pos = text.find('{', end)
    return total


if __name__ == '__main__':
    print(total_sent(sys.stdin.read()))
