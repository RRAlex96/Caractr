"""Recommender check on fixed buyer personas (read-only).

    python -m scripts.recommender_personas [-v] [persona-letter]

Prints the top 5 per persona; with -v, the top 15 ranked with their scores.
Run it before and after any change to recommend_service scoring and compare."""
import copy
import json
import os
import sys

BACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACK)
os.chdir(BACK)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BACK, ".env"))
from sqlalchemy import text  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.services import recommend_service as rs  # noqa: E402

PERSONAS = {
    "A família, só transporte, fiabilidade, discreto, 10-15k":
        dict(p1_context="familia", p2_relationship="apenas_transporte", p3_driving_style="suave_previsivel",
             p5_presence="discreto", p6_aversion="fiabilidade", p8_budget_min=10000, p8_budget_max=15000),
    "B família, gosta de conduzir, bom aspeto, espaço, 20-30k":
        dict(p1_context="familia", p2_relationship="gosto_conduzir", p3_driving_style="confortavel_com_alma",
             p5_presence="bom_aspeto", p6_aversion="espaco", p8_budget_min=20000, p8_budget_max=30000),
    "C cidade, só transporte, discreto, economia/nenhuma, 8-12k":
        dict(p1_context="cidade", p2_relationship="apenas_transporte", p3_driving_style="suave_previsivel",
             p5_presence="discreto", p6_aversion="nenhuma", p8_budget_min=8000, p8_budget_max=12000),
    "D estrada, gosta de conduzir, bom aspeto, conforto, 15-25k":
        dict(p1_context="estrada", p2_relationship="gosto_conduzir", p3_driving_style="confortavel_com_alma",
             p5_presence="bom_aspeto", p6_aversion="conforto", p8_budget_min=15000, p8_budget_max=25000),
    "E misto, adora conduzir, vire cabeças, potência, 25-40k":
        dict(p1_context="misto", p2_relationship="adoro_conduzir", p3_driving_style="dinamico_envolvente",
             p5_presence="vire_cabecas", p6_aversion="potencia", p8_budget_min=25000, p8_budget_max=40000),
    "F misto, só transporte, discreto, fiabilidade, 15-20k":
        dict(p1_context="misto", p2_relationship="apenas_transporte", p3_driving_style="suave_previsivel",
             p5_presence="discreto", p6_aversion="fiabilidade", p8_budget_min=15000, p8_budget_max=20000),
    "G estrada, só transporte, discreto, fiabilidade, 12-18k (comercial que faz km)":
        dict(p1_context="estrada", p2_relationship="apenas_transporte", p3_driving_style="suave_previsivel",
             p5_presence="discreto", p6_aversion="fiabilidade", p8_budget_min=12000, p8_budget_max=18000),
    "H cidade, gosta de conduzir, bom aspeto, nenhuma, 12-20k":
        dict(p1_context="cidade", p2_relationship="gosto_conduzir", p3_driving_style="confortavel_com_alma",
             p5_presence="bom_aspeto", p6_aversion="nenhuma", p8_budget_min=12000, p8_budget_max=20000),
}


def run(verbose=False, only=None):
    db = SessionLocal()
    db.execute(text("SET TRANSACTION READ ONLY"))
    try:
        base_models = rs.load_models(db)
    finally:
        db.rollback()
        db.close()
    out = {}
    for name, answers in PERSONAS.items():
        if only and not name.startswith(only):
            continue
        answers = dict(answers)
        profile, signals = rs.build_profile(answers)
        models = copy.deepcopy(base_models)
        passed, stretch = rs.apply_hard_constraints(models, answers)
        for m in passed:
            m["vector"] = rs._build_model_vector(m)
            m["_score"] = rs.score_model(m, profile, answers)
        for m in stretch:
            m["vector"] = rs._build_model_vector(m)
            m["_score"] = rs.score_model(m, profile, answers) * 0.90
        top5 = rs.select_diverse_top5(passed, stretch, answers)
        out[name] = [m["full_name"] for m in top5]
        print(f"\n=== {name}")
        print("    profile:", {k: round(v, 2) for k, v in profile.items()})
        for m in top5:
            print(f"  * {m['full_name']:<34} {m['body_type']:<9} {m.get('price_year')} €{m['avg_price']:>6}"
                  f"  rel={m['avg_reliability']:.1f} score={m['_score']:.3f}"
                  f"{'  [crit]' if m.get('has_critical_issue') else ''}"
                  f"{'  [stretch]' if m.get('is_stretch') else ''}{'  [wild]' if m.get('is_wildcard') else ''}")
        if verbose:
            ranked = sorted(passed, key=lambda m: m["_score"], reverse=True)[:15]
            print("    -- ranked pool --")
            for m in ranked:
                v = m["vector"]
                print(f"    {m['full_name']:<34} {m['body_type']:<9} €{m['avg_price']:>6} sc={m['_score']:.3f}"
                      f" rel={m['avg_reliability']:.1f} st={v['status']:.2f} dr={v['driving']:.2f}"
                      f" pr={v['practical']:.2f} eco={v['economy']:.2f} cf={v['comfort']:.2f}")
    return out


if __name__ == "__main__":
    verbose = "-v" in sys.argv
    only = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    res = run(verbose, only)
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
