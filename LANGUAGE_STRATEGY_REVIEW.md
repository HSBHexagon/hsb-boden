# LANGUAGE_STRATEGY_REVIEW.md

Stand: 2026-06-11
Projekt: HEXAFLOOR / HSB-Boden
Thema: Optimierung der Mehrsprachigkeits-Wirkung

## 1. IST-Zustand der Implementierung
*   **Technik:** Die Website verfügt über 5 internationale Landingpages (`/en/`, `/fr/`, `/nl/`, `/pl/`, `/tr/`).
*   **Erkennung:** Eine automatische Browser-Spracherkennung (`LanguageSuggest.astro`) ist aktiv und zeigt ein dezentes Banner für Nicht-DE-Besucher.
*   **Sichtbarkeit:** Im Header (Desktop & Mobile) ist permanent ein 6-Sprachen-Umschalter (`DE · EN · TR · NL · PL · FR`) integriert.
*   **Wartung:** Zentrales Management über `src/lib/i18n.ts`.

## 2. Bewertung gegen Zielzustand

| Zielvorgabe | Status | Analyse |
|---|---|---|
| Primärsprache Deutsch | ✅ Erfüllt | Kerninhalte sind tiefgreifend auf Deutsch vorhanden. |
| Automatische Spracherkennung | ✅ Erfüllt | Funktioniert via Client-seitigem Skript zuverlässig. |
| Kein dauerhaftes 6-Sprachen-Menü | ❌ Nicht erfüllt | Der Header-Umschalter ist immer präsent und wirkt "unruhig". |
| Maximale Vertrauenswirkung | ⚠️ Eingeschränkt | Ein spezialisierter deutscher Industriebetrieb wirkt authentischer, wenn er primär Deutsch spricht und Internationalisierung als "Service" (Banner) anbietet, statt als "Portal" (6er-Liste). |

## 3. Empfohlene minimale Änderung (The "B2B Professional" Fix)

1.  **Header bereinigen:** Den Sprachen-Umschalter (`languages.map(...)`) aus `Header.astro` entfernen.
2.  **Banner beibehalten:** `LanguageSuggest.astro` bleibt die primäre Brücke für internationale Kunden. Sie "sieht" den Kunden und bietet die Lösung an.
3.  **Diskreter Rückweg:** Nur auf den internationalen Landingpages (z.B. `/en/`) einen kleinen Link "Visit German Site" (bereits im Content vorhanden) oder einen einfachen `DE`-Button im Header einblenden, um den Weg zurück zur Hauptseite zu weisen.

## 4. Fazit
Die technische Grundlage ist exzellent. Die visuelle Reduktion auf "Deutsch als Standard" wird die wahrgenommene Expertise als deutscher Qualitätsschmied stärken. Der Wartungsaufwand sinkt, da die Navigation im Header kompakter und fokussierter wird.
