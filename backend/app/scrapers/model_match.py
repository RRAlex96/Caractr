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


def name_match(db_model: str, raw_model: str) -> bool:
    db, raw = norm_model(db_model), norm_model(raw_model)
    if not db or not raw:
        return False
    return re.search(r"(?<![\w.\-])" + re.escape(db) + r"(?![\w\-])", raw) is not None


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


def best_generation(rows, model_raw: str, years: list[int]) -> int | None:
    """rows: mappings with id, model_name, year_start, year_end (one brand).

    Ranking among name matches with any overlap: most production years inside
    the generation, then the generation where production started, then the
    most specific model name."""
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
        key = (n is not None, n or 0, starts_here, len(norm_model(r["model_name"])))
        if best_key is None or key > best_key:
            best_id, best_key = r["id"], key
    return best_id
