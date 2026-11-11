"""
Shared high-precision matcher: official recall text → a generation in our DB.

Precision over recall, deliberately. A recall pinned to the wrong car shows a
red deal-breaker banner on a car that never had the problem; a missed match
just means one fewer warning. So:

1. Whole-word matches only — no fuzzy similarity. Fuzzy matching put an S-Klasse
   recall on the A-Class, ID.4 on ID.3, C-MAX on S-Max, EV5 on EV3.
2. Strict boundaries: "ID.Polo" is not a "Polo", "500X" is not a "500".
3. Mercedes class naming is normalised ("A-Klasse" = "A-Class" = "Classe A"),
   without ever letting "S-Klasse" match "Classe A".
4. When the recall states production years and they don't overlap a
   generation (± 1 year), that generation is rejected — never just de-ranked.
   An Astra H (2004-10) airbag recall must not land on an Astra K (2015-21).
5. Among valid candidates: explicit year overlap first, then the most specific
   model name ("Range Rover Sport" beats "Range Rover").
"""

import re
from datetime import date

_CLASS_PREFIX = re.compile(r"\bclasse\s+([a-z]{1,3})\b")
_CLASS_SUFFIX = re.compile(r"\b([a-z]{1,3})[\s-]+(?:klasse|class|classe)\b")


def norm_model(s: str) -> str:
    s = (s or "").lower().replace("\t", " ")
    s = _CLASS_PREFIX.sub(r"\1", s)
    s = _CLASS_SUFFIX.sub(r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


_BMW_SERIES = re.compile(r"^s[ée]rie (\d)(?: (.+))?$")


_CONVERTIBLE = re.compile(r"\b(cabrio|cabriolet|convertible|roadster|spider|spyder|volante)\b")


def name_match(db_model: str, raw_model: str) -> bool:
    db, raw = norm_model(db_model), norm_model(raw_model)
    if not db or not raw:
        return False
    # Convertibles run on their own life cycle (an "A4 Cabrio" recall is the
    # older B7 cabrio, not the B8 saloon; a Golf Cabrio Mk6 sold alongside the
    # Mk7), so a convertible never matches a model that isn't one.
    if _CONVERTIBLE.search(raw) and not _CONVERTIBLE.search(db):
        return False
    if re.search(r"(?<![\w.\-])" + re.escape(db) + r"(?![\w\-])", raw):
        return True
    # BMW "Série 3" is sold as 318/320d/330e and listed as "3 Series":
    # accept a 3-digit code starting with the series number (any extra words
    # in the DB name, e.g. "Gran Coupé", must also be present).
    m = _BMW_SERIES.match(db)
    if m:
        num, rest = m.group(1), (m.group(2) or "")
        code = re.search(r"(?<![\w.\-])m?" + num + r"\d{2}[a-z]{0,2}(?![\w\-])", raw)
        series = re.search(r"(?<![\w.\-])" + num + r" series(?![\w\-])", raw)
        rest_ok = all(w in raw for w in norm_model(rest).replace("é", "e").split()) if rest else True
        return bool((code or series) and rest_ok)
    return False


def _brand_aliases(brand: str) -> list[str]:
    from app.scrapers.safety_gate import BRAND_NORM
    b = (brand or "").lower()
    return sorted({b, b.replace("-", " ")} | {k for k, v in BRAND_NORM.items() if v.lower() == b})


def brand_in_text(brand: str, text: str) -> bool:
    t = (text or "").lower().replace("-", " ")
    return any(re.search(r"(?<![\w])" + re.escape(a.replace("-", " ")) + r"(?![\w])", t)
               for a in _brand_aliases(brand))


def listing_text(listing: dict) -> str:
    """Title + the human slug of the listing URL ('…/anuncio/vw-golf-ver-1-5-tsi-ID8Q0ImG.html')."""
    url = listing.get("source_url") or ""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"-ID\w+(\.html)?$", "", slug).replace("-", " ")
    return f"{listing.get('title') or ''} {slug}"


def listing_matches_generation(listing: dict, brand: str, model: str,
                               year_start: int | None, year_end: int | None,
                               sibling_models: list[str] = ()) -> bool:
    """Is a scraped marketplace listing really this generation of this model?
    Search results include promoted ads for other cars (a Ferrari under
    "Golf") and other generations (a 1988 Corolla under 2018+)."""
    year = listing.get("year")
    if not year or (year_start and year < year_start) or (year_end and year > year_end):
        return False
    price = listing.get("price") or 0
    if price <= 1000:          # "1 000 €" is a common placeholder, not a price
        return False
    text = listing_text(listing)
    if not brand_in_text(brand, text) or not name_match(model, text):
        return False
    # A more specific model we also carry ("Corolla Cross" vs "Corolla") wins.
    for sib in sibling_models:
        if sib != model and len(norm_model(sib)) > len(norm_model(model)) \
                and name_match(model, sib) and name_match(sib, text):
            return False
    return True


def overlap_years(gen_start: int | None, gen_end: int | None, years: list[int]) -> int | None:
    """How many of the recall's production years fall inside the generation.
    None when either side is unknown. Strict — no tolerance: production dates
    are exact, and an Astra H built until 2014 is not a 2015 Astra K."""
    if not years or not gen_start:
        return None
    end = gen_end or date.today().year
    return sum(1 for y in set(years) if gen_start <= y <= end)


def years_overlap(gen_start: int | None, gen_end: int | None, years: list[int]) -> bool | None:
    n = overlap_years(gen_start, gen_end, years)
    return None if n is None else n > 0


_ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6",
          "vii": "7", "viii": "8", "ix": "9", "x": "10"}


def designators(text_: str, model_name: str) -> set[str]:
    """Generation designators left after removing the model's own words:
    'Astra L' → {'l'}, 'Octavia III' → {'3'}, 'Golf Mk7' / 'Golf VII' → {'7'},
    '3 Series (F30)' → {'f30'}. Roman numerals and MkN normalise to digits."""
    model_tokens = set(re.findall(r"[a-z0-9]+", norm_model(model_name)))
    out = set()
    for t in re.findall(r"[a-z0-9]+", norm_model(text_)):
        if t in model_tokens:
            continue
        t = _ROMAN.get(t, t)
        m = re.fullmatch(r"mk(\d+)", t)
        out.add(m.group(1) if m else t)
    return out


def best_generation(rows, model_raw: str, years: list[int]) -> int | None:
    """rows: mappings with id, model_name, year_start, year_end and optionally
    gen_name (one brand).

    Ranking among name matches with any year overlap: an explicit generation
    designator shared with the generation's name ("Astra L" ↔ "Astra L"),
    then most production years inside the generation, then the generation
    where production started, then the most specific model name."""
    first_year = min(years) if years else None
    best_id, best_key = None, None
    for r in rows:
        if not name_match(r["model_name"], model_raw):
            continue
        n = overlap_years(r["year_start"], r["year_end"], years)
        if n == 0:
            continue
        starts_here = bool(first_year and r["year_start"]
                           and r["year_start"] <= first_year <= (r["year_end"] or date.today().year))
        gen_name = r.get("gen_name") if hasattr(r, "get") else None
        desig = bool(gen_name) and bool(
            designators(model_raw, r["model_name"]) & designators(gen_name, r["model_name"]))
        key = (desig, n is not None, n or 0, starts_here, len(norm_model(r["model_name"])))
        if best_key is None or key > best_key:
            best_id, best_key = r["id"], key
    return best_id
