"""
Caractr — our brand and model names -> Standvirtual's make and model ids

The site drops a make or model id it does not know from the search and
answers with every car of the make ("/volvo/xc40": all 1 303 Volvos) or of the
site ("/citroën/c3": 46 090 cars); a few unknown ids come back empty instead.
Building the id from our name by rule ("lower case, spaces to hyphens") got 25
of the catalogue's 201 models wrong: "XC40" is `xc-40`, "ID.3" is `id-3`,
"up!" is `up`, "CX-30" is `cx30`, "Range Rover Evoque" is `evoque`, the
Hyundai Kona is sold as "Kauai".

So names are matched against the site's own list (sv_models_data.py): same
name once case, accents, spaces and punctuation are set aside. What the list
cannot tell — a model the site calls something else — is in _MODEL_ALIASES.
scripts/audit_sv_slugs.py checks every catalogue model against the live site.

Two more things the list cannot tell:

  - one car filed under two ids, which are searched together ("a--b" in the
    path, the site's own form for several models): the DS 7 is `ds7` and
    `ds7-crossback`, the MINI hatch `mini-3p` and `mini-5p` (_MODEL_GROUPS);
  - a model whose trims are priced as different cars: every MINI hatch is a
    "Cooper" in our catalogue, be it a One or a John Cooper Works. Its
    comparables must share the trim (needs_trim / trim_label).
"""
import re
from typing import Optional

from app.scrapers.sv_models_data import SV_MAKES, SV_MODELS
from app.scrapers.sv_series import _norm

# Our brand names the site's make names do not cover.
_MAKE_ALIASES = {
    "volkswagen": "vw",
    "mercedes": "mercedes-benz",
}

# (make id, our model name) -> model id, where the site's name differs.
_MODEL_ALIASES = {
    ("hyundai", "kona"): "kauai",                 # sold in Portugal as the Kauai
    ("mg", "zs ev"): "zs",                        # the EV is the ZS with the electric fuel filter
    ("opel", "combo life"): "combo",
    ("skoda", "superb combi"): "superb-break",
    ("skoda", "octavia combi"): "octavia-break",
    ("skoda", "fabia combi"): "fabia-break",
    # The MINI hatch: our catalogue calls it "Cooper"; listings name the trim.
    **{("mini", name): "mini-3p" for name in (
        "cooper", "cooper s", "cooper d", "cooper sd", "cooper se", "cooper e", "cooper c",
        "one", "one d", "one first", "john cooper works", "jcw", "hatch", "hatchback")},
}

# One car the site files under several model ids. Any of them is searched as
# all of them. Live, 2026-11-13: the two DS 7 ids hold the same model years
# (2018–2024) and a merged pool prices a listing as well as its own id's does
# (off by more than 20%: 6% against 8% diesel, 2% against 3% plug-in), with
# more verdicts; the DS 4 became the "Nº4" in 2025; a MINI 3-door and 5-door of
# one trim price alike (14% against 15%).
_MODEL_GROUPS = {
    "ds": [("ds7", "ds7-crossback"), ("ds4", "number-4")],
    "mini": [("mini-3p", "mini-5p")],
}

# Searches (make id, model id as searched) whose comparables must share the
# car's trim. MINI hatch, leave-one-out over 256 live listings: against all
# trims the reference is off by more than 20% for 49% of petrol cars (a One is
# 29% under it, a John Cooper Works 27% over) and 22% of diesels; against the
# same trim, 14% and 6%.
_TRIMMED = {("mini", "mini-3p--mini-5p")}


def _key(text: Optional[str]) -> str:
    return _norm(text).replace(" ", "")


_MAKE_BY_KEY = {}
for _id, _name in SV_MAKES.items():
    _MAKE_BY_KEY.setdefault(_key(_name), _id)
    _MAKE_BY_KEY.setdefault(_key(_id), _id)

_MODEL_BY_KEY = {}
for _make, _models in SV_MODELS.items():
    by_key = _MODEL_BY_KEY.setdefault(_make, {})
    for _id, _name in _models.items():           # names first: they are what we store
        by_key.setdefault(_key(_name), _id)
    for _id in _models:
        by_key.setdefault(_key(_id), _id)


