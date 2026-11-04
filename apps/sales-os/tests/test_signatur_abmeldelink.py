import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine"))
os.environ.setdefault("HSB_ADAPTER_URL_JOEL", "https://example.invalid/joel")
os.environ.setdefault("HSB_ADAPTER_URL_JORDI", "https://example.invalid/jordi")
import batch_engine, run_100_batch, run_ultimate_test, canonical_template_factory

def test_abmeldelink_in_allen_python_signaturen():
    for mod in (batch_engine, run_100_batch, run_ultimate_test):
        html = mod.signatur_html("Joel Cherino Diaz", "j-cherino@hsb-boden.de", "0151 21886891")
        assert "Hier abmelden" in html, f"Hier abmelden missing in {mod.__name__}"
        assert "https://www.hsb-boden.de/abmelden" in html, f"abmelden URL missing in {mod.__name__}"
        # Anti-Spam & Ästhetik: Keine klobigen Tabellen-Boxen oder doppelte Mailto-Abmeldungen mehr
        assert "<table" not in html, f"HTML table for opt-out still present in {mod.__name__}"
        assert "mailto:j-cherino@hsb-boden.de?subject=Abmelden" not in html, f"Redundant mailto optout present in {mod.__name__}"

    # Verifikation, dass im fertigen Body von overhaul_drafts exakt EIN Abmelde-Link existiert
    import overhaul_drafts
    body = overhaul_drafts.build_canonical_body_2026("JOEL", "Guten Tag,")
    assert body.count("Hier abmelden") == 1, f"Linktext 'Hier abmelden' kommt nicht exakt einmal vor: count={body.count('Hier abmelden')}"
    assert body.count("/abmelden") == 1, f"Abmelde-URL kommt nicht exakt einmal vor: count={body.count('/abmelden')}"
    assert "---" not in body, "Veralteter Trennstrich-Paragraph ('---') noch im Body vorhanden"


def test_impressum_und_datenschutz_links():
    """Verifiziert § 5 TMG/DDG, § 35a GmbHG und DSGVO-Konformität in allen Signaturen."""
    # 1. Signaturen aus den Engines
    for mod in (batch_engine, run_100_batch, run_ultimate_test):
        html = mod.signatur_html("Joel Cherino Diaz", "j-cherino@hsb-boden.de", "0151 21886891")
        assert 'href="https://www.hsb-boden.de/impressum/"' in html, f"Impressum link missing/invalid in {mod.__name__}"
        assert 'href="https://www.hsb-boden.de/datenschutz/"' in html, f"Datenschutz link missing/invalid in {mod.__name__}"
        assert "Jordie Post" in html, f"GF Jordie Post missing in {mod.__name__}"
        assert "Amtsgericht Coesfeld" in html, f"Registergericht missing in {mod.__name__}"
        assert "HRB 21481" in html, f"HRB missing in {mod.__name__}"
        assert "hsb-boden.com/impressum" not in html, f"hsb-boden.com has no web SSL cert! Must use .de in {mod.__name__}"

    # 2. Canonical Template Factory
    canonical_res = canonical_template_factory.render_canonical_email(
        lead={"Lead_ID": "TEST-1", "Email": "test@example.com", "Firma": "Test GmbH"},
        owner="JOEL",
        domain="com"
    )
    c_html = canonical_res["body_html"]
    assert 'href="https://www.hsb-boden.de/impressum/"' in c_html, "Impressum missing in canonical_template_factory"
    assert 'href="https://www.hsb-boden.de/datenschutz/"' in c_html, "Datenschutz missing in canonical_template_factory"
    assert "Jordie Post" in c_html, "Jordie Post missing in canonical_template_factory"
    assert "Amtsgericht Coesfeld" in c_html, "Registergericht missing in canonical_template_factory"
    assert "HRB 21481" in c_html, "HRB missing in canonical_template_factory"
    assert "hsb-boden.com/impressum" not in c_html, "canonical_template_factory must not use .com for web links"
