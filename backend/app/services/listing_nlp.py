"""
Listing NLP — extract problem-signal evidence from Standvirtual/OLX descriptions.

Lowest-trust reliability signal (weight=0.15). High noise, requires aggregation.

Logic:
  For each listing description (>100 chars), check if it contains:
    1. A component keyword (motor, caixa, travões, etc.)
    2. A negative phrase near that keyword (avariou, não funciona, defeito, etc.)

  Both must be present in the same description for it to count as a signal.

  Evidence is stored as AGGREGATE rows per (generation_id, component_bucket, month):
    fail_eff = min(N * 0.05, 2.0)   — volume signal capped at 2.0
    weight   = 0.15                   — lowest trust tier

  This means 40 listings mentioning "motor avariado" = fail_eff=2.0
  vs. one NHTSA safety recall = fail_eff=6.0. The ratio reflects the
  difference in reliability between official recall data and seller text.

Honesty note: seller descriptions are authored by sellers trying to sell the car.
  Mentions of problems may be exaggerated or understated. This is the weakest
  evidence source and should only move scores when volume is substantial.
"""

import re
import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ── Component keyword buckets ──────────────────────────────────────────────────
# Each bucket maps a component category to Portuguese keywords.
# A listing "fires" for a bucket if any of its keywords appear in the description.

COMPONENT_BUCKETS: dict[str, list[str]] = {
    "engine": [
        r"\bmotor\b", r"\bcarter\b", r"\bcorreia\b", r"\bcabeça\b",
        r"\bcabeça do motor\b", r"\bbloco\b", r"\bvela\b", r"\binjetor\b",
        r"\binjectores?\b", r"\bturbo\b", r"\bfiltr[oa] de [oó]leo\b",
        r"\bóleo\b", r"\bsuperaquece\b",
    ],
    "transmission": [
        r"\bcaixa de velocidades\b", r"\bcaixa\b", r"\bembraiagem\b",
        r"\bembrage\b", r"\bmudan[çc]as\b", r"\btransmiss[aã]o\b",
        r"\bdsg\b", r"\bautomatic[ao]\b", r"\bcambio\b",
    ],
    "brakes": [
        r"\btrav[oõ]es?\b", r"\btravagem\b", r"\bfrear\b",
        r"\bdiscos de travo\b", r"\bpast[ií]lhas\b",
    ],
    "suspension": [
        r"\bsuspens[aã]o\b", r"\bamortecedor[es]*\b", r"\bmolas?\b",
        r"\brolamentos?\b", r"\btriangulo\b",
    ],
    "electrical": [
        r"\bel[eé]tric[ao]\b", r"\bbateria\b", r"\balternador\b",
        r"\bstart[- ]?stop\b", r"\bsensor[es]*\b", r"\bcurt[oa][-. ]?circuit[oa]\b",
        r"\bfus[ií]vel\b", r"\bcentralina\b",
    ],
    "body": [
        r"\bcarroçaria\b", r"\boxid[aã]\b", r"\bferrugen\b", r"\bcorros[aã]\b",
        r"\brachaduras?\b", r"\bamolgad[ao]s?\b",
    ],
}

# ── Negative phrases ───────────────────────────────────────────────────────────
# At least one of these must also appear in the description (anywhere, not just near
# the component keyword — Portuguese descriptions tend to be short enough that
# proximity is not needed).

