"""
Caractr — audit of the reference data, with a score

What the site tells a buyer is only as good as these tables: which generation a
car belongs to, what its engines are, what the model costs on the market, how
reliable it is. This module asks the database the questions that have gone
wrong before (or would hurt if they did) and turns the answers into a score.

    python -m scripts.data_audit            # scorecard
    python -m scripts.data_audit --json     # for a machine
    python -m scripts.data_audit --strict   # exit 1 when a critical check fails

Two kinds of check:

  - a RULE finds rows that break it (an engine of 4 cv, two generations of one
    model claiming the same year). Its score is 1 with no offenders and falls
    with the share of rows that offend, faster the more serious the rule.
  - a MEASURE is a share to push up (models with a measured price), scored
    against a target.

Checks are grouped in six dimensions; the overall score is their weighted
mean. Everything here only reads.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy import text

# How fast a rule's score falls with the share of offending rows.
_PENALTY = {"critical": 25.0, "major": 6.0, "minor": 2.0}
_WEIGHT = {"critical": 3.0, "major": 2.0, "minor": 1.0}

DIMENSIONS = {
    "integrity":    ("Structure: no orphans, duplicates, overlaps", 0.20),
    "plausibility": ("Values are physically and commercially possible", 0.20),
    "coverage":     ("The Portuguese market is covered", 0.20),
    "freshness":    ("Prices are recent", 0.10),
    "provenance":   ("Every figure says where it comes from", 0.20),
    "safeties":     ("The database itself refuses bad rows", 0.10),
}

# A real model has a body type; a row auto-created from an unmatched listing
# does not (see _find_or_create_model). Stubs are kept out of every measure.
_REAL = "COALESCE(vm.body_type, '') <> ''"


@dataclass
class Check:
    id: str
    dim: str
    title: str
    severity: str = "major"
    # RULE: `sql` returns the offending rows (first column(s) shown as examples);
    # `total` returns how many rows the rule applies to.
    sql: Optional[str] = None
    total: Optional[str] = None
    # MEASURE: `measure` returns (numerator, denominator); scored against `target`.
    measure: Optional[str] = None
    target: float = 1.0
    why: str = ""


@dataclass
class Result:
    check: Check
    score: float
    found: int = 0
    of: int = 0
    examples: list = field(default_factory=list)
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.score >= 0.999


CHECKS = [
    # ── integrity ────────────────────────────────────────────────────────────
    Check("INT-01", "integrity", "Engines, generations and scores all belong to a model", "critical",
          sql="""SELECT 'engine ' || id FROM engines WHERE model_id IS NULL
                 UNION ALL SELECT 'generation ' || id FROM generations WHERE model_id IS NULL
                 UNION ALL SELECT 'character ' || id FROM driving_character WHERE model_id IS NULL
                 UNION ALL SELECT 'price ' || id FROM market_price_stats WHERE model_id IS NULL
                 UNION ALL SELECT 'model ' || id FROM vehicle_models WHERE brand_id IS NULL""",
          total="SELECT (SELECT COUNT(*) FROM engines) + (SELECT COUNT(*) FROM generations)"),
    Check("INT-02", "integrity", "No model is in the catalogue twice", "critical",
          sql="""SELECT b.name || ' ' || MIN(vm.name) || ' x' || COUNT(*)
                 FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
                 GROUP BY b.name, LOWER(TRANSLATE(vm.name, 'áàâãéêíóôõúçÁÉÍÓÚÇ -', 'aaaaeeiooouc AEIOUC'))
                 HAVING COUNT(*) > 1""",
          total="SELECT COUNT(*) FROM vehicle_models"),
    Check("INT-03", "integrity", "No generation or engine is listed twice for a model", "major",
          sql="""SELECT 'generation ' || b.name || ' ' || vm.name || ' ' || g.name
                 FROM generations g JOIN vehicle_models vm ON vm.id = g.model_id JOIN brands b ON b.id = vm.brand_id
                 GROUP BY b.name, vm.name, g.model_id, g.name HAVING COUNT(*) > 1
                 UNION ALL
                 SELECT 'engine ' || b.name || ' ' || vm.name || ' ' || e.code
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 GROUP BY b.name, vm.name, e.model_id, e.code HAVING COUNT(*) > 1""",
          total="SELECT (SELECT COUNT(*) FROM engines) + (SELECT COUNT(*) FROM generations)"),
    Check("INT-04", "integrity", "Two generations of a model never claim the same year", "critical",
          why="A car of that year would be compared with either generation's prices and faults.",
          sql="""SELECT b.name || ' ' || vm.name || ': ' || a.name || ' ' || a.year_start || '-' || COALESCE(a.year_end::text, '')
                        || ' / ' || c.name || ' ' || c.year_start || '-' || COALESCE(c.year_end::text, '')
                 FROM generations a
                 JOIN generations c ON c.model_id = a.model_id AND c.id > a.id
                      AND COALESCE(a.fuel_type, '') = COALESCE(c.fuel_type, '')
                      AND a.year_start <= COALESCE(c.year_end, 9999) AND c.year_start <= COALESCE(a.year_end, 9999)
                 JOIN vehicle_models vm ON vm.id = a.model_id JOIN brands b ON b.id = vm.brand_id""",
          total="SELECT COUNT(*) FROM generations"),
    Check("INT-05", "integrity", "No single year falls between two generations of a model", "major",
          why="A car registered in that year has no generation. A longer gap is a model that was off the market "
              "(the Defender from 2017 to 2019) and is left alone.",
          sql="""SELECT b.name || ' ' || vm.name || ': ' || g.name || ' ends ' || g.year_end || ', next starts ' || nxt.year_start
                 FROM generations g
                 JOIN vehicle_models vm ON vm.id = g.model_id JOIN brands b ON b.id = vm.brand_id
                 JOIN LATERAL (SELECT MIN(n.year_start) AS year_start FROM generations n
                               WHERE n.model_id = g.model_id AND n.fuel_type IS NULL AND n.year_start > g.year_start) nxt ON TRUE
                 WHERE g.fuel_type IS NULL AND g.year_end IS NOT NULL
                   AND nxt.year_start = g.year_end + 2""",
          total="SELECT COUNT(*) FROM generations"),
    Check("INT-06", "integrity", "Generation years are in order and in range", "critical",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || g.name || ' ' || COALESCE(g.year_start::text, '?') || '-' || COALESCE(g.year_end::text, '')
                 FROM generations g JOIN vehicle_models vm ON vm.id = g.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE g.year_start IS NULL OR g.year_start < 1970 OR g.year_start > EXTRACT(YEAR FROM NOW()) + 1
                    OR g.year_end < g.year_start OR g.year_end > EXTRACT(YEAR FROM NOW()) + 1""",
          total="SELECT COUNT(*) FROM generations"),
    Check("INT-07", "integrity", "A model has one generation on sale at most", "major",
          sql=f"""SELECT b.name || ' ' || vm.name || ' x' || COUNT(*)
                  FROM generations g JOIN vehicle_models vm ON vm.id = g.model_id JOIN brands b ON b.id = vm.brand_id
                  WHERE g.year_end IS NULL AND g.fuel_type IS NULL AND {_REAL}
                  GROUP BY b.name, vm.name HAVING COUNT(*) > 1""",
          total="SELECT COUNT(*) FROM vehicle_models"),
    Check("INT-08", "integrity", "Every model has a generation", "major",
          sql=f"""SELECT b.name || ' ' || vm.name FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
                  WHERE {_REAL} AND NOT EXISTS (SELECT 1 FROM generations g WHERE g.model_id = vm.id)""",
          total=f"SELECT COUNT(*) FROM vehicle_models vm WHERE {_REAL}"),
    Check("INT-09", "integrity", "No leftover stub models from unmatched listings", "minor",
          why="A listing that matches nothing creates a model with no body type; it should be mapped or removed.",
          sql="""SELECT b.name || ' ' || vm.name FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
                 WHERE COALESCE(vm.body_type, '') = ''""",
          total="SELECT COUNT(*) FROM vehicle_models"),
    Check("INT-10", "integrity", "Each stored listing price sits in a generation of its model", "major",
          sql="""SELECT 'observation ' || po.id FROM price_observations po
                 JOIN generations g ON g.id = po.generation_id
                 WHERE g.model_id <> po.model_id
                    OR po.vehicle_year NOT BETWEEN g.year_start AND COALESCE(g.year_end, 9999)""",
          total="SELECT COUNT(*) FROM price_observations WHERE generation_id IS NOT NULL"),

    # ── plausibility ─────────────────────────────────────────────────────────
    Check("PLA-01", "plausibility", "Engine fuel is one of the five known kinds", "critical",
          sql="""SELECT e.id || ' ' || COALESCE(e.fuel_type, 'null') FROM engines e
                 WHERE e.fuel_type IS NULL OR e.fuel_type NOT IN ('gasolina', 'diesel', 'hibrido', 'eletrico', 'gpl')""",
          total="SELECT COUNT(*) FROM engines"),
    Check("PLA-02", "plausibility", "Engine power is between 30 and 1 100 cv", "critical",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || COALESCE(e.power_hp::text, 'null') || ' cv'
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE e.power_hp IS NULL OR e.power_hp < 30 OR e.power_hp > 1100""",
          total="SELECT COUNT(*) FROM engines"),
    Check("PLA-03", "plausibility", "Engine size fits the fuel", "major",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || COALESCE(e.displacement_cc::text, 'null') || ' cc ' || e.fuel_type
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE (e.fuel_type = 'eletrico' AND COALESCE(e.displacement_cc, 0) > 0)
                    OR (e.fuel_type <> 'eletrico' AND (e.displacement_cc IS NULL OR e.displacement_cc < 600 OR e.displacement_cc > 8500))""",
          total="SELECT COUNT(*) FROM engines"),
    Check("PLA-04", "plausibility", "Consumption is possible for the kind of engine", "major",
          why="Litres for combustion (plug-in hybrids from 0.5), kWh for electric.",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || e.consumption_mixed || ' (' || e.fuel_type
                        || CASE WHEN e.plug_in THEN ' plug-in' ELSE '' END || ')'
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE e.consumption_mixed IS NOT NULL AND (
                       (e.fuel_type = 'eletrico' AND e.consumption_mixed NOT BETWEEN 10 AND 35)
                    OR (e.fuel_type <> 'eletrico' AND e.plug_in AND e.consumption_mixed NOT BETWEEN 0.4 AND 9)
                    OR (e.fuel_type <> 'eletrico' AND NOT e.plug_in AND e.consumption_mixed NOT BETWEEN 2.8 AND 25))""",
          total="SELECT COUNT(*) FROM engines WHERE consumption_mixed IS NOT NULL"),
    Check("PLA-05", "plausibility", "CO2 agrees with consumption", "major",
          why="Burning a litre of petrol gives about 23 g/km per L/100 km, diesel about 26; a row far off has one of the two wrong.",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || e.consumption_mixed || ' L, ' || e.co2_emissions || ' g'
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE e.fuel_type IN ('gasolina', 'diesel', 'hibrido') AND e.consumption_mixed > 0 AND e.co2_emissions > 0
                   AND e.co2_emissions / e.consumption_mixed NOT BETWEEN 19 AND 31""",
          total="""SELECT COUNT(*) FROM engines WHERE fuel_type IN ('gasolina', 'diesel', 'hibrido')
                   AND consumption_mixed > 0 AND co2_emissions > 0"""),
    Check("PLA-06", "plausibility", "An electric car emits no CO2; a combustion car emits some", "major",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || COALESCE(e.co2_emissions::text, 'null') || ' g ' || e.fuel_type
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE (e.fuel_type = 'eletrico' AND COALESCE(e.co2_emissions, 0) > 0)
                    OR (e.fuel_type <> 'eletrico' AND e.co2_emissions IS NOT NULL
                        AND (e.co2_emissions < 8 OR e.co2_emissions > 500))""",
          total="SELECT COUNT(*) FROM engines"),
    Check("PLA-07", "plausibility", "Reliability and maintenance estimates are on their scales", "critical",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || COALESCE(e.reliability_score::text, 'null')
                        || ' / ' || COALESCE(e.maintenance_cost_year::text, 'null') || ' EUR'
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE e.reliability_score IS NULL OR e.reliability_score NOT BETWEEN 1 AND 10
                    OR e.maintenance_cost_year IS NULL OR e.maintenance_cost_year NOT BETWEEN 100 AND 6000""",
          total="SELECT COUNT(*) FROM engines"),
    Check("PLA-08", "plausibility", "An engine's years are in order and inside its model's generations", "major",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || e.code || ': ' || e.year_from || '-' || e.year_to
                 FROM engines e JOIN vehicle_models vm ON vm.id = e.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE e.year_from IS NOT NULL AND (
                       e.year_to < e.year_from OR e.year_from < 1985 OR e.year_to > EXTRACT(YEAR FROM NOW()) + 1
                    OR NOT EXISTS (SELECT 1 FROM generations g WHERE g.model_id = e.model_id
                                   AND g.year_start <= e.year_to AND COALESCE(g.year_end, 9999) >= e.year_from))""",
          total="SELECT COUNT(*) FROM engines WHERE year_from IS NOT NULL"),
    Check("PLA-09", "plausibility", "Character scores are between 1 and 10", "critical",
          sql="""SELECT 'model ' || model_id FROM driving_character
                 WHERE LEAST(comfort_score, driving_fun_score, city_score, highway_score, family_score) < 1
                    OR GREATEST(comfort_score, driving_fun_score, city_score, highway_score, family_score) > 10
                    OR comfort_score IS NULL OR driving_fun_score IS NULL OR city_score IS NULL
                    OR highway_score IS NULL OR family_score IS NULL""",
          total="SELECT COUNT(*) FROM driving_character"),
    Check("PLA-10", "plausibility", "A market price has low <= typical <= high and enough listings behind it", "critical",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || m.year || ': ' || m.min_price || '/' || m.avg_price || '/' || m.max_price
                        || ' n=' || COALESCE(m.sample_count::text, 'null')
                 FROM market_price_stats m JOIN vehicle_models vm ON vm.id = m.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE m.avg_price IS NULL OR m.avg_price NOT BETWEEN 500 AND 500000
                    OR m.min_price > m.avg_price OR m.max_price < m.avg_price
                    OR (m.source = 'aggregated' AND COALESCE(m.sample_count, 0) < 6)""",
          total="SELECT COUNT(*) FROM market_price_stats"),
    Check("PLA-11", "plausibility", "Within a generation, a newer year is not cheaper and not far dearer", "major",
          why="A year 12% cheaper than the year before it, or 45% dearer, in the same generation is a thin or mixed "
              "sample (a year of sports versions next to a year of ex-rental cars).",
          sql="""SELECT b.name || ' ' || vm.name || ': ' || a.year || ' = ' || a.avg_price || ', ' || c.year || ' = ' || c.avg_price
                 FROM market_price_stats a
                 JOIN market_price_stats c ON c.model_id = a.model_id AND c.year = a.year + 1 AND c.source = a.source
                 JOIN vehicle_models vm ON vm.id = a.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE a.source = 'aggregated' AND a.year >= EXTRACT(YEAR FROM NOW()) - 15
                   AND (c.avg_price > a.avg_price * 1.45 OR c.avg_price < a.avg_price * 0.88)
                   AND EXISTS (SELECT 1 FROM generations g WHERE g.model_id = a.model_id AND g.fuel_type IS NULL
                               AND a.year >= g.year_start AND c.year <= COALESCE(g.year_end, 9999))""",
          total="""SELECT COUNT(*) FROM market_price_stats WHERE source = 'aggregated'
                   AND year >= EXTRACT(YEAR FROM NOW()) - 15"""),
    Check("PLA-12", "plausibility", "Depreciation rates are between 3% and 25% a year", "major",
          sql="""SELECT b.name || ' ' || vm.name || ' ' || g.name || ': ' || g.depreciation_pct_year
                 FROM generations g JOIN vehicle_models vm ON vm.id = g.model_id JOIN brands b ON b.id = vm.brand_id
                 WHERE g.depreciation_pct_year IS NOT NULL AND g.depreciation_pct_year NOT BETWEEN 0.03 AND 0.25""",
          total="SELECT COUNT(*) FROM generations WHERE depreciation_pct_year IS NOT NULL"),
    Check("PLA-13", "plausibility", "Stored listing prices are plausible for a car", "major",
          sql="""SELECT 'observation ' || id || ': ' || price || ' EUR, ' || COALESCE(vehicle_year::text, '?') || ', ' || COALESCE(km::text, '?') || ' km'
                 FROM price_observations
                 WHERE price < 1000 OR price > 500000 OR vehicle_year < 1990
                    OR vehicle_year > EXTRACT(YEAR FROM NOW()) + 1 OR km < 0 OR km > 600000""",
          total="SELECT COUNT(*) FROM price_observations"),

    # ── coverage ─────────────────────────────────────────────────────────────
    Check("COV-01", "coverage", "Listings on the market that match a catalogue model", "critical", target=0.95,
          why="From the last market snapshot: of every listing read, how many belong to a model we know.",
          measure="""SELECT COALESCE(SUM(listings_matched), 0), COALESCE(SUM(listings_read), 0)
                     FROM (SELECT listings_matched, listings_read FROM market_snapshot_runs
                           ORDER BY collected_on DESC LIMIT 1) r"""),
    Check("COV-02", "coverage", "Models with a measured market price", "major", target=0.90,
          why="A model with too few listings for a price is not recommended; it is still recognised in an analysis.",
          measure=f"""SELECT COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM market_price_stats m
                                 WHERE m.model_id = vm.id AND m.source = 'aggregated')), COUNT(*)
                      FROM vehicle_models vm WHERE {_REAL}"""),
    Check("COV-03", "coverage", "Models with engines", "major", target=0.97,
          measure=f"""SELECT COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM engines e WHERE e.model_id = vm.id)), COUNT(*)
                      FROM vehicle_models vm WHERE {_REAL}"""),
    Check("COV-04", "coverage", "Models with at least two engines", "minor", target=0.85,
          measure=f"""SELECT COUNT(*) FILTER (WHERE (SELECT COUNT(*) FROM engines e WHERE e.model_id = vm.id) >= 2), COUNT(*)
                      FROM vehicle_models vm WHERE {_REAL}"""),
    Check("COV-05", "coverage", "Models with character scores", "major", target=1.0,
          measure=f"""SELECT COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM driving_character d WHERE d.model_id = vm.id)), COUNT(*)
                      FROM vehicle_models vm WHERE {_REAL}"""),
    Check("COV-06", "coverage", "Recent generations with a market value", "major", target=0.90,
          measure="""SELECT COUNT(*) FILTER (WHERE g.market_value_p50 IS NOT NULL), COUNT(*)
                     FROM generations g
                     WHERE COALESCE(g.year_end, 9999) >= EXTRACT(YEAR FROM NOW()) - 12"""),
    Check("COV-07", "coverage", "Listings whose year has a generation", "major", target=0.99,
          why="A listing of a catalogue model with no generation for its year cannot be compared like for like.",
          measure="""SELECT COUNT(*) FILTER (WHERE generation_id IS NOT NULL), COUNT(*)
                     FROM price_observations WHERE extraction_method = 'search_snapshot' AND model_id IS NOT NULL"""),
    Check("COV-08", "coverage", "Engines that say which years they were sold", "major", target=0.95,
          measure="SELECT COUNT(*) FILTER (WHERE year_from IS NOT NULL), COUNT(*) FROM engines"),

    # ── freshness ────────────────────────────────────────────────────────────
    Check("FRE-01", "freshness", "The market snapshot is under 35 days old", "critical",
          why="Listings older than 60 days are ignored and prices older than 75 days expire.",
          measure="""SELECT GREATEST(0, LEAST(1, (60 - EXTRACT(EPOCH FROM NOW() - MAX(observed_at)) / 86400.0) / 25.0)), 1
                     FROM price_observations WHERE extraction_method = 'search_snapshot'"""),
    Check("FRE-02", "freshness", "Market prices were computed after the last snapshot", "major",
          measure="""SELECT COUNT(*) FILTER (WHERE m.updated_at >= s.last - INTERVAL '1 day'), COUNT(*)
                     FROM market_price_stats m,
                          (SELECT MAX(observed_at) AS last FROM price_observations
                           WHERE extraction_method = 'search_snapshot') s
                     WHERE m.source = 'aggregated'"""),
    Check("FRE-03", "freshness", "No placeholder prices left", "critical",
          sql="SELECT 'price ' || id || ' ' || source FROM market_price_stats WHERE source NOT IN ('aggregated', 'live_scraped')",
          total="SELECT COUNT(*) FROM market_price_stats"),

    # ── provenance ───────────────────────────────────────────────────────────
    Check("PRO-01", "provenance", "Generations checked against a published source", "major", target=0.98,
          measure="SELECT COUNT(*) FILTER (WHERE source_url IS NOT NULL AND verified_on IS NOT NULL), COUNT(*) FROM generations"),
    Check("PRO-02", "provenance", "Engines that record where their figures come from", "major", target=0.98,
          why="A row written by the AI curator without sources does not count.",
          measure="""SELECT COUNT(*) FILTER (WHERE source IS NOT NULL AND source NOT LIKE 'IA (%sem fontes%'),
                            COUNT(*) FROM engines"""),
    Check("PRO-03", "provenance", "Brands whose reliability rests on at least two published studies", "major", target=0.90,
          why="Young and niche brands (BYD, Polestar, Alpine) appear in one study or none; their score says so.",
          measure="""SELECT COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM brand_reliability r
                                 WHERE r.brand_id = b.id AND r.studies >= 2)), COUNT(*)
                     FROM brands b WHERE EXISTS (SELECT 1 FROM vehicle_models vm WHERE vm.brand_id = b.id)"""),
    Check("PRO-04", "provenance", "Known-issue rows with a named source", "major", target=0.95,
          why="Rows the AI curator wrote without sources are not shown to buyers as facts, and do not count.",
          measure="""SELECT COUNT(*) FILTER (WHERE COALESCE(source, '') <> '' AND source NOT LIKE 'IA (%'),
                            COUNT(*) FROM engine_issues"""),
    Check("PRO-05", "provenance", "Market prices that record their sample", "major", target=1.0,
          measure="SELECT COUNT(*) FILTER (WHERE sample_count IS NOT NULL AND source IS NOT NULL), COUNT(*) FROM market_price_stats"),
    Check("PRO-06", "provenance", "Every snapshot loaded is on record", "major", target=1.0,
          why="When it was read, how many listings, how many matched.",
          measure="""SELECT CASE WHEN EXISTS (SELECT 1 FROM market_snapshot_runs) THEN 1 ELSE 0 END, 1"""),

    # ── safeties ─────────────────────────────────────────────────────────────
    Check("SAF-01", "safeties", "Database constraints that keep bad rows out are in place", "critical", target=1.0,
          why="Range and uniqueness rules enforced by Postgres, not only by this audit.",
          measure="""SELECT COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = w.name)
                                                OR EXISTS (SELECT 1 FROM pg_indexes i WHERE i.indexname = w.name)),
                            COUNT(*)
                     FROM (VALUES ('engines_model_required'), ('engines_fuel_known'), ('engines_power_range'),
                                  ('engines_consumption_range'), ('engines_reliability_range'), ('engines_years_ordered'),
                                  ('uq_engines_model_code'), ('generations_model_required'), ('generations_years_ordered'),
                                  ('uq_generations_model_name'), ('uq_vehicle_models_brand_name'),
                                  ('market_price_stats_ordered'), ('market_price_stats_sample'),
                                  ('driving_character_scores_range'), ('uq_driving_character_model'),
                                  ('price_observations_year_km_range')) AS w(name)"""),
]


