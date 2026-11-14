"""Public model pages (/carros/<slug>): addresses and the exported data file."""
import json
import os

from scripts.export_model_pages import MIN_PRICED_YEARS, model_slug, slugify

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "frontend", "data", "models.json")


def test_addresses_are_plain_and_distinct():
    assert model_slug("Peugeot", "208") == "peugeot-208"
    assert model_slug("BMW", "Série 3") == "bmw-serie-3"
    assert model_slug("Mercedes-Benz", "Classe A") == "mercedes-benz-classe-a"
    assert model_slug("Citroën", "ë-C4") == "citroen-e-c4"
    assert model_slug("Ford", "Ka+") != model_slug("Ford", "Ka")
    assert slugify("  Fiat 500C!! ") == "fiat-500c"


def test_exported_file_is_consistent():
    data = json.load(open(DATA, encoding="utf-8"))
    models = data["models"]
    slugs = [m["slug"] for m in models]
    assert len(slugs) == len(set(slugs))
    by_slug = set(slugs)
    for m in models:
        assert m["slug"] == model_slug(m["brand"], m["model"])
        assert m["indexable"] == (len(m["prices"]) >= MIN_PRICED_YEARS and bool(m["engines"]))
        assert all(r in by_slug for r in m["related"])
        for p in m["prices"]:
            assert p["p10"] <= p["p50"] <= p["p90"] and p["n"] >= 6
        for g in m["generations"]:
            d = g["depreciation"]
            assert d is None or 0.03 <= d <= 0.25          # a fraction, never rounded to 0.1
        # only approved known issues may ever be in the file
        assert all(i.get("curated") for i in m["known_issues"])
