"""
What it costs to drive a car each month in Portugal — fuel or electricity.

One place for the energy prices the recommender and the analysis use. Update
the figures (and their dates) when prices move; every number carries its
source so a buyer can check it.
"""
from typing import Optional

# Prices with taxes, as a private buyer pays them.
PRICES = {
    "gasolina": {"eur": 1.887, "unit": "L", "as_of": "2026-11-16",
                 "source": "DGEG — preço médio diário, gasolina simples 95 (continente)",
                 "url": "https://precoscombustiveis.dgeg.gov.pt/estatistica/preco-medio-diario/"},
    "diesel":   {"eur": 2.078, "unit": "L", "as_of": "2026-11-16",
                 "source": "DGEG — preço médio diário, gasóleo simples (continente)",
                 "url": "https://precoscombustiveis.dgeg.gov.pt/estatistica/preco-medio-diario/"},
    "gpl":      {"eur": 1.032, "unit": "L", "as_of": "2026-11-16",
                 "source": "DGEG — preço médio diário, GPL Auto (continente)",
                 "url": "https://precoscombustiveis.dgeg.gov.pt/estatistica/preco-medio-diario/"},
    "eletrico_casa":    {"eur": 0.212, "unit": "kWh", "as_of": "2026-10",
                         "source": "Tarifa regulada simples (ERSE), com IEC e IVA",
                         "url": "https://www.voltaback.com/pt/blog/preco-kwh-carregamento-carro-eletrico/"},
    "eletrico_publico": {"eur": 0.37, "unit": "kWh", "as_of": "2026-10",
                         "source": "Mediana do preço ad hoc na rede MOBI.E (AC e DC), com IVA",
                         "url": "https://gotogreg.io/carregamento/"},
}

# An EV owner with a home or work charger does most charging there.
EV_HOME_SHARE = 0.8

# Monthly distance by the buyer's answer to "where do you drive most?"
KM_PER_MONTH = {"cidade": 800, "misto": 1200, "familia": 1200, "estrada": 2000}


def ev_blended_kwh_price() -> float:
    return (EV_HOME_SHARE * PRICES["eletrico_casa"]["eur"]
            + (1 - EV_HOME_SHARE) * PRICES["eletrico_publico"]["eur"])


def kwh_to_petrol_litres(kwh_per_100: float) -> float:
    """Petrol litres that cost the same as `kwh_per_100` of (blended) charging —
    lets the economy score compare an EV with a petrol car on money, not units."""
    return kwh_per_100 * ev_blended_kwh_price() / PRICES["gasolina"]["eur"]


def fuel_key(fuel: Optional[str]) -> Optional[str]:
    f = (fuel or "").lower()
    if f.startswith("elet") or f.startswith("elé") or f.startswith("elec"):
        return "eletrico"
    if "diesel" in f or "gasoleo" in f or "gasóleo" in f:
        return "diesel"
    if "gpl" in f:
        return "gpl"
    if f.startswith("h") or "hibrid" in f or "híbrid" in f:
        return "hibrido"
    if "gasolina" in f or "petrol" in f:
        return "gasolina"
    return None


def monthly_energy_cost(fuel: Optional[str], consumption: Optional[float], km_month: int,
                        plug_in: bool = False) -> Optional[dict]:
    """{eur_month, ...} for a car using `consumption` (L/100 km, or kWh/100 km
    for an EV) over `km_month`. None when the figure would be a guess: an
    unknown consumption, or a plug-in hybrid (its homologated litres assume
    charging habits we don't know)."""
    key = fuel_key(fuel)
    if not key or not consumption or consumption <= 0 or plug_in:
        return None
    if key == "eletrico":
        home = consumption * km_month / 100 * PRICES["eletrico_casa"]["eur"]
        public = consumption * km_month / 100 * PRICES["eletrico_publico"]["eur"]
        blended = consumption * km_month / 100 * ev_blended_kwh_price()
        return {"fuel": "eletrico", "consumption": round(consumption, 1), "unit": "kWh/100 km",
                "km_month": km_month, "eur_month": round(blended),
                "eur_month_home": round(home), "eur_month_public": round(public),
                "price_note": (f"{int(EV_HOME_SHARE * 100)}% em casa a {PRICES['eletrico_casa']['eur']:.3f} €/kWh, "
                               f"o resto na rede pública a {PRICES['eletrico_publico']['eur']:.2f} €/kWh"),
                "as_of": PRICES["eletrico_publico"]["as_of"]}
    price_key = "gasolina" if key == "hibrido" else key   # a full hybrid burns petrol
    p = PRICES[price_key]
    return {"fuel": key, "consumption": round(consumption, 1), "unit": "L/100 km", "km_month": km_month,
            "eur_month": round(consumption * km_month / 100 * p["eur"]),
            "price_note": f"{p['source'].split(' — ')[-1]} a {p['eur']:.3f} €/L ({p['as_of']})",
            "as_of": p["as_of"]}
