"""Listing -> catalogue model. Each 'used to' case below failed against the
production catalogue on 2026-11-13: catalogue names with an accent never
matched, so those listings were analysed with no catalogue data at all."""
import pytest

from app.services.ad_analysis_service import _models_compatible, match_catalogue_model


def _cat():
    rows = [
        ("BMW", "Série 1", "compacto"), ("BMW", "Série 2 Active Tourer", "mpv"),
        ("BMW", "Série 2 Gran Coupé", "compacto"), ("BMW", "Série 3", "berlina"),
        ("BMW", "Série 5", "berlina"), ("BMW", "X1", "suv"), ("BMW", "530", None),     # 530: a stub
        ("Citroën", "C3", "citadino"), ("Citroën", "C4", "compacto"), ("Citroën", "C5 Aircross", "suv"),
        ("Renault", "Mégane", "compacto"), ("Renault", "Scénic", "mpv"), ("Renault", "Clio", "citadino"),
        ("Audi", "A3", "compacto"), ("Audi", "A4", "berlina"), ("Audi", "Q3", "suv"),
        ("Volkswagen", "Golf", "compacto"), ("Volkswagen", "Passat", "berlina"), ("Volkswagen", "Tiguan", "suv"),
        ("Mercedes-Benz", "Classe A", "compacto"), ("Mercedes-Benz", "Classe E", "berlina"),
        ("Mercedes-Benz", "CLA", "berlina"), ("Mercedes-Benz", "GLA", "suv"), ("Mercedes-Benz", "E Coupé", "compacto"),
        ("Land Rover", "Range Rover Evoque", "suv"), ("Land Rover", "Range Rover Velar", "suv"),
        ("Toyota", "Corolla", "compacto"), ("Toyota", "Yaris", "citadino"), ("Toyota", "Yaris Cross", "suv"),
        ("DS", "7", "suv"), ("MINI", "Cooper", "citadino"), ("MINI", "Countryman", "suv"), ("Volvo", "V60", "carrinha"), ("Skoda", "Octavia", "compacto"),
        ("Peugeot", "308", "compacto"), ("Peugeot", "3008", "suv"), ("Fiat", "500", "citadino"), ("Fiat", "500X", "suv"),
        ("Peugeot", "208", "citadino"), ("Peugeot", "E-308", "compacto"), ("Opel", "Mokka", "suv"),
        ("Opel", "Grandland", "suv"), ("Kia", "Niro", "suv"), ("Hyundai", "Kona", "suv"), ("MG", "HS", "suv"),
        ("Honda", "Jazz", "citadino"),
    ]
    return [{"id": i + 1, "brand_name": b, "model_name": m, "body_type": body} for i, (b, m, body) in enumerate(rows)]


def _match(brand, model):
    row = match_catalogue_model(_cat(), brand, model, model.split()[0])
    return f"{row['brand_name']} {row['model_name']}" if row else None


