"""Yearly depreciation of a generation from the medians of its registration
years: a weighted fit, and no figure when the data cannot support one."""
import pytest

from app.services.depreciation import _compute_annual_depreciation


def _years(start_price, rate, years, n=20, first_year=2015):
    """Medians falling `rate` a year with age; newest year = start_price."""
    newest = first_year + years - 1
    return [(y, start_price * (1 - rate) ** (newest - y), n) for y in range(first_year, newest + 1)]


def test_recovers_the_rate_of_a_clean_curve():
    result = _compute_annual_depreciation(_years(25000, 0.10, 6))
    assert result["pct_year"] == pytest.approx(0.10, abs=0.002)
    curve = result["curve"]
    assert curve[0] == {"age": 0, "pct_of_new": 1.0, "year": 2020, "p50": 25000}
    assert [p["age"] for p in curve] == [0, 1, 2, 3, 4, 5]


def test_a_thin_odd_newest_year_does_not_set_the_rate():
    # Three listings of a top trim in the newest year: 40% above the trend.
    # Measured against the newest year alone, the generation lost 20% a year.
    data = _years(20000, 0.08, 6, n=40)
    data[-1] = (data[-1][0], data[-1][1] * 1.4, 5)
    result = _compute_annual_depreciation(data)
    assert result is not None
    assert result["pct_year"] == pytest.approx(0.08, abs=0.02)


def test_no_figure_from_too_little():
    assert _compute_annual_depreciation(_years(20000, 0.10, 2)) is None            # two years
    assert _compute_annual_depreciation(_years(20000, 0.10, 5, n=5)) is None       # 25 listings in all
    assert _compute_annual_depreciation([]) is None


def test_no_figure_outside_a_plausible_rate():
    assert _compute_annual_depreciation(_years(8000, 0.005, 6)) is None    # prices have flattened
    assert _compute_annual_depreciation(_years(8000, -0.05, 6)) is None    # older is dearer: a mix, not a curve
    assert _compute_annual_depreciation(_years(60000, 0.35, 5)) is None


def test_no_figure_from_a_loose_fit():
    noisy = [(2015, 9000, 20), (2016, 15000, 20), (2017, 8000, 20), (2018, 17000, 20),
             (2019, 9500, 20), (2020, 18000, 20)]
    assert _compute_annual_depreciation(noisy) is None


def test_unweighted_points_are_still_accepted():
    # market_price_stats_history rows used to come without their counts.
    result = _compute_annual_depreciation([(y, p) for y, p, _ in _years(25000, 0.12, 5)])
    assert result["pct_year"] == pytest.approx(0.12, abs=0.002)
