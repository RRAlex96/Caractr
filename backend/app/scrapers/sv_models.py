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

Known gaps: MINI "Cooper" (the site files MINIs as "3 Portas" / "5 Portas")
and the DS 7, which the site splits into `ds7` and `ds7-crossback`.
"""
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
}


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
      site writes it that way: DS "4" -> "ds4", MG "4" -> "mg4".

    For BMW, Mercedes-Benz and Lexus the ids found here are series, which the
    search path does not take — ask sv_series first.
    """
    name = _norm(model_name)
    if not make or not name:
        return None
    alias = _MODEL_ALIASES.get((make, name))
    if alias:
        return alias
    by_key = _MODEL_BY_KEY.get(make, {})
    key = name.replace(" ", "")
    return by_key.get(key) or by_key.get(_key(SV_MAKES.get(make)) + key) or by_key.get(_key(make) + key)
