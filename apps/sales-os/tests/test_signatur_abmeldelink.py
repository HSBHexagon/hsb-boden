import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "engine"))
import batch_engine, run_100_batch, run_ultimate_test

def test_abmeldelink_in_allen_python_signaturen():
    for mod in (batch_engine, run_100_batch, run_ultimate_test):
        html = mod.signatur_html("Joel Cherino Diaz", "j-cherino@hsb-boden.de", "0151 21886891")
        assert 'href="mailto:j-cherino@hsb-boden.de?subject=Abmelden"' in html, mod.__name__
        assert "Hier abmelden" in html
        assert html.index("Hier abmelden") < html.index("Geschäftsführer")
