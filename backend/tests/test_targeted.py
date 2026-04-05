"""
Caractr Targeted Diagnostic Suite
Runs 18 strategically designed profiles and prints a rich analysis table
for manual review. Each profile is annotated with what it's testing and
what a good result looks like.

Usage:
    python tests/test_targeted.py [--host http://localhost:8000]
"""

import sys, io, argparse, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# TARGETED PROFILES — 18 surgical tests
# ─────────────────────────────────────────────────────────────────────────────

PROFILES = [

    # ── GROUP 1: Generalista brand challenge ──────────────────────────────────
    {
        "group": "G1a",
        "label": "Pure value seeker — mid budget, zero status",
        "test": "Should surface Skoda, Hyundai, Renault, VW — NOT BMW/Mercedes",
        "red_flag": "BMW or Mercedes in top 3",
        "p1_context": "misto", "p2_relationship": 0.3, "p3_driving_style": 0.3,
        "p4_risk": 0.2, "p5_presence": 0.05, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 14000, "p8_budget_max": 22000,
    },
    {
        "group": "G1b",
        "label": "Family on tight budget — SUV needed",
        "test": "Should surface Skoda Kodiaq, VW Tiguan, Hyundai Tucson, SEAT Ateca",
        "red_flag": "All results are premium brands (Audi/BMW/Mercedes)",
        "p1_context": "familia", "p2_relationship": 0.4, "p3_driving_style": 0.3,
        "p4_risk": 0.2, "p5_presence": 0.2, "p6_aversion": "espaco",
        "p7_dream_car": None, "p8_budget_min": 18000, "p8_budget_max": 30000,
    },
    {
        "group": "G1c",
        "label": "City daily, low care, practical, no status",
        "test": "Should surface Renault Clio, Hyundai i20, Opel Corsa, SEAT Ibiza",
        "red_flag": "Premium brands in top 3 for a zero-status city user",
        "p1_context": "cidade", "p2_relationship": 0.15, "p3_driving_style": 0.15,
        "p4_risk": 0.15, "p5_presence": 0.05, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 8000, "p8_budget_max": 16000,
    },

    # ── GROUP 2: Aversion stress tests ────────────────────────────────────────
    {
        "group": "G2a",
        "label": "Aversion=fiabilidade — driving enthusiast",
        "test": "Alfa Giulia (low reliability) should be penalised or absent",
        "red_flag": "Alfa Giulia in top 2 despite fiabilidade aversion",
        "p1_context": "estrada", "p2_relationship": 0.85, "p3_driving_style": 0.85,
        "p4_risk": 0.7, "p5_presence": 0.5, "p6_aversion": "fiabilidade",
        "p7_dream_car": "bmw_m3", "p8_budget_min": 20000, "p8_budget_max": 42000,
    },
    {
        "group": "G2b",
        "label": "Aversion=espaco — non-family, city",
        "test": "Citadinos and compactos should survive; only small-space models suppressed",
        "red_flag": "Low family_score citadinos appear — aversion filter not working",
        "p1_context": "cidade", "p2_relationship": 0.4, "p3_driving_style": 0.4,
        "p4_risk": 0.3, "p5_presence": 0.4, "p6_aversion": "espaco",
        "p7_dream_car": None, "p8_budget_min": 15000, "p8_budget_max": 28000,
    },
    {
        "group": "G2c",
        "label": "Aversion=conforto — highway comfort seeker",
        "test": "Low comfort_score models suppressed even on highway profile",
        "red_flag": "Models with comfort_score < 6 appear in results",
        "p1_context": "estrada", "p2_relationship": 0.3, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.3, "p6_aversion": "conforto",
        "p7_dream_car": None, "p8_budget_min": 18000, "p8_budget_max": 35000,
    },
    {
        "group": "G2d",
        "label": "Aversion=potencia — hates boring cars",
        "test": "Low driving_fun models suppressed; results should all have driving_fun >= 6",
        "red_flag": "Models with driving_fun_score < 6 appear",
        "p1_context": "misto", "p2_relationship": 0.6, "p3_driving_style": 0.6,
        "p4_risk": 0.5, "p5_presence": 0.5, "p6_aversion": "potencia",
        "p7_dream_car": None, "p8_budget_min": 16000, "p8_budget_max": 30000,
    },

    # ── GROUP 3: Dream car contradictions ─────────────────────────────────────
    {
        "group": "G3a",
        "label": "Porsche 911 dream — 8-15k budget (can't afford)",
        "test": "Profile should tilt toward driving/status but all results within budget",
        "red_flag": "Porsche appears in results despite budget impossibility",
        "p1_context": "misto", "p2_relationship": 0.7, "p3_driving_style": 0.7,
        "p4_risk": 0.6, "p5_presence": 0.5, "p6_aversion": "nenhuma",
        "p7_dream_car": "porsche_911", "p8_budget_min": 8000, "p8_budget_max": 15000,
    },
    {
        "group": "G3b",
        "label": "Dacia Duster dream — high presence, high budget",
        "test": "Status contradiction — does the Dacia dream override presence signal?",
        "red_flag": "Dacia/budget brands dominate despite presence=0.9 and 40k budget",
        "p1_context": "misto", "p2_relationship": 0.4, "p3_driving_style": 0.3,
        "p4_risk": 0.3, "p5_presence": 0.9, "p6_aversion": "nenhuma",
        "p7_dream_car": "dacia_duster", "p8_budget_min": 25000, "p8_budget_max": 45000,
    },
    {
        "group": "G3c",
        "label": "Mercedes S dream — low budget 10-18k",
        "test": "Budget forces affordable results; profile vector leans status/comfort",
        "red_flag": "Mercedes S-Class appears despite being 3x the budget",
        "p1_context": "cidade", "p2_relationship": 0.3, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.7, "p6_aversion": "nenhuma",
        "p7_dream_car": "mercedes_s", "p8_budget_min": 10000, "p8_budget_max": 18000,
    },
    {
        "group": "G3d",
        "label": "Toyota Yaris dream — full driving enthusiast",
        "test": "Economy dream vs driving profile — does the vector balance or get pulled too far?",
        "red_flag": "Results are pure economy cars with no driving character",
        "p1_context": "estrada", "p2_relationship": 0.9, "p3_driving_style": 0.9,
        "p4_risk": 0.8, "p5_presence": 0.4, "p6_aversion": "nenhuma",
        "p7_dream_car": "toyota_yaris", "p8_budget_min": 15000, "p8_budget_max": 28000,
    },

    # ── GROUP 4: Budget extremes ───────────────────────────────────────────────
    {
        "group": "G4a",
        "label": "Ultra-low budget (4-8k)",
        "test": "Only truly affordable models; what's at the absolute floor?",
        "red_flag": "Models with avg_price > 9200 (stretch) appear",
        "p1_context": "cidade", "p2_relationship": 0.2, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.2, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 4000, "p8_budget_max": 8000,
    },
    {
        "group": "G4b",
        "label": "Maximum luxury (80k-150k)",
        "test": "Porsche, Maserati, top Mercedes/BMW — is the ultra-premium pool correct?",
        "red_flag": "Mid-range brands appear when budget supports full luxury",
        "p1_context": "estrada", "p2_relationship": 0.7, "p3_driving_style": 0.6,
        "p4_risk": 0.5, "p5_presence": 0.9, "p6_aversion": "nenhuma",
        "p7_dream_car": "porsche_911", "p8_budget_min": 80000, "p8_budget_max": 150000,
    },

    # ── GROUP 5: Body type edge cases ─────────────────────────────────────────
    {
        "group": "G5a",
        "label": "MPV trigger — max family, max practical, economy",
        "test": "Dacia Jogger (only MPV) should appear; check if MPV adjacency works",
        "red_flag": "No MPV appears at all — Dacia Jogger completely absent",
        "p1_context": "familia", "p2_relationship": 0.2, "p3_driving_style": 0.1,
        "p4_risk": 0.1, "p5_presence": 0.1, "p6_aversion": "espaco",
        "p7_dream_car": None, "p8_budget_min": 12000, "p8_budget_max": 22000,
    },
    {
        "group": "G5b",
        "label": "Carrinha trigger — estrada + comfort + reliability",
        "test": "Volvo V60 (only carrinha) should appear for estate-ideal profile",
        "red_flag": "Volvo V60 absent — carrinhas being ignored entirely",
        "p1_context": "estrada", "p2_relationship": 0.4, "p3_driving_style": 0.3,
        "p4_risk": 0.2, "p5_presence": 0.5, "p6_aversion": "conforto",
        "p7_dream_car": "volvo_xc60", "p8_budget_min": 25000, "p8_budget_max": 42000,
    },
    {
        "group": "G5c",
        "label": "Wildcard trigger — mild family profile, sports car score",
        "test": "A sports compacto should appear as wildcard for misto profile",
        "red_flag": "No is_wildcard=true model in results",
        "p1_context": "misto", "p2_relationship": 0.75, "p3_driving_style": 0.75,
        "p4_risk": 0.6, "p5_presence": 0.45, "p6_aversion": "nenhuma",
        "p7_dream_car": "mazda_mx5", "p8_budget_min": 18000, "p8_budget_max": 32000,
    },

    # ── GROUP 6: Latent EV preference ─────────────────────────────────────────
    {
        "group": "G6a",
        "label": "EV purely from profile — no dream car signal",
        "test": "City + economy + no dream car → should EVs/hybrids appear organically?",
        "red_flag": "No EV or hybrid at all — economy signal not connecting to EV pool",
        "p1_context": "cidade", "p2_relationship": 0.25, "p3_driving_style": 0.2,
        "p4_risk": 0.2, "p5_presence": 0.3, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 22000, "p8_budget_max": 38000,
    },
    {
        "group": "G6b",
        "label": "Hybrid preference — reliability + economy + highway",
        "test": "Toyota Prius, Lexus NX, Corolla Hybrid should rank highly",
        "red_flag": "No hybrid/low-consumption model in top 3",
        "p1_context": "estrada", "p2_relationship": 0.3, "p3_driving_style": 0.25,
        "p4_risk": 0.15, "p5_presence": 0.35, "p6_aversion": "nenhuma",
        "p7_dream_car": None, "p8_budget_min": 20000, "p8_budget_max": 38000,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

GROUPS = {
    "G1": "GENERALISTA BRAND CHALLENGE",
    "G2": "AVERSION STRESS TESTS",
    "G3": "DREAM CAR CONTRADICTIONS",
    "G4": "BUDGET EXTREMES",
    "G5": "BODY TYPE EDGE CASES",
    "G6": "LATENT EV PREFERENCE",
}

def payload_for(p):
    keys = ["p1_context","p2_relationship","p3_driving_style","p4_risk",
            "p5_presence","p6_aversion","p7_dream_car","p8_budget_min","p8_budget_max"]
    return {k: p[k] for k in keys if p.get(k) is not None}

def run(host):
    url = f"{host.rstrip('/')}/api/recommend"
    current_group = None

    for p in PROFILES:
        grp = p["group"][:2]
        if grp != current_group:
            current_group = grp
            print(f"\n{'━'*72}")
            print(f"  {grp} — {GROUPS[grp]}")
            print(f"{'━'*72}")

        try:
            resp = requests.post(url, json=payload_for(p), timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"\n  [{p['group']}] ERROR: {e}")
            continue

        recs   = data.get("recommendations", [])
        prof   = data.get("profile", {})
        budget = f"{p['p8_budget_min']//1000}k–{p['p8_budget_max']//1000}k €"
        dream  = p.get("p7_dream_car") or "—"

        # Profile vector ranked
        prof_ranked = sorted(prof.items(), key=lambda x: x[1], reverse=True)
        prof_str = "  ".join(f"{d[:3].upper()}={v:.2f}" for d, v in prof_ranked[:4])

        print(f"\n  [{p['group']}] {p['label']}")
        print(f"  Input:   ctx={p['p1_context']}  rel={p['p2_relationship']}  style={p['p3_driving_style']}  "
              f"risk={p['p4_risk']}  pres={p['p5_presence']}  aver={p['p6_aversion']}  dream={dream}  budget={budget}")
        print(f"  Vector:  {prof_str}")
        print(f"  Test:    {p['test']}")
        print(f"  Watch:   ⚠  {p['red_flag']}")
        print()

        for i, m in enumerate(recs, 1):
            flags = []
            if m.get("is_stretch"):  flags.append("STRETCH")
            if m.get("is_wildcard"): flags.append("WILDCARD")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            pr = m.get("price_range", {})
            price_str = f"{pr.get('min',0)//1000}k–{pr.get('max',0)//1000}k €" if pr else "?"
            print(f"    {i}. {m.get('full_name','?'):<35s}  "
                  f"{m.get('body_type','?'):10s}  {m.get('segment','?'):8s}  "
                  f"{price_str:12s}{flag_str}")

        print(f"\n  Headline for #1: \"{recs[0].get('headline','?')}\"" if recs else "")
        print(f"  {'─'*68}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://localhost:8000")
    args = parser.parse_args()
    run(args.host)
