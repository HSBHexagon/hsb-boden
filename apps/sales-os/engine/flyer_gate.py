"""
HSB Sales OS - Visuelles PDF-Release-Gate.

Ein Datei-Hash allein beweist nur, dass eine Datei unveraendert ist - nicht,
dass sie inhaltlich richtig ist. Genau daran ist die vorige Fassung
gescheitert. Dieses Gate rendert beide Seiten und prueft den Inhalt.

Benoetigt poppler (pdftoppm, pdftotext) und Pillow.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from hsb_core import FLYERS, REPO_ROOT, sha256_file

GOLDEN_DIR = REPO_ROOT / "golden"
RENDER_DPI = 100
# Toleranz: Rendering ist zwischen poppler-Versionen minimal nicht deterministisch.
MAX_PIXEL_DRIFT_PCT = 0.35


@dataclass
class GateResult:
    owner_key: str
    passed: bool
    checks: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "",
            severity: str = "hard") -> None:
        """
        severity="hard"  -> blockiert den Versand.
        severity="warn"  -> wird protokolliert, blockiert aber nicht.

        Unterschieden wird danach, was der Empfaenger tatsaechlich sieht:
        Ein falsch gerendeter Flyer ist ein harter Fehler. Ein Mangel, der
        nur in der Textebene steckt, wird sichtbar dokumentiert statt den
        gesamten Versand zu blockieren.
        """
        self.checks[name] = {"ok": ok, "detail": detail, "severity": severity}
        if ok:
            return
        if severity == "hard":
            self.passed = False
            self.failures.append(f"{name}: {detail}")
        else:
            self.warnings.append(f"{name}: {detail}")


def _require(tool: str) -> None:
    if shutil.which(tool) is None:
        raise RuntimeError(f"Benoetigtes Werkzeug fehlt: {tool} (brew install poppler)")


def render_pages(pdf: Path, outdir: Path, dpi: int = RENDER_DPI) -> list[Path]:
    _require("pdftoppm")
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = outdir / pdf.stem
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        check=True, capture_output=True)
    return sorted(outdir.glob(f"{pdf.stem}-*.png"))


def pdf_text(pdf: Path, page: int) -> str:
    _require("pdftotext")
    res = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
        check=True, capture_output=True, text=True)
    return res.stdout


def page_count(pdf: Path) -> int:
    _require("pdfinfo")
    res = subprocess.run(["pdfinfo", str(pdf)], check=True,
                         capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    return 0


MIN_PHOTO_W = 200
MIN_PHOTO_H = 150


def count_project_photos(pdf: Path, page: int = 2) -> int:
    """
    Zaehlt die grossen Projektfotos auf einer Seite ueber die eingebetteten
    Bild-XObjects - deterministisch statt per Pixel-Heuristik.

    Die korrekte Seite 2 traegt genau vier Referenzflaechen-Fotos
    (ca. 509x394 px). Die fehlerhafte Vorfassung hatte nur ein einziges
    grosses Foto - dieser Test unterscheidet beide zuverlaessig.
    Kleine Kundenlogos (<= 384x100) und das Hexagon-Logo fallen durch die
    Groessenschwelle heraus, smask-Eintraege werden ignoriert.
    """
    _require("pdfimages")
    res = subprocess.run(
        ["pdfimages", "-list", "-f", str(page), "-l", str(page), str(pdf)],
        check=True, capture_output=True, text=True)

    count = 0
    for line in res.stdout.splitlines():
        parts = line.split()
        # Erwartetes Format: page num type width height color comp bpc enc ...
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        if parts[2] != "image":          # smask/stencil ignorieren
            continue
        try:
            width, height = int(parts[3]), int(parts[4])
        except ValueError:
            continue
        colorspace = parts[5]
        # Das Hexagon-Logo ist icc/jpeg-kodiert und faellt hier heraus;
        # die Projektfotos sind rgb-kodiert.
        if colorspace != "rgb":
            continue
        if width >= MIN_PHOTO_W and height >= MIN_PHOTO_H:
            count += 1
    return count


def check_flyer(owner_key: str, pdf: Path | None = None,
                update_golden: bool = False) -> GateResult:
    flyer = FLYERS[owner_key]
    pdf = pdf or flyer.path
    res = GateResult(owner_key=owner_key, passed=True)

    # 1. Existenz + Hash
    if not pdf.exists():
        res.add("datei_vorhanden", False, str(pdf))
        return res
    res.add("datei_vorhanden", True, str(pdf))

    actual = sha256_file(pdf)
    res.add("sha256", actual == flyer.sha256,
            f"erwartet {flyer.sha256[:16]}, gefunden {actual[:16]}")

    # 2. Seitenzahl
    pages = page_count(pdf)
    res.add("zwei_seiten", pages == 2, f"{pages} Seiten")
    if pages < 2:
        return res

    # 3. Textinhalt Seite 2: richtiger Ansprechpartner + E-Mail
    t2 = pdf_text(pdf, 2)
    # Eigene Mailadresse MUSS vorhanden sein - das ist hart.
    res.add("mailadresse", flyer.mailbox in t2, f"'{flyer.mailbox}' auf Seite 2")
    # Namensprüfung Seite 2
    res.add("ansprechpartner", flyer.display_name in t2,
            f"'{flyer.display_name}' auf Seite 2 (Textebene)")
    res.add("cta_vorhanden", "Belastungsprofil" in t2, "CTA-Block Seite 2")

    # 4. Textinhalt Seite 1
    t1 = pdf_text(pdf, 1)
    res.add("seite1_headline", "Produktion" in t1, "Headline Seite 1")

    with tempfile.TemporaryDirectory() as tmp:
        pngs = render_pages(pdf, Path(tmp))
        if len(pngs) < 2:
            res.add("render", False, f"nur {len(pngs)} Seiten gerendert")
            return res
        res.add("render", True, f"{len(pngs)} Seiten gerendert")

        # 5. Die vier Projektbilder auf Seite 2
        blocks = count_project_photos(pdf, page=2)
        res.add("vier_projektbilder", blocks == 4,
                f"{blocks} Projektfotos erkannt (erwartet 4)")

        # 6. Golden-Reference-Regression
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        for i, png in enumerate(pngs[:2], start=1):
            golden = GOLDEN_DIR / f"{owner_key}-seite{i}.png"
            if update_golden or not golden.exists():
                shutil.copy(png, golden)
                res.add(f"golden_seite{i}", True, "Referenz neu angelegt")
                continue
            drift = _pixel_drift(png, golden)
            res.add(f"golden_seite{i}", drift <= MAX_PIXEL_DRIFT_PCT,
                    f"Abweichung {drift:.3f}% (max {MAX_PIXEL_DRIFT_PCT}%)")
    return res


def _pixel_drift(a_path: Path, b_path: Path) -> float:
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        return 100.0
    aw, ah = a.size
    ap, bp = a.load(), b.load()
    step = max(1, aw // 300)
    diff = total = 0
    for y in range(0, ah, step):
        for x in range(0, aw, step):
            total += 1
            r1, g1, b1 = ap[x, y]
            r2, g2, b2 = bp[x, y]
            if abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2) > 30:
                diff += 1
    return (diff / total * 100) if total else 100.0


def run_all(update_golden: bool = False) -> dict:
    results = {}
    overall = True
    all_warnings = []
    for key in FLYERS:
        r = check_flyer(key, update_golden=update_golden)
        results[key] = {"passed": r.passed, "checks": r.checks,
                        "failures": r.failures, "warnings": r.warnings}
        all_warnings.extend(f"{key}: {w}" for w in r.warnings)
        overall = overall and r.passed
    return {"VISUAL_PDF_GATE": "PASS" if overall else "FAIL",
            "warnings": all_warnings, "flyers": results}


if __name__ == "__main__":
    import sys
    out = run_all(update_golden="--update-golden" in sys.argv)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0 if out["VISUAL_PDF_GATE"] == "PASS" else 1)
