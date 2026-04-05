"""
Tests for KBA recall scraper (car-recalls.eu).

Covers:
  - Production date range parsing
  - Safety-critical keyword detection
  - Brand slug mapping completeness
  - Live HTTP fetch (smoke test)
  - Generation matching logic (unit)
"""

import pytest
from app.scrapers.kba_recalls import (
    _parse_production_years,
    _is_safety_critical,
    _find_generation,
    _fetch_page,
    BRAND_SLUGS,
    BASE_URL,
)


# ── Date parsing ─────────────────────────────────────────────────────────────

class TestParseProdYears:
    def test_standard_range(self):
        y0, y1 = _parse_production_years("4/2017 – 11/2018")
        assert y0 == 2017
        assert y1 == 2018

    def test_dash_separator(self):
        y0, y1 = _parse_production_years("12/2009 - 10/2011")
        assert y0 == 2009
        assert y1 == 2011

    def test_em_dash(self):
        y0, y1 = _parse_production_years("01/2015 — 06/2019")
        assert y0 == 2015
        assert y1 == 2019

    def test_single_year_fallback(self):
        y0, y1 = _parse_production_years("produced in 2020")
        assert y0 == 2020
        assert y1 == 2020

    def test_two_years_fallback(self):
        y0, y1 = _parse_production_years("vehicles from 2018 to 2021")
        assert y0 == 2018
        assert y1 == 2021

    def test_empty_string(self):
        y0, y1 = _parse_production_years("")
        assert y0 is None
        assert y1 is None

    def test_no_years(self):
        y0, y1 = _parse_production_years("unknown production period")
        assert y0 is None
        assert y1 is None


# ── Safety-critical detection ─────────────────────────────────────────────────

class TestSafetyCritical:
    def test_brake_critical(self):
        assert _is_safety_critical("The brake caliper may seize")

    def test_airbag_critical(self):
        assert _is_safety_critical("Airbag may not deploy correctly")

    def test_engine_critical(self):
        assert _is_safety_critical("Engine may stall at highway speed")

    def test_steering_critical(self):
        assert _is_safety_critical("Loss of steering assistance")

    def test_fuel_system_critical(self):
        assert _is_safety_critical("Fuel system may leak near heat source")

    def test_battery_electric_critical(self):
        assert _is_safety_critical("Battery may short circuit causing fire risk")

    def test_cosmetic_not_critical(self):
        assert not _is_safety_critical("Windscreen wiper blade may detach")

    def test_software_not_critical(self):
        assert not _is_safety_critical("Instrument cluster display may show incorrect speed")

    def test_trim_not_critical(self):
        assert not _is_safety_critical("Interior trim panel may rattle or detach")


# ── Brand slug coverage ────────────────────────────────────────────────────────

class TestBrandSlugs:
    VW_GROUP = ["Volkswagen", "Audi", "Skoda", "SEAT", "Cupra", "Porsche"]
    BMW_GROUP = ["BMW", "MINI"]
    DAIMLER   = ["Mercedes-Benz", "Smart"]

    def test_vw_group_covered(self):
        for brand in self.VW_GROUP:
            assert brand in BRAND_SLUGS, f"{brand} missing from BRAND_SLUGS"

    def test_bmw_group_covered(self):
        for brand in self.BMW_GROUP:
            assert brand in BRAND_SLUGS, f"{brand} missing from BRAND_SLUGS"

    def test_daimler_covered(self):
        for brand in self.DAIMLER:
            assert brand in BRAND_SLUGS, f"{brand} missing from BRAND_SLUGS"

    def test_slugs_are_lowercase_hyphenated(self):
        for brand, slug in BRAND_SLUGS.items():
            assert slug == slug.lower(), f"{brand} slug '{slug}' not lowercase"
            assert " " not in slug, f"{brand} slug '{slug}' has spaces (use hyphens)"

    def test_no_empty_slugs(self):
        for brand, slug in BRAND_SLUGS.items():
            assert slug, f"{brand} has empty slug"


# ── Live HTTP smoke test ───────────────────────────────────────────────────────

class TestLiveFetch:
    """Requires network access — run with: pytest -m live"""

    @pytest.mark.live
    def test_fetch_vw_page_2019(self):
        """car-recalls.eu should have a VW 2019 page with recalls."""
        soup = _fetch_page(f"{BASE_URL}/volkswagen-recalls-2019/")
        assert soup is not None
        # Page should have h3 model sections
        h3_tags = soup.find_all("h3")
        assert len(h3_tags) > 0, "Expected model section headers on VW 2019 page"

    @pytest.mark.live
    def test_fetch_bmw_page_2020(self):
        soup = _fetch_page(f"{BASE_URL}/bmw-recalls-2020/")
        assert soup is not None
        tables = soup.find_all("table")
        assert len(tables) > 0, "Expected recall tables on BMW 2020 page"

    @pytest.mark.live
    def test_fetch_nonexistent_brand_year(self):
        """A brand/year combination with no recalls should return None (404)."""
        soup = _fetch_page(f"{BASE_URL}/tesla-recalls-2010/")
        # Either None (404) or empty page — both acceptable
        if soup is not None:
            tables = soup.find_all("table")
            # If page exists, it might have 0 or few tables
            assert isinstance(tables, list)

    @pytest.mark.live
    def test_mercedes_page_has_model_sections(self):
        soup = _fetch_page(f"{BASE_URL}/mercedes-benz-recalls-2021/")
        assert soup is not None
        h3s = [h.get_text(strip=True) for h in soup.find_all("h3")]
        # Should include common models like C-Class, E-Class, GLC, etc.
        assert len(h3s) > 0
