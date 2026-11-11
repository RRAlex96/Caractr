"""
Review aid for the curated engine-issue list (seeds/known_engine_issues.json).

    # from backend/
    python -m scripts.review_engine_issues            # validate + match + write review doc
    python -m scripts.review_engine_issues --no-db    # validate only

1. Validates every entry (schema, sources, the "critico needs an official or
   press source" rule).
2. Dry-runs the matcher against the catalogue (read-only): which catalogue
   engines each entry would flag, and through which generations.
3. Writes docs/engine-issues-review.md — one section per entry with the
   evidence, so a human can approve, edit or reject it. Approve by setting
   "status": "approved" in the JSON. Nothing reaches users until then.
"""
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.known_issues import (  # noqa: E402
    SEED_PATH, load_issues, matches_engine, validate, years_overlap,
)

DOC = Path(__file__).resolve().parents[2] / "docs" / "engine-issues-review.md"

_SEV = {"critico": "🔴 crítico (alerta vermelho)", "alto": "🟠 alto (lista de verificação)"}
_KIND = {"official": "oficial", "press": "imprensa", "trade": "técnica/oficina", "forum": "fórum"}


def _catalog(db):
    from sqlalchemy import text
    engines = db.execute(text("""
        SELECT e.id, b.name AS brand, vm.name AS model, e.code AS label, e.fuel_type,
               e.displacement_cc, e.transmission, e.torque_nm, vm.id AS model_id
        FROM engines e
        JOIN vehicle_models vm ON vm.id = e.model_id
        JOIN brands b ON b.id = vm.brand_id
    """)).mappings().fetchall()
    gens = defaultdict(list)
    for g in db.execute(text("SELECT model_id, name, year_start, year_end FROM generations")).mappings():
        gens[g["model_id"]].append(g)
    return engines, gens


def _matches(issue, engines, gens):
    hits = []
    for e in engines:
        if not matches_engine(issue, brand=e["brand"], model=e["model"], label=e["label"],
                              fuel=e["fuel_type"], displacement_cc=e["displacement_cc"],
                              transmission=e["transmission"], torque_nm=e["torque_nm"]):
            continue
        overlapping = [g for g in gens[e["model_id"]] if years_overlap(issue, g["year_start"], g["year_end"])]
        hits.append((e, overlapping))
    return hits


def _eur(r):
    return "—" if not r else f"{r[0]:,}–{r[1]:,} €".replace(",", ".")


def _section(issue, errs, hits) -> str:
    lo, hi = issue["years"]
    out = [f"## {issue['name']}", ""]
    out.append(f"`{issue['id']}` · {_SEV[issue['severity']]} · confiança {issue['confidence']} · "
               f"{issue['component']} · **{lo}–{hi}** · estado: **{issue['status']}**")
    out.append("")
    if errs:
        out += [f"> ⚠ **Validação:** {'; '.join(errs)}", ""]
    out += [f"**{issue['problem']}**", "", issue["detail"], ""]
    out += [f"**Antes de comprar:** {issue['check']}", ""]
    cost = issue["cost_eur"]
    out.append(f"**Custo estimado:** preventivo {_eur(cost.get('preventive'))} · se falhar {_eur(cost.get('failure'))}")
    if issue.get("mitigation"):
        out += ["", f"**Garantias / peças revistas:** {issue['mitigation']}"]
    if issue.get("models"):
        out += ["", "**Modelos:** " + "; ".join(issue["models"])]
    out += ["", "**Fontes:**"]
    out += [f"- [{s['label']}]({s['url']}) — {_KIND[s['kind']]}" for s in issue["sources"]]
    if issue.get("review_notes"):
        out += ["", f"> **Para rever:** {issue['review_notes']}"]
    out += ["", "**Motores do catálogo com esta motorização** (o catálogo não guarda anos por motor "
            "— numa análise de anúncio decide o ano do carro):"]
    if hits is None:
        out.append("- (não verificado — sem base de dados)")
    elif not hits:
        out.append("- nenhum (aplica-se só a anúncios de carros mais antigos)")
    else:
        out.append("- " + "; ".join(f"{e['brand']} {e['model']} {e['label']}" for e, _ in hits))
    out += ["", "---", ""]
    return "\n".join(out)


def main(argv):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    issues = load_issues(SEED_PATH, include_drafts=True)
    all_errs = {i["id"]: validate(i) for i in issues}
    ids = [i["id"] for i in issues]
    dupes = {x for x in ids if ids.count(x) > 1}

    engines = gens = None
    if "--no-db" not in argv and os.getenv("DATABASE_URL"):
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            engines, gens = _catalog(db)
        finally:
            db.close()

    by_sev = defaultdict(int)
    flagged_engines = 0
    sections = []
    for i in sorted(issues, key=lambda x: (x["severity"] != "critico", x["name"])):
        by_sev[i["severity"]] += 1
        hits = _matches(i, engines, gens) if engines is not None else None
        flagged_engines += len(hits or [])
        sections.append(_section(i, all_errs[i["id"]], hits))

    invalid = {k: v for k, v in all_errs.items() if v}
    header = [
        "# Falhas conhecidas por motor — revisão",
        "",
        "Lista curada de problemas crónicos e caros de motores e caixas específicos. "
        "**Rascunho:** nada disto chega aos utilizadores até a entrada ter `\"status\": \"approved\"` "
        "em `backend/seeds/known_engine_issues.json`.",
        "",
        f"- {len(issues)} entradas · {by_sev['critico']} crítico · {by_sev['alto']} alto",
        f"- Regra: **crítico** (alerta vermelho) exige pelo menos uma fonte oficial ou de imprensa; "
        f"o resto fica em **alto** (lista de verificação, sem vermelho).",
        f"- Custos são estimativas Caractr para Portugal (oficina independente) — intervalos, não orçamentos.",
        f"- Motores do catálogo com uma motorização desta lista: "
        + (str(flagged_engines) if engines is not None else "não verificado")
        + " — o catálogo não tem anos por motor, por isso a ligação final faz-se pelo ano do anúncio.",
        f"- Erros de validação: {len(invalid)}" + (f" ({', '.join(invalid)})" if invalid else ""),
        "",
        "Gerado por `python -m scripts.review_engine_issues`.",
        "",
        "---",
        "",
    ]
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(header) + "\n".join(sections), encoding="utf-8")

    print(f"{len(issues)} entries ({by_sev['critico']} critico, {by_sev['alto']} alto)")
    if dupes:
        print("DUPLICATE ids:", sorted(dupes))
    for k, v in invalid.items():
        print(f"INVALID {k}: {'; '.join(v)}")
    if engines is not None:
        print(f"catalogue engines sharing a listed engine family: {flagged_engines}")
    print(f"review doc: {DOC}")
    return 1 if (invalid or dupes) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