def _score_rule(found: int, of: int, severity: str) -> float:
    if found == 0:
        return 1.0
    share = found / max(of, found, 1)
    return max(0.0, 1.0 - share * _PENALTY[severity])


def run_check(db, check: Check) -> Result:
    try:
        if check.measure:
            row = db.execute(text(check.measure)).fetchone()
            num, den = float(row[0] or 0), float(row[1] or 0)
            share = num / den if den else 0.0
            return Result(check, min(1.0, share / check.target) if check.target else 1.0,
                          found=int(num) if num == int(num) else round(num, 3), of=int(den))
        rows = db.execute(text(check.sql)).fetchall()
        of = int(db.execute(text(check.total)).scalar() or 0)
        return Result(check, _score_rule(len(rows), of, check.severity), found=len(rows), of=of,
                      examples=[str(r[0]) for r in rows[:8]])
    except Exception as e:                                    # a missing table or column
        db.rollback()
        return Result(check, 0.0, error=str(e).split("\n")[0][:160])


def run_audit(db) -> dict:
    """Run every check. Returns {"score", "dimensions": {name: score}, "results": [Result]}."""
    results = [run_check(db, c) for c in CHECKS]
    dims = {}
    for name in DIMENSIONS:
        mine = [r for r in results if r.check.dim == name]
        weight = sum(_WEIGHT[r.check.severity] for r in mine)
        dims[name] = sum(r.score * _WEIGHT[r.check.severity] for r in mine) / weight if weight else 0.0
    overall = sum(dims[name] * w for name, (_title, w) in DIMENSIONS.items())
    return {"score": round(overall * 100, 1), "dimensions": {k: round(v * 100, 1) for k, v in dims.items()},
            "results": results, "as_of": date.today().isoformat(),
            "critical_failures": [r.check.id for r in results if r.check.severity == "critical" and not r.passed]}


