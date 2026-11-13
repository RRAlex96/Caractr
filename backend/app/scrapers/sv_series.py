"""
Caractr — Standvirtual series and sub-models

For BMW, Mercedes-Benz, Lexus and the Porsche 911 the site has two levels: a
series ("Série 5", "Classe A", "NX") and its sub-models ("530", "A 180",
"NX 350h"). Only the sub-model works as the model in the search path:

    /carros/bmw/530                                   the 530s
    /carros/bmw?search[filter_enum_model]=serie-5     every Série 5
    /carros/bmw/serie-5                               not recognised: every BMW

Our catalogue names these cars by the series ("Serie 5", "Classe A"), so a car
that does not come with the site's own slug (any listing that is not from
Standvirtual) has to be mapped: to its sub-model when its title names one, to
the series otherwise.
"""
import re
import unicodedata
from typing import Optional

from app.scrapers.sv_series_data import SV_SERIES

# Words of a sub-model name that a listing often leaves out ("A 45" for
# "A 45 AMG", "NX 450h" for "NX 450h+"): never required, but they count when
# choosing between two sub-models.
_OPTIONAL_WORDS = {"amg", "plus", "todos"}
# A bare class letter is a series only when a body style follows ("E Coupé").
_BODY_WORDS = {"coupe", "cabrio", "cabriolet", "limousine", "station", "break", "sw", "sedan", "all"}
# A number followed by one of these is a quantity, not a sub-model ("320 cv").
_UNITS = r"(?:cv|hp|kw|km|kms|nm|mil|cc|cm3|eur|euros?)\b"


def _norm(text: Optional[str]) -> str:
    """Lower case, no accents, '+' spelled out, everything else that is not a
    letter or a digit turned into a space."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("+", " plus ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _series_aliases(make: str, series_name: str) -> list[str]:
    name = _norm(series_name)
    aliases = [name]
    if make == "bmw" and name.startswith("serie "):
        aliases.append(f"{name[6:]} series")                 # "3 series"
    if make == "mercedes-benz" and name.startswith("classe "):
        letters = name[7:]
        aliases += [f"{letters} class", f"{letters} klasse"]
        aliases.append(letters)                               # "CLA", "GLC"; a bare letter: see find_series
    if name.endswith(" todos"):                               # "911 (Todos)"
        aliases.append(name[:-6])
    return aliases


def find_series(make: Optional[str], model_name: Optional[str]) -> Optional[str]:
    """The site's series id when `model_name` is a series of `make` (the site's
    make id), alone or followed by a body style: "Série 5" -> "serie-5",
    "CLA" -> "classe-cla", "Série 2 Gran Coupé" -> "serie-2". None otherwise."""
    model = _norm(model_name)
    if not model:
        return None
    best = None
    for series_id, (series_name, _) in SV_SERIES.get(make or "", {}).items():
        for alias in _series_aliases(make, series_name):
            if model == alias:
                matched = len(alias) >= 2                     # never a bare "A"
            elif model.startswith(alias + " "):
                matched = len(alias) >= 2 or model.split()[1] in _BODY_WORDS
            else:
                matched = False
            if matched and (best is None or len(alias) > best[0]):
                best = (len(alias), series_id)
    return best[1] if best else None


def _split_name(variant_name: str) -> tuple:
    """(base tokens, qualifier tokens) of a sub-model name: the base runs up to
    the first token holding a digit ("A 180", "M340", "IS 300h"), the rest
    qualifies it ("Limousine", "Gran Coupé", "AMG")."""
    tokens = _norm(variant_name).split()
    for i, token in enumerate(tokens):
        if any(c.isdigit() for c in token):
            return tokens[:i + 1], tokens[i + 1:]
    return tokens, []


def _base_pattern(base: list[str]) -> re.Pattern:
    """The base as it may be written in a title: "A 180", "A180", "a-180",
    "320" in "320d". Not inside another word or number, and not a quantity."""
    parts = []
    for token in base:
        pieces = re.findall(r"[a-z]+|\d+", token)
        parts.append(r"[\s-]?".join(re.escape(p) for p in pieces))
    body = r"[\s-]?".join(parts)
    return re.compile(rf"(?<![a-z0-9]){body}(?![0-9])(?![.,]\d)(?!\s?\d{{3}}\b)(?!\s?{_UNITS})")


def find_variant(make: Optional[str], model_name: Optional[str], *texts: Optional[str]) -> Optional[str]:
    """
    The site's sub-model id for a car of `make` (the site's make id), or None:

      - `model_name` is itself a sub-model ("530", "A 180", "X3", "NX 350h")
      - `model_name` is a series and one of `texts` (the listing's title, the
        model as the source wrote it, its URL) names one of that series'
        sub-models: "BMW 320d Touring" -> "320", "Mercedes A 180 d Limousine"
        -> "a-180-limousine".

    Only sub-models of the car's own series are looked for, and where a text
    names several the first one wins.
    """
    series_of_make = SV_SERIES.get(make or "", {})
    model = _norm(model_name)
    if not series_of_make or not model:
        return None

    compact = model.replace(" ", "")
    for _, variants in series_of_make.values():
        for variant_id, variant_name in variants.items():
            if _norm(variant_name).replace(" ", "") == compact:
                return variant_id

    series_id = find_series(make, model_name)
    if not series_id:
        return None
    text = " | ".join(_norm(t) for t in texts if t)
    if not text:
        return None
    # Body-style words of the catalogue name count too ("Série 2 Gran Coupé").
    words = set(text.replace("|", " ").split()) | set(model.split())
    if "gt" in words:
        words |= {"gran", "turismo"}

    best = None
    for variant_id, variant_name in series_of_make[series_id][1].items():
        base, qualifier = _split_name(variant_name)
        m = _base_pattern(base).search(text)
        if not m or any(w not in words for w in qualifier if w not in _OPTIONAL_WORDS):
            continue
        present = sum(1 for w in qualifier if w in words)
        key = (m.start(), -len(" ".join(base)), -present, len(qualifier))
        if best is None or key < best[0]:
            best = (key, variant_id)
    return best[1] if best else None
