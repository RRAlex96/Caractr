"""
Safety Gate parsing — offline, using the real 2026 public-API payload shape
(alert SR/02935/26: VW steering-rack bolt, trimmed).
"""
from app.scrapers.safety_gate import (
    _is_candidate, _is_vehicle_detail, _normalise_brand, _risk_description,
    _risk_types, _severity_from_notification, _split_models, _years_from_detail,
    _measures,
)

DETAIL = {
    "id": 10119264,
    "notificationType": {"code": "A12", "name": "ARTICLE_12"},
    "reference": "SR/02935/26",
    "publicationDate": "2026-10-23T09:42:37.293Z",
    "product": {
        "productCategory": {"key": "product.category.motor.vehicles", "name": "MOTOR_VEHICLES"},
        "nameSpecific": "Caddy, Golf Sportsvan, Golf Variant 7, Tiguan, Tiguan Allspace, Touran\t\t",
        "brands": [{"brand": "Volkswagen (VW)"}],
        "batchNumbers": [{"batchNumber": "04.09.2013 - 01.07.2024"}],
    },
    "risk": {
        "riskType": [{"key": "riskType.injuries", "name": "INJURIES"}],
        "versions": [
            {"language": {"key": "BG"}, "riskDescription": "Влага…"},
            {"language": {"key": "EN"}, "riskDescription": "Moisture ingress could lead to corrosion of a steering rack bolt."},
        ],
    },
    "measureTaken": {"measures": [{"measureCategory": {"name": "PRODUCT_RECALL_FROM_CONSUMERS"}}]},
}


def test_brand_normalisation_handles_registry_spellings():
    assert _normalise_brand("Volkswagen (VW)") == "Volkswagen"
    assert _normalise_brand("VW - Volkswagen AG") == "Volkswagen"
    assert _normalise_brand("Alfa Romeo S.p.A.") == "Alfa Romeo"
    assert _normalise_brand("Unknown Toys Ltd") is None


def test_split_models_handles_lists_and_tabs():
    assert _split_models(DETAIL["product"]["nameSpecific"]) == [
        "Caddy", "Golf Sportsvan", "Golf Variant 7", "Tiguan", "Tiguan Allspace", "Touran"]


def test_years_expand_production_range():
    years = _years_from_detail(DETAIL)
    assert years[0] == 2013 and years[-1] == 2024 and len(years) == 12


def test_art12_notification_is_serious():
    assert _severity_from_notification(DETAIL) == "serious"
    assert _severity_from_notification({"notificationType": {"code": "A11"}, "reference": "A11/1/20"}) == "medium"
    assert _severity_from_notification({"reference": "A12/03161/24"}) == "serious"


def test_risk_description_prefers_english():
    assert _risk_description(DETAIL).startswith("Moisture ingress")
    assert _risk_types(DETAIL) == ["INJURIES"]
    assert "recall" in _measures(DETAIL)


def test_vehicle_detail_and_list_candidate_filters():
    assert _is_vehicle_detail(DETAIL)
    assert not _is_vehicle_detail({"product": {"productCategory": {"key": "product.category.toys"}}})
    car = {"product": {"name": "Passenger car / Passenger van", "brands": [{"brand": "Volkswagen"}]}}
    toy = {"product": {"name": "Soft toy", "brands": [{"brand": "Volkswagen"}]}}
    unknown_brand = {"product": {"name": "Passenger car", "brands": [{"brand": "NoName"}]}}
    assert _is_candidate(car) == "Volkswagen"
    assert _is_candidate(toy) is None
    assert _is_candidate(unknown_brand) is None


def test_years_attributed_per_model_from_labelled_batches():
    from app.scrapers.safety_gate import _years_for_model
    d = {"product": {"nameSpecific": "Astra H / Mokka A", "batchNumbers": [
        {"batchNumber": "Astra H : 03.01.2005 - 14.03.2014 // VIN : W0L0AHL4858055910 - W0L0AHL48E2065632"},
        {"batchNumber": "Mokka A : 22.05.2012 - 23.05.2018 // VIN : W0LJB7EE9DB000566 - W0VJD7EC0J4329477"},
    ]}}
    assert _years_for_model(d, "Astra H") == list(range(2005, 2015))
    assert _years_for_model(d, "Mokka A") == list(range(2012, 2019))


def test_unlabelled_batch_is_shared_by_all_models():
    from app.scrapers.safety_gate import _years_for_model
    assert _years_for_model(DETAIL, "Touran") == list(range(2013, 2025))
