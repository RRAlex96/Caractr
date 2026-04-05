"""
Caractr MVP Profile Testing Suite
Runs 20 diverse personas through /api/recommend and analyses:
  - Repetitiveness (which models dominate across profiles)
  - Adequacy (do recommendations match declared priorities?)
  - Coverage (how many distinct models appear at all?)

Usage:
    # With the backend running on localhost:8000
    python tests/test_profiles.py

    # Against a different host
    python tests/test_profiles.py --host https://api.caractr.pt
"""

import sys
import io
import argparse
import requests
from collections import Counter, defaultdict

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 20 TEST PERSONAS — diverse across all 6 profile dimensions
# ─────────────────────────────────────────────────────────────────────────────
PROFILES = [
    {
        "id": "P01", "label": "Daily city commuter (budget tight)",
        "p1_context": "cidade", "p2_relationship": 0.2, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.2, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 6000, "p8_budget_max": 13000,
        "expect_top": ["economy", "reliability"],
    },
    {
        "id": "P02", "label": "Highway road warrior (comfort first)",
        "p1_context": "estrada", "p2_relationship": 0.3, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.3, "p6_aversion": "potencia",
        "p7_dream_car": None, "p8_budget_min": 15000, "p8_budget_max": 30000,
        "expect_top": ["comfort", "reliability"],
    },
    {
        "id": "P03", "label": "Driving enthusiast (feels every curve)",
        "p1_context": "misto", "p2_relationship": 0.9, "p3_driving_style": 0.9,
        "p4_risk": 0.8, "p5_presence": 0.5, "p6_aversion": "nenhuma",
        "p7_dream_car": "bmw_m3", "p8_budget_min": 20000, "p8_budget_max": 38000,
        "expect_top": ["driving", "status"],
    },
    {
        "id": "P04", "label": "Young family (needs space, reliability)",
        "p1_context": "familia", "p2_relationship": 0.4, "p3_driving_style": 0.2,
        "p4_risk": 0.1, "p5_presence": 0.3, "p6_aversion": "espaco",
        "p7_dream_car": "volvo_xc60", "p8_budget_min": 18000, "p8_budget_max": 36000,
        "expect_top": ["practical", "reliability"],
    },
    {
        "id": "P05", "label": "Status seeker (presence matters)",
        "p1_context": "misto", "p2_relationship": 0.5, "p3_driving_style": 0.4,
        "p4_risk": 0.5, "p5_presence": 0.9, "p6_aversion": "nenhuma",
        "p7_dream_car": "range_rover", "p8_budget_min": 35000, "p8_budget_max": 70000,
        "expect_top": ["status", "comfort"],
    },
    {
        "id": "P06", "label": "Budget pragmatist (just needs to work)",
        "p1_context": "cidade", "p2_relationship": 0.1, "p3_driving_style": 0.1,
        "p4_risk": 0.1, "p5_presence": 0.1, "p6_aversion": "fiabilidade",
        "p7_dream_car": "toyota_yaris", "p8_budget_min": 5000, "p8_budget_max": 12000,
        "expect_top": ["economy", "reliability"],
    },
    {
        "id": "P07", "label": "Retired road tripper (gentle + comfortable)",
        "p1_context": "estrada", "p2_relationship": 0.3, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.4, "p6_aversion": "conforto",
        "p7_dream_car": None, "p8_budget_min": 18000, "p8_budget_max": 35000,
        "expect_top": ["comfort", "reliability"],
    },
    {
        "id": "P08", "label": "Weekend track enthusiast (max performance)",
        "p1_context": "estrada", "p2_relationship": 1.0, "p3_driving_style": 1.0,
        "p4_risk": 0.9, "p5_presence": 0.6, "p6_aversion": "nenhuma",
        "p7_dream_car": "porsche_911", "p8_budget_min": 40000, "p8_budget_max": 85000,
        "expect_top": ["driving", "status"],
    },
    {
        "id": "P09", "label": "Urban tech-forward (EV mindset)",
        "p1_context": "cidade", "p2_relationship": 0.5, "p3_driving_style": 0.3,
        "p4_risk": 0.3, "p5_presence": 0.7, "p6_aversion": "nenhuma",
        "p7_dream_car": "tesla_model3", "p8_budget_min": 25000, "p8_budget_max": 50000,
        "expect_top": ["status", "economy"],
    },
    {
        "id": "P10", "label": "Reliability obsessive (never breaks down)",
        "p1_context": "misto", "p2_relationship": 0.4, "p3_driving_style": 0.3,
        "p4_risk": 0.1, "p5_presence": 0.2, "p6_aversion": "fiabilidade",
        "p7_dream_car": "lexus_ls", "p8_budget_min": 20000, "p8_budget_max": 45000,
        "expect_top": ["reliability", "comfort"],
    },
    {
        "id": "P11", "label": "Young professional (city, sporty, affordable)",
        "p1_context": "cidade", "p2_relationship": 0.65, "p3_driving_style": 0.55,
        "p4_risk": 0.45, "p5_presence": 0.6, "p6_aversion": "nenhuma",
        "p7_dream_car": "vw_golf_gti", "p8_budget_min": 16000, "p8_budget_max": 28000,
        "expect_top": ["driving", "economy"],
    },
    {
        "id": "P12", "label": "Large family (max space, off-road capable)",
        "p1_context": "familia", "p2_relationship": 0.4, "p3_driving_style": 0.3,
        "p4_risk": 0.3, "p5_presence": 0.4, "p6_aversion": "espaco",
        "p7_dream_car": "toyota_landcruiser", "p8_budget_min": 28000, "p8_budget_max": 58000,
        "expect_top": ["practical", "reliability"],
    },
    {
        "id": "P13", "label": "Speed demon on a budget (hot hatch)",
        "p1_context": "estrada", "p2_relationship": 0.9, "p3_driving_style": 0.9,
        "p4_risk": 0.9, "p5_presence": 0.4, "p6_aversion": "nenhuma",
        "p7_dream_car": "honda_civic_typer", "p8_budget_min": 18000, "p8_budget_max": 32000,
        "expect_top": ["driving", "economy"],
    },
    {
        "id": "P14", "label": "Luxury daily (city + prestige + silence)",
        "p1_context": "cidade", "p2_relationship": 0.5, "p3_driving_style": 0.3,
        "p4_risk": 0.3, "p5_presence": 0.95, "p6_aversion": "nenhuma",
        "p7_dream_car": "mercedes_s", "p8_budget_min": 50000, "p8_budget_max": 95000,
        "expect_top": ["status", "comfort"],
    },
    {
        "id": "P15", "label": "Eco-conscious pragmatist (low footprint)",
        "p1_context": "cidade", "p2_relationship": 0.3, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.4, "p6_aversion": "nenhuma",
        "p7_dream_car": "tesla_model3", "p8_budget_min": 28000, "p8_budget_max": 52000,
        "expect_top": ["economy", "reliability"],
    },
    {
        "id": "P16", "label": "Adventure off-roader (family + terrain)",
        "p1_context": "familia", "p2_relationship": 0.6, "p3_driving_style": 0.5,
        "p4_risk": 0.5, "p5_presence": 0.5, "p6_aversion": "nenhuma",
        "p7_dream_car": "defender", "p8_budget_min": 22000, "p8_budget_max": 48000,
        "expect_top": ["practical", "driving"],
    },
    {
        "id": "P17", "label": "Minimalist city dweller (smallest, cheapest)",
        "p1_context": "cidade", "p2_relationship": 0.1, "p3_driving_style": 0.1,
        "p4_risk": 0.2, "p5_presence": 0.1, "p6_aversion": "nenhuma",
        "p7_dream_car": "nenhum", "p8_budget_min": 5000, "p8_budget_max": 13000,
        "expect_top": ["economy", "practical"],
    },
    {
        "id": "P18", "label": "Wealthy petrolhead (track-capable GT)",
        "p1_context": "estrada", "p2_relationship": 1.0, "p3_driving_style": 1.0,
        "p4_risk": 0.95, "p5_presence": 0.8, "p6_aversion": "nenhuma",
        "p7_dream_car": "alfa_giulia_qv", "p8_budget_min": 38000, "p8_budget_max": 75000,
        "expect_top": ["driving", "status"],
    },
    {
        "id": "P19", "label": "Suburban family upgrade (safe + reliable)",
        "p1_context": "familia", "p2_relationship": 0.5, "p3_driving_style": 0.3,
        "p4_risk": 0.2, "p5_presence": 0.5, "p6_aversion": "fiabilidade",
        "p7_dream_car": "volvo_xc60", "p8_budget_min": 22000, "p8_budget_max": 45000,
        "expect_top": ["reliability", "practical"],
    },
    {
        "id": "P20", "label": "First-time buyer (cautious, low budget)",
        "p1_context": "cidade", "p2_relationship": 0.3, "p3_driving_style": 0.3,
        "p4_risk": 0.1, "p5_presence": 0.3, "p6_aversion": "fiabilidade",
        "p7_dream_car": "dacia_duster", "p8_budget_min": 6000, "p8_budget_max": 15000,
        "expect_top": ["economy", "reliability"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

ANSI = {
    "reset": "\033[0m", "bold": "\033[1m",
    "green": "\033[92m", "red": "\033[91m",
    "yellow": "\033[93m", "cyan": "\033[96m", "dim": "\033[2m",
}

def c(code, text):
    return f"{ANSI[code]}{text}{ANSI['reset']}"


def payload_for(p):
    keys = ["p1_context", "p2_relationship", "p3_driving_style",
            "p4_risk", "p5_presence", "p6_aversion", "p7_dream_car",
            "p8_budget_min", "p8_budget_max"]
    return {k: p[k] for k in keys if p.get(k) is not None}


def adequacy_check(profile_result, expect_dims):
    """
    Returns True if either of the top-2 expected dimensions ranks in
    the top-3 of the returned profile vector.
    """
    vec = profile_result.get("profile", {})
    if not vec:
        return False
    ranked = sorted(vec.items(), key=lambda x: x[1], reverse=True)
    top3 = [d for d, _ in ranked[:3]]
    return any(e in top3 for e in expect_dims)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run(host: str):
    url = f"{host.rstrip('/')}/api/recommend"
    print(c("bold", f"\n{'═'*70}"))
    print(c("bold", f"  CARACTR PROFILE TEST — {len(PROFILES)} personas → {url}"))
    print(c("bold", f"{'═'*70}\n"))

    results = []
    model_freq: Counter = Counter()       # model_id → total appearances
    pos_freq: Counter = Counter()         # (model_id, position) → count
    profile_models: dict = {}             # persona id → list of model names

    for p in PROFILES:
        try:
            resp = requests.post(url, json=payload_for(p), timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(c("red", f"  ✗ {p['id']} {p['label'][:40]}: ERROR — {e}"))
            results.append({"id": p["id"], "ok": False})
            continue

        models = data.get("recommendations", [])
        model_names = [m.get("full_name") or (m.get("brand_name", "?") + " " + m.get("model_name", "?")) for m in models]
        model_ids   = [m.get("model_id", 0) for m in models]
        adequate    = adequacy_check(data, p["expect_top"])

        for i, mid in enumerate(model_ids):
            model_freq[mid] += 1
            pos_freq[(mid, i + 1)] += 1

        profile_models[p["id"]] = model_names

        status = c("green", "✓ adequate") if adequate else c("yellow", "⚠ mismatch")
        print(f"  {c('cyan', p['id'])}  {p['label'][:42]:<43}  {status}")
        for i, name in enumerate(model_names, 1):
            print(c("dim", f"         {i}. {name}"))
        print()

        results.append({
            "id": p["id"], "ok": True,
            "models": model_names,
            "_raw_models": models,
            "adequate": adequate,
            "profile": data.get("profile", {}),
        })

    # ── Repetitiveness analysis ──────────────────────────────────────────────
    print(c("bold", f"\n{'─'*70}"))
    print(c("bold", "  REPETITIVENESS ANALYSIS"))
    print(c("bold", f"{'─'*70}"))

    ok_results   = [r for r in results if r["ok"]]
    total_slots  = len(ok_results) * 5  # 5 recommendations per persona

    # Unique model IDs across all runs
    total_unique = len(model_freq)

    print(f"\n  Total profiles run:    {len(ok_results)}/{len(PROFILES)}")
    print(f"  Total recommendation slots: {total_slots}")
    print(f"  Distinct models seen:  {c('cyan', str(total_unique))}")

    if total_unique < 8:
        diversity = c("red", "LOW  ← consider expanding model pool")
    elif total_unique < 15:
        diversity = c("yellow", "MODERATE")
    else:
        diversity = c("green", "GOOD")
    print(f"  Diversity rating:      {diversity}\n")

    print(f"  {'Model':<35}  {'Appearances':>11}  {'% of slots':>10}  {'Pos freq'}")
    print(f"  {'─'*35}  {'─'*11}  {'─'*10}  {'─'*20}")

    # Build model_id -> name lookup from results
    id_to_name: dict = {}
    for r in ok_results:
        for name_str in r.get("models", []):
            pass  # names collected below
    id_to_name = {}
    for r in ok_results:
        raw = r.get("_raw_models", [])
        for m in raw:
            id_to_name[m["model_id"]] = m.get("full_name") or f"model#{m['model_id']}"

    for mid, count in model_freq.most_common(20):
        name = id_to_name.get(mid, f"model#{mid}")
        pct  = count / total_slots * 100
        pos  = ", ".join(f"#{k[1]}×{v}" for k, v in sorted(pos_freq.items())
                         if k[0] == mid and v > 0)
        bar  = "█" * int(pct / 2)
        flag = c("red", " ← over-represented") if pct > 35 else ""
        print(f"  {name:<35}  {count:>11}  {pct:>9.1f}%  {bar}{flag}")

    # ── Adequacy summary ────────────────────────────────────────────────────
    print(c("bold", f"\n{'─'*70}"))
    print(c("bold", "  ADEQUACY SUMMARY"))
    print(c("bold", f"{'─'*70}"))

    adequate_count = sum(1 for r in ok_results if r.get("adequate"))
    pct_adequate   = adequate_count / len(ok_results) * 100 if ok_results else 0

    print(f"\n  Profiles with ≥1 expected dimension in top-3 of profile vector:")
    print(f"  {adequate_count}/{len(ok_results)} ({pct_adequate:.0f}%)")

    if pct_adequate >= 80:
        verdict = c("green", "PASS — scoring aligns well with declared priorities")
    elif pct_adequate >= 60:
        verdict = c("yellow", "WARN — some mismatches, review edge cases")
    else:
        verdict = c("red", "FAIL — significant scoring drift, investigate build_profile()")
    print(f"\n  Verdict: {verdict}")

    # ── Mismatch details ────────────────────────────────────────────────────
    mismatches = [r for r in ok_results if not r.get("adequate")]
    if mismatches:
        print(f"\n  Profiles that didn't match expected dimensions:")
        for r in mismatches:
            p = next(x for x in PROFILES if x["id"] == r["id"])
            vec = r["profile"]
            top2 = sorted(vec.items(), key=lambda x: x[1], reverse=True)[:2]
            top2_str = ", ".join(f"{d}={v:.2f}" for d, v in top2)
            print(f"    {c('yellow', r['id'])}  {p['label'][:45]}")
            print(f"         expected: {p['expect_top']}")
            print(f"         got top2: {top2_str}")

    # ── Final summary ───────────────────────────────────────────────────────
    print(c("bold", f"\n{'═'*70}"))
    errors = len(results) - len(ok_results)
    print(f"  {c('green', str(len(ok_results)))} profiles OK  |  "
          f"{c('red', str(errors))} errors  |  "
          f"{adequate_count}/{len(ok_results)} adequate  |  "
          f"{total_unique} distinct models")
    print(c("bold", f"{'═'*70}\n"))

    return 0 if errors == 0 and pct_adequate >= 60 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Caractr MVP profile test suite")
    parser.add_argument("--host", default="http://localhost:8000",
                        help="Backend base URL (default: http://localhost:8000)")
    args = parser.parse_args()

    sys.exit(run(args.host))
