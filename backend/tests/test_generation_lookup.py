"""Which generation a car belongs to when two generations contain its year.

The petrol Fiat 500 (to 2024) and the electric 500e (from 2020) are different
cars sold side by side. The lookup used to return the newest row, so every
2020-or-later petrol 500 was treated as a 500e.
"""
from app.services.ad_analysis_service import _get_generation_window, _pick_generation

PETROL_500 = {"id": 363, "year_start": 2016, "year_end": 2024, "fuel_type": None}
ELECTRIC_500E = {"id": 35, "year_start": 2020, "year_end": None, "fuel_type": "eletrico"}
BOTH = [ELECTRIC_500E, PETROL_500]          # newest first, as the query returns them


def test_petrol_and_hybrid_cars_stay_out_of_the_electric_generation():
    assert _pick_generation(BOTH, "Gasolina")["id"] == 363
    assert _pick_generation(BOTH, "Híbrido")["id"] == 363
    assert _pick_generation(BOTH, "GPL")["id"] == 363


def test_electric_car_gets_the_electric_generation():
    assert _pick_generation(BOTH, "Elétrico")["id"] == 35
    assert _pick_generation(BOTH, "eletrico")["id"] == 35
    assert _pick_generation(BOTH, "Electric")["id"] == 35


def test_unknown_fuel_does_not_assume_the_fuel_specific_generation():
    assert _pick_generation(BOTH, None)["id"] == 363
    assert _pick_generation(BOTH, "")["id"] == 363


def test_fuel_specific_generation_is_the_last_resort():
    # 2026 hybrid 500: the petrol row ended in 2024, only the 500e row contains the year.
    assert _pick_generation([ELECTRIC_500E], "Híbrido")["id"] == 35


def test_ordinary_models_still_get_the_newest_matching_generation():
    older = {"id": 1, "year_start": 2012, "year_end": 2019, "fuel_type": None}
    newer = {"id": 2, "year_start": 2019, "year_end": None, "fuel_type": None}
    assert _pick_generation([newer, older], "Diesel")["id"] == 2
    assert _pick_generation([older, newer], "Diesel")["id"] == 2      # order of rows is irrelevant
    assert _pick_generation([older], "Diesel")["id"] == 1
    assert _pick_generation([], "Diesel") is None


class _FakeDb:
    def __init__(self, rows):
        self.rows, self.params = rows, None

    def execute(self, _sql, params):
        self.params = params
        return self

    def mappings(self):
        return self

    def fetchall(self):
        return self.rows


def test_lookup_passes_the_cars_fuel_through():
    db = _FakeDb(BOTH)
    assert _get_generation_window(db, 16, 2022, "Gasolina") == (2016, 2024, 363)
    assert _get_generation_window(db, 16, 2022, "Elétrico") == (2020, None, 35)
    assert db.params == {"model_id": 16, "year": 2022}
    assert _get_generation_window(_FakeDb([]), 16, 1990, "Gasolina") is None