def find_make(brand: Optional[str]) -> Optional[str]:
    """The site's make id for one of our brand names ("Citroën" -> "citroen",
    "Volkswagen" -> "vw"), or None when the site has no such make."""
    key = _key(brand)
    if not key:
        return None
    return _MAKE_ALIASES.get(_norm(brand)) or _MAKE_BY_KEY.get(key)


def find_model(make: Optional[str], model_name: Optional[str]) -> Optional[str]:
    """
    The site's model id for one of our model names of `make` (the site's make
    id), or None when the site lists no model by that name:

      "XC40" -> "xc-40", "ID.3" -> "id-3", "Mégane" -> "megane", "#1" -> "smart-1",
      "Range Rover Evoque" -> "evoque", and with the make in front where the
      site writes it that way: MG "4" -> "mg4". A car filed under several ids
      comes back as all of them: DS "7" -> "ds7--ds7-crossback".

    For BMW, Mercedes-Benz and Lexus the ids found here are series, which the
    search path does not take — ask sv_series first.
    """
    name = _norm(model_name)
    if not make or not name:
        return None
    alias = _MODEL_ALIASES.get((make, name))
    if alias:
        return expand_model(make, alias)
    by_key = _MODEL_BY_KEY.get(make, {})
    key = name.replace(" ", "")
    return expand_model(make, by_key.get(key) or by_key.get(_key(SV_MAKES.get(make)) + key)
                        or by_key.get(_key(make) + key))


def expand_model(make: Optional[str], model_id: Optional[str]) -> Optional[str]:
    """The path slug to search a model id under: the id itself, or, for a car
    the site files under several ids, all of them ("ds7" -> "ds7--ds7-crossback")."""
    for group in _MODEL_GROUPS.get(make or "", []):
        if model_id in group:
            return "--".join(group)
    return model_id


def needs_trim(make: Optional[str], searched_slug: Optional[str]) -> bool:
    """True when the comparables of this search must share the car's trim."""
    return (make, searched_slug) in _TRIMMED


def trim_label(*texts: Optional[str]) -> Optional[str]:
    """
    The MINI trim a listing names, from the first text that names one: "one",
    "cooper", "cooper s", "cooper se", "cooper e" or "jcw". The diesels fall
    in with their petrol namesakes (One D, Cooper D, Cooper SD); the fuel
    filter keeps them apart. None when no text names a trim.
    """
    for text in texts:
        t = _norm(text)
        if not t:
            continue
        if "john cooper works" in t or re.search(r"\bjcw\b", t):
            return "jcw"
        m = re.search(r"\bcooper(?: (se|sd|s|e|d|c))?\b", t)
        if m:
            return {"se": "cooper se", "s": "cooper s", "sd": "cooper s", "e": "cooper e"}.get(m.group(1), "cooper")
        if re.search(r"\bone\b", t):
            return "one"
    return None


# ── a site model name that belongs to a differently named catalogue model ────

# Site ids that are one catalogue model or another depending on the fuel: the
# name alone does not say which (MG "ZS" is the petrol ZS or the ZS EV).
_FUEL_DEPENDENT = {("mg", "zs")}
_SITE_ID_BY_NAME: dict = {}


def catalogue_target(brand: Optional[str], model_name: Optional[str]) -> Optional[tuple]:
    """
    (catalogue brand, catalogue model) for a listing whose model is written the
    way the site names it, when that site model is mapped to a catalogue model
    of another name (sv_catalogue_map): "Insignia Sports Tourer" -> Opel
    Insignia, BMW "216 Gran Tourer" -> Série 2 Active Tourer, Citroën "DS3" ->
    DS 3. None for any other name.
    """
    from app.scrapers.sv_catalogue_map import SITE_MODEL_MAP
    from app.scrapers.sv_series_data import SV_SERIES

    make = find_make(brand)
    key = _key(model_name)
    if not make or not key:
        return None
    if make not in _SITE_ID_BY_NAME:
        index: dict = {}
        for site_id, name in SV_MODELS.get(make, {}).items():
            index.setdefault(_key(name), site_id)
        for _series_id, (_series_name, subs) in SV_SERIES.get(make, {}).items():
            for sub_id, sub_name in subs.items():
                index.setdefault(_key(sub_name), sub_id)
        _SITE_ID_BY_NAME[make] = index
    site_id = _SITE_ID_BY_NAME[make].get(key)
    if not site_id or (make, site_id) in _FUEL_DEPENDENT:
        return None
    return SITE_MODEL_MAP.get((make, site_id))
