# Das Zero-Bullshit Performance Manifest für KI-Agenten

**Datum:** 2026-10-08
**Thema:** Radikale Ehrlichkeit über maximale Performance, Tool-Nutzung, Parallel-Agenten und Autonomie-Loops in Antigravity/Superpowers.

---

## 1. Tool-Nutzung & Schnelligkeit: Präzision schlägt Brute-Force

Die größte Lüge in der Agenten-Orchestrierung ist, dass mehr Tools und mehr Kontext zu besseren Ergebnissen führen. Das Gegenteil ist der Fall.

* **Die Prompt-Cache-Realität:** Jeder asynchrone Pager-Output, jedes sinnlose Laden einer 5.000-Zeilen-Datei und jede Ladeanimation zerstört den Prompt-Cache. Wer den Cache bricht, halbiert die Geschwindigkeit und verzehnfacht die Kosten.
* **Die goldene Regel:** Tools müssen chirurgisch eingesetzt werden. Statt `ls -la` nutzt man `find` oder limitiert die Ausgaben. Statt eine ganze Logdatei zu lesen, wird `grep` genutzt. 
* **Fazit:** Maximale Performance entsteht nicht durch das Ausführen vieler Tools, sondern durch das clevere **Vermeiden** von unnötigen Tool-Aufrufen.

## 2. Writing Plans: Der einzige Ausweg aus dem Halluzinations-Chaos

KI-Modelle haben ein schlechtes Kurzzeitgedächtnis für komplexe, implizite Abhängigkeiten, wenn sie sofort mit dem Coden beginnen.

* **Die Blueprint-Pflicht:** Niemals – unter keinen Umständen – darf Code geschrieben werden, bevor nicht ein schriftlicher Plan (`writing-plans`) existiert. 
* **Warum es schneller ist:** Ein vorab geschriebener Plan zwingt den Agenten, Randfälle (Edge Cases) und Systemgrenzen zu erkennen, bevor er sich in einer Datei verrennt. 
* **Fazit:** Wer die 30 Sekunden für einen Plan spart, verliert später 3 Stunden in einer Debugging-Hölle.

## 3. Parallel Agents & Superpowers Dispatch: Die Overhead-Falle

Es klingt verlockend: "Lass uns einfach 5 Agenten parallel auf das Repo ansetzen." In der Realität ist das oft ein Desaster.

* **Der Synchronisations-Kollaps:** Wenn mehrere Agenten an verknüpften Dateien arbeiten, produzieren sie Git-Merge-Konflikte, überschreiben sich gegenseitig und verbringen mehr Zeit mit der Fehlerbehebung (Overhead) als mit der eigentlichen Lösung.
* **Wann Parallelisierung funktioniert:** Ausschliesslich bei **strikt orthogonalen (isolierten) Workloads**. Agent A liest eine Doku. Agent B scrapt eine Website. Agent C schreibt Unit-Tests für ein isoliertes Modul.
* **Fazit:** Wenn der Kontext stark verzahnt ist, ist ein einzelner, mächtiger Agent (im Pro-Modus), der den Plan sequenziell, aber rasend schnell abarbeitet, jedem Agenten-Schwarm überlegen.

## 4. Autonomie-Loops (`/loop` & `/goal`): Vertrauen erfordert harte Verifikation

Einen Agenten in einen `/loop` zu schicken und zu hoffen, dass er das Problem löst, ist Naivität.

* **Die Test-Driven-Loop-Regel:** Ein `/loop` ist nur so gut wie seine Exit-Condition. Eine heuristische Selbstbewertung ("Sieht gut aus") reicht nicht. Der Exit muss ein deterministischer Terminal-Befehl sein (z.B. `npm run check` oder `pytest` gibt Exit Code 0).
* **Der 3-Strikes-Abbruch:** Wenn ein Agent im `/loop` nach drei Versuchen denselben Fehler produziert, ist der Ansatz fundamental falsch. Harter Abbruch, Plan neu schreiben.
* **`/goal` und Langläufer:** Echte Fire-and-Forget-Goals (Ultragoals) dürfen niemals ungesichert im `main`-Branch laufen. Sie erfordern zwingend isolierte Git-Worktrees und regelmäßige Checkpoint-Commits (Snapshot-Rollbacks).

---

## Zusammenfassung: Die 4 Säulen der Maximal-Performance

1. **Weniger Lärm:** Halte den Kontext sauber und den Cache stabil.
2. **Immer Planen:** Code folgt dem Design, niemals umgekehrt.
3. **Klug Isolieren:** Parallele Agenten nur für getrennte Pfade.
4. **Hart Verifizieren:** Autonomie braucht deterministische Tests als Leitplanken.