NEGATIVE_PATTERNS = re.compile(
    r"("
    r"problemas?(?: com| de| no| na| nos| nas)?"
    r"|avari[ao]u"
    r"|avaria"
    r"|defeito"
    r"|n[aã]o funciona"
    r"|est[aá] partido"
    r"|partido"
    r"|partido"
    r"|barulho"
    r"|ru[ií]do"
    r"|perco?\b"
    r"|perd[eu]"
    r"|fuma"
    r"|fumega"
    r"|falha"
    r"|falhando"
    r"|erro"
    r"|luz de avaria"
    r"|luz de erro"
    r"|luz vermelha"
    r"|fraco\b"
    r"|irregular"
    r"|treme\b"
    r"|vibra[çc][aã]o"
    r"|excesso de consumo"
    r"|consome muito"
    r"|vaza"
    r"|vaz[ao]"
    r"|escapes de [oó]leo"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Pre-compile component patterns per bucket
_COMPILED_BUCKETS: dict[str, re.Pattern] = {
    bucket: re.compile("|".join(patterns), re.IGNORECASE | re.UNICODE)
    for bucket, patterns in COMPONENT_BUCKETS.items()
}

# Minimum description length to consider (filter boilerplate/dealer templates)
MIN_DESC_LEN = 100


def _detect_signals(description: str) -> list[str]:
    """
    Return list of component buckets that have a problem signal in this description.
    Both a component keyword AND a negative phrase must be present.
    """
    if not description or len(description) < MIN_DESC_LEN:
        return []

    has_negative = bool(NEGATIVE_PATTERNS.search(description))
    if not has_negative:
        return []

    fired = []
    for bucket, pattern in _COMPILED_BUCKETS.items():
        if pattern.search(description):
            fired.append(bucket)

    return fired


def _nlp_evidence_url(generation_id: int, bucket: str, observed_month: date) -> str:
    """Stable URL for deduplication of aggregate NLP evidence rows."""
    return f"nlp://sv/{generation_id}/{bucket}/{observed_month.strftime('%Y-%m')}"


def run_nlp_pass(db: Session, observed_month: Optional[date] = None) -> dict:
    """
    Batch NLP pass over normalized_listings.

    For each generation:
      - Read descriptions from normalized_listings (this month's new rows)
      - Count listings firing per component bucket
      - Write / update aggregate evidence rows in reliability_evidence

    Safe to run after each scraping run (skips existing evidence rows via ON CONFLICT).

    Returns stats: {generations_processed, signals_found, evidence_rows_written, errors}
    """
    if observed_month is None:
        observed_month = date.today().replace(day=1)

    stats = {
        "generations_processed": 0,
        "descriptions_scanned": 0,
        "signals_found": 0,
        "evidence_rows_written": 0,
        "errors": 0,
    }

    # Load all distinct generation_ids that have listings this month
    gen_rows = db.execute(text("""
        SELECT DISTINCT
            nl.generation_id,
            b.name  AS brand_name,
            vm.name AS model_name
        FROM normalized_listings nl
        JOIN generations g   ON nl.generation_id = g.id
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        WHERE nl.generation_id IS NOT NULL
          AND nl.description IS NOT NULL
          AND length(nl.description) >= :min_len
        ORDER BY nl.generation_id
    """), {"min_len": MIN_DESC_LEN}).mappings().fetchall()

    for gen_row in gen_rows:
        gen_id = gen_row["generation_id"]

        try:
            # Fetch descriptions for this generation
            desc_rows = db.execute(text("""
                SELECT description
                FROM normalized_listings
                WHERE generation_id = :gen_id
                  AND description IS NOT NULL
                  AND length(description) >= :min_len
            """), {"gen_id": gen_id, "min_len": MIN_DESC_LEN}).fetchall()

            # Tally signals per bucket
            bucket_counts: dict[str, int] = {}
            for (desc,) in desc_rows:
                stats["descriptions_scanned"] += 1
                signals = _detect_signals(desc)
                for bucket in signals:
                    bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
                    stats["signals_found"] += 1

            # Write one aggregate evidence row per fired bucket
            for bucket, n in bucket_counts.items():
                if n == 0:
                    continue

                ev_url = _nlp_evidence_url(gen_id, bucket, observed_month)

                # Skip if already written this month
                existing = db.execute(text("""
                    SELECT 1 FROM reliability_evidence
                    WHERE generation_id = :gid AND source_url = :url
                    LIMIT 1
                """), {"gid": gen_id, "url": ev_url}).fetchone()
                if existing:
                    continue

                fail_eff = round(min(n * 0.05, 2.0), 3)

                db.execute(text("""
                    INSERT INTO reliability_evidence
                        (generation_id, evidence_type, source, source_url,
                         observed_month, fail_eff, succ_eff, weight, payload)
                    VALUES
                        (:gen_id, 'nlp_complaint', 'standvirtual_nlp', :url,
                         :month, :fail_eff, 0, 0.15, :payload::jsonb)
                    ON CONFLICT DO NOTHING
                """), {
                    "gen_id":   gen_id,
                    "url":      ev_url,
                    "month":    observed_month,
                    "fail_eff": fail_eff,
                    "payload":  __import__("json").dumps({
                        "component_bucket": bucket,
                        "n_listings": n,
                        "fail_eff": fail_eff,
                        "brand": gen_row["brand_name"],
                        "model": gen_row["model_name"],
                    }),
                })
                stats["evidence_rows_written"] += 1

            stats["generations_processed"] += 1

        except Exception as e:
            logger.error(
                f"NLP pass error gen={gen_id} "
                f"{gen_row['brand_name']} {gen_row['model_name']}: {e}"
            )
            stats["errors"] += 1

    db.commit()
    logger.info(f"NLP evidence pass complete: {stats}")
    return stats
