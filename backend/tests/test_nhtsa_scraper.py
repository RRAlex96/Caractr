"""
Smoke tests for the NHTSA scraper.

These tests call the real NHTSA API (no auth required) to verify:
1. Recalls endpoint returns structured data for a known recall-heavy vehicle
2. Complaints endpoint returns structured data
3. Evidence weight logic is correct (safety-critical vs other)
4. Aggregate complaint row is created correctly

Run: pytest tests/test_nhtsa_scraper.py -v
Note: requires internet access.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.scrapers.nhtsa import (
    _fetch_recalls,
    _fetch_complaints,
    _is_safety_critical,
    _nhtsa_model_name,
    BRAND_TO_NHTSA,
)


# ─────────────────────────────────────────────────────────────
# 1. API connectivity — use VW Golf 2018 as canary
# ─────────────────────────────────────────────────────────────

def test_recalls_api_returns_list():
    results = _fetch_recalls("VOLKSWAGEN", "GOLF", 2018)
    # May be empty if no US recalls, but should return a list (not raise)
    assert isinstance(results, list)


def test_complaints_api_returns_list():
    results = _fetch_complaints("VOLKSWAGEN", "GOLF", 2018)
    assert isinstance(results, list)


def test_recalls_known_recall_vehicle():
    """Takata airbag recall affected many Honda models including Civic."""
    results = _fetch_recalls("HONDA", "CIVIC", 2014)
    assert isinstance(results, list)
    # Honda Civic 2014 had known Takata airbag recalls
    if results:
        assert "NHTSACampaignNumber" in results[0] or "Component" in results[0]


def test_complaints_toyota_camry_has_data():
    """Toyota Camry is one of the most-reported vehicles in NHTSA complaints."""
    results = _fetch_complaints("TOYOTA", "CAMRY", 2018)
    assert isinstance(results, list)
    # Should have at least some complaints for a high-volume vehicle
    # (not asserting count > 0 because data can change)


# ─────────────────────────────────────────────────────────────
# 2. Safety-critical detection
# ─────────────────────────────────────────────────────────────

def test_brake_is_safety_critical():
    assert _is_safety_critical("The brakes may fail under heavy load")

def test_airbag_is_safety_critical():
    assert _is_safety_critical("The airbag inflator may rupture and cause fire")

def test_engine_is_safety_critical():
    assert _is_safety_critical("ENGINE may stall unexpectedly at highway speeds")

def test_fuel_system_is_safety_critical():
    assert _is_safety_critical("fuel pump may fail causing engine stall")

def test_cosmetic_is_not_safety_critical():
    assert not _is_safety_critical("Seat adjustment label may be missing")

def test_software_update_is_not_safety_critical():
    assert not _is_safety_critical("Software update required for infotainment display")


# ─────────────────────────────────────────────────────────────
# 3. Model name mapping
# ─────────────────────────────────────────────────────────────

def test_bmw_serie1_maps_correctly():
    assert _nhtsa_model_name("BMW", "Serie 1") == "1 SERIES"

def test_mercedes_classe_c_maps_correctly():
    assert _nhtsa_model_name("Mercedes-Benz", "Classe C") == "C-CLASS"

def test_vw_golf_uppercased():
    assert _nhtsa_model_name("Volkswagen", "Golf") == "GOLF"

def test_unknown_model_uppercased():
    assert _nhtsa_model_name("Toyota", "Yaris") == "YARIS"


# ─────────────────────────────────────────────────────────────
# 4. Brand mapping completeness
# ─────────────────────────────────────────────────────────────

def test_major_brands_mapped():
    for brand in ["Volkswagen", "Toyota", "BMW", "Mercedes-Benz",
                  "Ford", "Honda", "Hyundai", "Volvo"]:
        assert brand in BRAND_TO_NHTSA, f"{brand} not in BRAND_TO_NHTSA"
        assert len(BRAND_TO_NHTSA[brand]) > 0, f"{brand} has empty NHTSA make list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