def as_markdown(audit: dict) -> str:
    out = [f"# Data audit — {audit['as_of']}", "", f"**Overall: {audit['score']} / 100**", "",
           "| Dimension | Score | Weight |", "|---|---|---|"]
    for name, (title, w) in DIMENSIONS.items():
        out.append(f"| {title} | {audit['dimensions'][name]} | {int(w * 100)}% |")
    for name, (title, _w) in DIMENSIONS.items():
        out += ["", f"## {title}", "", "| Check | | Result | Score |", "|---|---|---|---|"]
        for r in [r for r in audit["results"] if r.check.dim == name]:
            c = r.check
            if r.error:
                what = f"could not run: {r.error}"
            elif c.measure:
                what = f"{r.found} of {r.of}" + (f" (target {int(c.target * 100)}%)" if r.of > 1 else "")
            else:
                what = "none" if not r.found else f"{r.found} of {r.of}"
            mark = "pass" if r.passed else ("FAIL" if c.severity == "critical" else "open")
            out.append(f"| {c.id} {c.title} ({c.severity}) | {mark} | {what} | {round(r.score * 100)} |")
            for ex in r.examples[:5]:
                out.append(f"| &nbsp;&nbsp;&nbsp;{ex} | | | |")
    return "\n".join(out) + "\n"


def as_json(audit: dict) -> dict:
    return {
        "as_of": audit["as_of"], "score": audit["score"], "dimensions": audit["dimensions"],
        "critical_failures": audit["critical_failures"],
        "checks": [{"id": r.check.id, "dimension": r.check.dim, "title": r.check.title,
                    "severity": r.check.severity, "passed": r.passed, "score": round(r.score * 100),
                    "found": r.found, "of": r.of, "examples": r.examples, "error": r.error}
                   for r in audit["results"]],
    }
