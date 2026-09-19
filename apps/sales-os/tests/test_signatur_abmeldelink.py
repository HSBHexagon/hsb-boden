import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine"))
os.environ.setdefault("HSB_ADAPTER_URL_JOEL", "https://example.invalid/joel")
os.environ.setdefault("HSB_ADAPTER_URL_JORDI", "https://example.invalid/jordi")
import batch_engine, run_100_batch, run_ultimate_test

def test_abmeldelink_in_allen_python_signaturen():
    for mod in (batch_engine, run_100_batch, run_ultimate_test):
        html = mod.signatur_html("Joel Cherino Diaz", "j-cherino@hsb-boden.de", "0151 21886891")
        assert 'href="mailto:j-cherino@hsb-boden.de?subject=Abmelden"' in html, f"mailto missing in {mod.__name__}"
        assert "Hier abmelden" in html, f"Hier abmelden missing in {mod.__name__}"
        assert "https://www.hsb-boden.de/abmelden" in html, f"abmelden URL missing in {mod.__name__}"
        assert html.index("Hier abmelden") < html.index("Geschäftsführer"), f"order wrong in {mod.__name__}"