@pytest.mark.parametrize("brand, model, expected", [
    # accents in the catalogue name — used to miss
    ("Renault", "Mégane", "Renault Mégane"),
    ("Renault", "Megane", "Renault Mégane"),
    ("Renault", "Mégane Sport Tourer", "Renault Mégane"),
    ("Citroën", "C3", "Citroën C3"),
    ("Citroen", "C3", "Citroën C3"),
    ("Citroën", "C5 Aircross", "Citroën C5 Aircross"),
    ("BMW", "Série 3", "BMW Série 3"),
    # BMW numbers — used to miss, or to stick to a stub
    ("BMW", "320", "BMW Série 3"),
    ("BMW", "118", "BMW Série 1"),
    ("BMW", "530", "BMW Série 5"),                 # not the "530" stub
    ("BMW", "218 Active Tourer", "BMW Série 2 Active Tourer"),
    ("BMW", "220 Gran Coupé", "BMW Série 2 Gran Coupé"),
    ("BMW", "X1", "BMW X1"),
    # body variants resolve to the base model
    ("Audi", "A3 Sportback", "Audi A3"),
    ("Audi", "A4 Avant", "Audi A4"),
    ("Audi", "Q3 Sportback", "Audi Q3"),
    ("Volkswagen", "Golf Variant", "Volkswagen Golf"),
    ("VW", "Passat Variant", "Volkswagen Passat"),
    ("Toyota", "Corolla Touring Sports", "Toyota Corolla"),
    ("Skoda", "Octavia Break", "Skoda Octavia"),
    ("Škoda", "Octavia", "Skoda Octavia"),
    # Mercedes
    ("Mercedes-Benz", "A 180", "Mercedes-Benz Classe A"),
    ("Mercedes-Benz", "E 220", "Mercedes-Benz Classe E"),
    ("Mercedes", "CLA 200", "Mercedes-Benz CLA"),
    ("Mercedes-Benz", "GLA 200", "Mercedes-Benz GLA"),
    # brand repeated in the model name
    ("DS", "DS 7", "DS 7"),
    ("Mini", "Cooper", "MINI Cooper"),
    # a longer model name is its own model
    ("Toyota", "Yaris Cross", "Toyota Yaris Cross"),
    ("Toyota", "Yaris", "Toyota Yaris"),
    ("Fiat", "500X", "Fiat 500X"),
    ("Fiat", "500", "Fiat 500"),
    ("Mercedes-Benz", "Classe CLA", "Mercedes-Benz CLA"),
    ("Mercedes-Benz", "E 220 Coupé", "Mercedes-Benz E Coupé"),
    ("Mercedes-Benz", "A180", "Mercedes-Benz Classe A"),
    ("MINI", "Cooper S", "MINI Cooper"),
    ("MINI", "One", "MINI Cooper"),
    ("BMW", "320d", "BMW Série 3"),
    ("Volvo", "V60 Cross Country", "Volvo V60"),
    ("Peugeot", "3008", "Peugeot 3008"),
    ("Peugeot", "308 SW", "Peugeot 308"),
    # the electric version filed under its own name
    ("Peugeot", "e-208", "Peugeot 208"),
    ("Peugeot", "E-308", "Peugeot E-308"),          # its own catalogue model: the exact name wins
    ("Peugeot", "e-308 SW", "Peugeot E-308"),
    ("Peugeot", "e-3008", "Peugeot 3008"),
    ("Citroën", "ë-C4", "Citroën C4"),
    ("Opel", "Mokka-e", "Opel Mokka"),
    ("Fiat", "500e", "Fiat 500"),
    ("Kia", "e-Niro", "Kia Niro"),
    ("Volkswagen", "e-Golf", "Volkswagen Golf"),
    # another name the market uses
    ("Hyundai", "Kauai", "Hyundai Kona"),
    ("Hyundai", "Kauai Electric", "Hyundai Kona"),
    ("MG", "EHS", "MG HS"),
    ("Opel", "Grandland X", "Opel Grandland"),
    ("Renault", "Scenic E-Tech", "Renault Scénic"),
])
def test_matches(brand, model, expected):
    assert _match(brand, model) == expected


@pytest.mark.parametrize("brand, model", [
    ("BMW", "640 Gran Coupé"),        # was analysed as a Série 2 Gran Coupé
    ("BMW", "740"),                   # no Série 7 in the catalogue
    ("Land Rover", "Range Rover"),    # not an Evoque or a Velar
    ("Renault", "Kangoo"),
    ("Volkswagen", "Arteon Shooting Brake"),
    ("Renault", "Grand Scénic"),      # "Grand" can name another car (Grand Vitara)
    ("Citroën", "C4 Cactus"),         # was a C4
    ("Citroën", "C3 Picasso"),        # was a C3
    ("Renault", "Kangoo E-Tech"),     # was a Renault 5 E-Tech
    ("Renault", "Mégane E-Tech"),     # an electric crossover, not a Mégane
    ("Toyota", "Corolla Cross"),      # was a Corolla
    ("Toyota", "Yaris Verso"),
    ("BMW", "1602"),                  # a classic, not a Série 1
    ("BMW", "502"),
    ("BMW", "218"),                   # Active Tourer or Gran Coupé? not known
    ("BMW", "Série 2"),
    ("Audi", "TT RS Coupé"),
    ("Tesla", "Model X"),             # brand not in this catalogue at all
    ("Honda", "e"),                   # a model of its own, not "the electric nothing"
    ("Audi", "e-tron"),
    ("Fiat", "500e C"),               # the electric convertible
    ("Citroën", "ë-C4 X"),            # the C4 X is another body, not in this catalogue
    ("Fiat", "600e"),
    ("Opel", "Combo-e Life"),
])
def test_unknown_models_do_not_match_something_else(brand, model):
    assert _match(brand, model) is None


def test_a_stub_is_returned_only_by_its_exact_name():
    cat = _cat() + [{"id": 99, "brand_name": "Renault", "model_name": "Kangoo", "body_type": None}]
    hit = match_catalogue_model(cat, "Renault", "Kangoo", "Kangoo")
    assert hit and hit["id"] == 99
    assert match_catalogue_model(cat, "Renault", "Kangoo Maxi Van", "Kangoo") is None


def test_mini_countryman_is_not_the_hatch():
    assert _match("MINI", "Countryman") == "MINI Countryman"
    assert _match("MINI", "Cooper Countryman") is None


def test_shared_body_word_is_not_a_shared_model():
    assert _models_compatible("640 Gran Coupé", "Série 2 Gran Coupé") is False
    assert _models_compatible("Range Rover Velar", "Range Rover Evoque") is False
    assert _models_compatible("Corolla Touring Sports", "Corolla") is True
    assert _models_compatible("Golf", "Golf") is True
