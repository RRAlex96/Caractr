"""
Comprehensive DB update — v2
Research-backed engine/generation-specific reliability corrections,
new EV models, BMW i4, Defender engine split, price corrections.

Run: python migrations/comprehensive_db_update_v2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

def model_id(brand_name, model_name):
    cur.execute("""
        SELECT vm.id FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        WHERE b.name = %s AND vm.name = %s LIMIT 1
    """, (brand_name, model_name))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Model not found: {brand_name} {model_name}")
    return row[0]

def brand_id(name):
    cur.execute("SELECT id FROM brands WHERE name=%s LIMIT 1", (name,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Brand not found: {name}")
    return row[0]

print("=== COMPREHENSIVE DB UPDATE v2 ===")

# ─────────────────────────────────────────────
# PART 1: ENGINE RELIABILITY CORRECTIONS
# Research-backed, per engine/generation
# ─────────────────────────────────────────────
print("\n[1/6] Applying engine reliability corrections...")

# --- PSA 1.2 PureTech (wet belt 2014-2022) ---
# ICE petrol engines: SEVERE reduction. Electric/diesel: moderate.
# Logic: only downgrade fuel_type IN ('gasolina') for PSA brands

psa_petrol_model_ids = []
for brand, model in [
    ('Peugeot','208'), ('Peugeot','2008'), ('Peugeot','308'), ('Peugeot','3008'),
    ('Peugeot','5008'), ('Peugeot','508'),
    ('Citroen','C3'), ('Citroen','C3 Aircross'), ('Citroen','C4'), ('Citroen','C5 Aircross'),
    ('DS','4'), ('Opel','Corsa'), ('Opel','Mokka'), ('Opel','Astra'), ('Opel','Grandland'),
]:
    try:
        psa_petrol_model_ids.append(model_id(brand, model))
    except ValueError:
        pass

# Petrol engines in PSA models: wet belt → reliability floor 5.5 for <130hp, 5.8 for 130+hp
# We use power_hp as a proxy: small 3-cyl PureTech (<140hp) gets the biggest hit
cur.execute("""
    UPDATE engines
    SET reliability_score = CASE
        WHEN power_hp < 140 THEN LEAST(reliability_score, 5.5)
        ELSE LEAST(reliability_score, 6.0)
    END
    WHERE model_id = ANY(%s)
      AND fuel_type = 'gasolina'
      AND reliability_score > 5.5
""", (psa_petrol_model_ids,))
print(f"  PSA petrol engines updated: {cur.rowcount} rows")

# PSA diesel (1.5/2.0 BlueHDi) — better than petrol but not perfect
cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 7.0)
    WHERE model_id = ANY(%s)
      AND fuel_type = 'diesel'
      AND reliability_score > 7.0
""", (psa_petrol_model_ids,))
print(f"  PSA diesel engines capped: {cur.rowcount} rows")

# PSA PHEV (e.g. 3008 PHEV) — hybrid electric component somewhat redeems it
# No change needed — already scored around 7.0

# PSA electric engines: RAISE — new chain platform (2023+), very reliable
# Peugeot 208 e (engine_id=6), 2008 e (engine_id=134): already at 7.5/8.0
# Ensure e-208, e-2008 are at 8.0
cur.execute("""
    UPDATE engines SET reliability_score = 8.0
    WHERE model_id IN (
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name='Peugeot' AND vm.name IN ('208','2008')
    ) AND fuel_type='eletrico' AND reliability_score < 8.0
""")

# DS 4: PSA platform + DS brand quality issues → harder hit
cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 4.8)
    WHERE model_id = (
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name='DS' AND vm.name='4' LIMIT 1
    ) AND fuel_type='gasolina'
""")
print(f"  DS 4 petrol penalised.")

# --- Renault 1.3 TCe (moderate issues, strict oil needed) ---
renault_tce_ids = []
for m in ['Clio','Captur','Megane','Kadjar','Arkana','Austral','Scenic']:
    try: renault_tce_ids.append(model_id('Renault', m))
    except ValueError: pass

# Petrol and GPL: reduce; Hybrid (E-Tech): smaller reduction
cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 6.5)
    WHERE model_id = ANY(%s)
      AND fuel_type IN ('gasolina','gpl')
      AND reliability_score > 6.5
""", (renault_tce_ids,))
print(f"  Renault TCe petrol/GPL capped: {cur.rowcount} rows")

cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 7.0)
    WHERE model_id = ANY(%s)
      AND fuel_type = 'hibrido'
      AND reliability_score > 7.0
""", (renault_tce_ids,))
# Kadjar gets extra penalty (ADAC worst performer + 1.6 dCi issues)
cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 6.0)
    WHERE model_id = (
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name='Renault' AND vm.name='Kadjar' LIMIT 1
    )
""")

# --- VW Golf Mk8 software debacle (What Car? last/22nd, infotainment) ---
# The engine is fine; the software is the problem. Score reflects ownership experience.
vw_golf_id = model_id('Volkswagen', 'Golf')
cur.execute("""
    UPDATE engines SET reliability_score = LEAST(reliability_score, 6.8)
    WHERE model_id = %s AND reliability_score > 6.8
""", (vw_golf_id,))
print(f"  VW Golf Mk8 capped.")

# Skoda Octavia (shares Golf 8 MQB platform/software, less affected)
skoda_oct_id = model_id('Skoda', 'Octavia')
cur.execute("""
    UPDATE engines SET reliability_score = LEAST(reliability_score, 7.0)
    WHERE model_id = %s AND reliability_score > 7.0
""", (skoda_oct_id,))

# VW Polo (DQ200 dry clutch concerns on DSG variants)
try:
    vw_polo_id = model_id('Volkswagen', 'Polo')
    cur.execute("""
        UPDATE engines SET reliability_score = LEAST(reliability_score, 7.0)
        WHERE model_id = %s AND reliability_score > 7.0
    """, (vw_polo_id,))
except: pass

# --- BMW N47 diesel no longer in DB (B47 from 2014). Slight general reduction for BMW diesels ---
# BMW Serie 3 diesel (B47): fine. BMW petrol (B58): actually raise to 7.5 for M340
cur.execute("""
    UPDATE engines SET reliability_score = 7.5
    WHERE model_id = (
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name='BMW' AND vm.name='Serie 3' LIMIT 1
    ) AND power_hp >= 250 AND fuel_type='gasolina'
      AND reliability_score < 7.5
""")  # B58 3.0T — excellent reliability

# BMW Serie 1 diesel: B47 decent, slight normalisation
cur.execute("""
    UPDATE engines SET reliability_score = LEAST(reliability_score, 7.0)
    WHERE model_id = (
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name='BMW' AND vm.name='Serie 1' LIMIT 1
    ) AND fuel_type='diesel'
""")

# --- Mercedes M274/M260 (timing chain, water pump, camshaft actuators) ---
# M274 in C-Class pre-2018, GLC. M260 in A-Class, CLA, GLA.
merc_models_m274 = []
for m in ['Classe C', 'GLC']:
    try: merc_models_m274.append(model_id('Mercedes-Benz', m))
    except: pass

cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 6.8)
    WHERE model_id = ANY(%s)
      AND fuel_type IN ('gasolina','hibrido')
      AND reliability_score > 6.8
""", (merc_models_m274,))

# M260 1.3 in A-Class, CLA, GLA (shared Renault engine + MBUX issues)
merc_models_m260 = []
for m in ['Classe A', 'CLA', 'GLA']:
    try: merc_models_m260.append(model_id('Mercedes-Benz', m))
    except: pass

cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 6.5)
    WHERE model_id = ANY(%s)
      AND fuel_type = 'gasolina'
      AND power_hp <= 225
      AND reliability_score > 6.5
""", (merc_models_m260,))
print(f"  Mercedes M274/M260 capped: {cur.rowcount} rows")

# --- Alfa Romeo Giulia 2.0T — electrical horrors ---
giulia_id = model_id('Alfa Romeo', 'Giulia')
cur.execute("""
    UPDATE engines
    SET reliability_score = CASE
        WHEN power_hp <= 280 THEN LEAST(reliability_score, 5.5)
        ELSE reliability_score  -- QV/Competizione: hand-built, better
    END
    WHERE model_id = %s
""", (giulia_id,))
print(f"  Alfa Romeo Giulia 2.0T capped.")

# --- Hyundai Ioniq 5 / Kia EV6 — ICCU failure (2-10% failure rate) ---
ioniq5_id = model_id('Hyundai', 'Ioniq 5')
ev6_id = model_id('Kia', 'EV6')
cur.execute("""
    UPDATE engines SET reliability_score = 6.5
    WHERE model_id IN (%s, %s) AND fuel_type='eletrico'
""", (ioniq5_id, ev6_id))
print(f"  Ioniq 5 / EV6 ICCU reliability corrected.")

# --- Ford 1.0 EcoBoost (head gasket 2012-2016, fixed 2017+) ---
ford_models = []
for m in ['Focus', 'Puma', 'Fiesta']:
    try: ford_models.append(model_id('Ford', m))
    except: pass

cur.execute("""
    UPDATE engines
    SET reliability_score = LEAST(reliability_score, 6.8)
    WHERE model_id = ANY(%s)
      AND fuel_type IN ('gasolina','hibrido')
      AND power_hp < 200
      AND reliability_score > 6.8
""", (ford_models,))

# Ford Kuga: ADAC poor performer
ford_kuga_id = model_id('Ford', 'Kuga')
cur.execute("""
    UPDATE engines SET reliability_score = LEAST(reliability_score, 6.5)
    WHERE model_id = %s AND reliability_score > 6.5
""", (ford_kuga_id,))
print(f"  Ford engines capped.")

# --- Nissan Qashqai / Juke (ADAC poor performers, 1.3 DiG-T = Renault 1.3 TCe) ---
for brand, model_name, cap in [('Nissan','Qashqai',6.5), ('Nissan','Juke',6.8)]:
    try:
        mid = model_id(brand, model_name)
        cur.execute("""
            UPDATE engines SET reliability_score = LEAST(reliability_score, %s)
            WHERE model_id = %s AND fuel_type IN ('gasolina','hibrido')
              AND reliability_score > %s
        """, (cap, mid, cap))
    except: pass
print(f"  Nissan Qashqai/Juke capped.")

# --- Volvo T8 PHEV on SPA platform (ERAD failures) ---
# V60, S60, XC60: mostly sold as PHEV in Portugal — ERAD is the problem
# XC40: CMA platform, ERAD less affected; BEV version solid
for volvo_model, cap in [('V60',6.5),('S60',6.5),('XC60',6.5),('XC40',7.2)]:
    try:
        mid = model_id('Volvo', volvo_model)
        cur.execute("""
            UPDATE engines SET reliability_score = LEAST(reliability_score, %s)
            WHERE model_id = %s AND fuel_type IN ('hibrido','gasolina')
              AND reliability_score > %s
        """, (cap, mid, cap))
    except: pass
# EX30 BEV: keep high — no known systematic issues
print(f"  Volvo PHEV/ICE capped; EX30 untouched.")

# --- Toyota: slight corrections based on ADAC data ---
# C-HR 2020: ADAC 51.5/1000 (abnormally high; mostly 12V battery + 2.0 hybrid early teething)
# Yaris: ADAC 27.8/1000 (still above average)
# These are still GOOD cars, just reduce from 9.0 slightly
for t_model, new_score in [('C-HR', 8.3), ('Yaris', 8.5), ('Yaris Cross', 8.8)]:
    try:
        mid = model_id('Toyota', t_model)
        cur.execute("""
            UPDATE engines SET reliability_score = LEAST(reliability_score, %s)
            WHERE model_id = %s AND reliability_score > %s
        """, (new_score, mid, new_score))
    except: pass
print(f"  Toyota slight corrections applied.")

print("  [DONE] Engine reliability corrections complete.")

# ─────────────────────────────────────────────
# PART 2: LAND ROVER DEFENDER — ENGINE SPLIT
# Ingenium diesel = 4.5 (catastrophic)
# P300/P400e/V8 = 7.5/8.0 (great car)
# ─────────────────────────────────────────────
print("\n[2/6] Land Rover Defender engine split...")

defender_id = model_id('Land Rover', 'Defender')
lrb_id = brand_id('Land Rover')

# Get current DC scores for Defender to copy to new model
cur.execute("SELECT comfort_score, driving_fun_score, city_score, highway_score, family_score FROM driving_character WHERE model_id=%s LIMIT 1", (defender_id,))
dc = cur.fetchone() or (7,7,5,7,8)

# Create new "Defender D200" model entry (Ingenium diesel only)
cur.execute("""
    INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced)
    VALUES (%s, 'Defender D200', 'suv', 'premium', '2020-present')
    RETURNING id
""", (lrb_id,))
d200_id = cur.fetchone()[0]

# driving_character for D200 — same physical scores, but driving_fun slightly lower (diesel)
cur.execute("""
    INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
    VALUES (%s, %s, %s, %s, %s, %s, 'Ingenium 2.0d diesel. Catastrophic failure risk: timing chain, turbo, oil dilution. Avoid unless recall history verified.')
""", (d200_id, dc[0], dc[1]-1, dc[2], dc[3], dc[4]))

# Update the diesel engine to reference D200 model
cur.execute("""
    UPDATE engines SET model_id=%s, reliability_score=4.5
    WHERE model_id=%s AND fuel_type='diesel'
""", (d200_id, defender_id))
diesel_moved = cur.rowcount
print(f"  Moved {diesel_moved} diesel engine(s) to Defender D200.")

# Market price stats for D200 (diesel = cheaper)
cur.execute("""
    INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
    VALUES (%s, 'used_pt', 2024, 48000, 38000, 60000, 'standvirtual_2024')
""", (d200_id,))

# Now fix remaining Defender engines (P300 petrol, P400e PHEV) — the GOOD versions
# P300 petrol (~300hp gasoline): 7.5
cur.execute("""
    UPDATE engines SET reliability_score=7.5
    WHERE model_id=%s AND fuel_type='gasolina'
""", (defender_id,))
# P400e PHEV: Land Rover's best drivetrain, electric-assisted. 8.0
cur.execute("""
    UPDATE engines SET reliability_score=8.0
    WHERE model_id=%s AND fuel_type='hibrido'
""", (defender_id,))

# Update original Defender DC description
cur.execute("""
    UPDATE driving_character SET description='P300/P400e/V8 versions. Exceptional off-road, elevated highway comfort, impressive performance. Avoid D200 diesel (separate listing).'
    WHERE model_id=%s
""", (defender_id,))

print(f"  Defender P300/P400e reliability corrected. D200 split done.")

# ─────────────────────────────────────────────
# PART 3: DRIVING CHARACTER CORRECTIONS
# ─────────────────────────────────────────────
print("\n[3/6] Driving character corrections...")

# Mazda 2 family_score: 4 → 2 (no rear space, 2-door feel, fails espaco aversion)
mazda2_id = model_id('Mazda', '2')
cur.execute("UPDATE driving_character SET family_score=2 WHERE model_id=%s", (mazda2_id,))
print(f"  Mazda 2 family_score → 2")

# Alfa Romeo Giulia driving_fun: already 10. family_score: increase to 4 (it's a proper berlina)
# No change needed there.

# Hyundai Ioniq 5 driving_character: it's a solid car, just ICCU issue. Scores fine.
# Lower city_score slightly for Ioniq 5 (it's large for a city)
cur.execute("""
    UPDATE driving_character SET city_score=6
    WHERE model_id=%s AND city_score > 6
""", (ioniq5_id,))

print(f"  [DONE] Driving character corrections.")

# ─────────────────────────────────────────────
# PART 4: PRICE CORRECTIONS
# ─────────────────────────────────────────────
print("\n[4/6] Price corrections...")

price_fixes = [
    # (brand, model, new_avg, new_min, new_max)
    ('Mazda',         '2',          16500, 12000, 21000),
    ('Honda',         'Jazz',       16000, 12000, 20000),
    ('Mercedes-Benz', 'Classe A',   30000, 22000, 38000),
    ('Alfa Romeo',    'Giulia',     31000, 24000, 40000),
    ('Land Rover',    'Defender',   58000, 46000, 72000),
    ('BMW',           'Serie 3',    35000, 27000, 44000),
    ('Volvo',         'V60',        36000, 28000, 44000),
    ('Volvo',         'XC60',       40000, 32000, 50000),
]

for brand_name, model_name, avg, mn, mx in price_fixes:
    try:
        mid = model_id(brand_name, model_name)
        cur.execute("""
            UPDATE market_price_stats SET avg_price=%s, min_price=%s, max_price=%s
            WHERE model_id=%s
        """, (avg, mn, mx, mid))
        print(f"  {brand_name} {model_name}: avg={avg}")
    except ValueError:
        print(f"  WARN: {brand_name} {model_name} not found")

print(f"  [DONE] Price corrections.")

# ─────────────────────────────────────────────
# PART 5: NEW MODELS
# ─────────────────────────────────────────────
print("\n[5/6] Inserting new models...")

def insert_full_model(brand_name, name, body_type, segment, years,
                      comfort, driving_fun, city, highway, family, description,
                      engines_list,   # list of (fuel_type, hp, torque, transmission, consumption, co2, reliability, maint)
                      avg_price, min_price, max_price):
    """Insert a complete model: vehicle_models + driving_character + engines + market_price_stats"""
    b_id = brand_id(brand_name)
    # Check if already exists
    cur.execute("""
        SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
        WHERE b.name=%s AND vm.name=%s LIMIT 1
    """, (brand_name, name))
    existing = cur.fetchone()
    if existing:
        mid = existing[0]
        print(f"  SKIP (exists): {brand_name} {name} (id={mid})")
        return mid

    cur.execute("""
        INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced)
        VALUES (%s,%s,%s,%s,%s) RETURNING id
    """, (b_id, name, body_type, segment, years))
    mid = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO driving_character
          (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (mid, comfort, driving_fun, city, highway, family, description))

    for (fuel_type, hp, torque, transmission, consumption, co2, reliability, maint) in engines_list:
        cur.execute("""
            INSERT INTO engines
              (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (mid, fuel_type, hp, torque, transmission, consumption, co2, reliability, maint))

    cur.execute("""
        INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
        VALUES (%s,'used_pt',2024,%s,%s,%s,'research_2024')
    """, (mid, avg_price, min_price, max_price))

    print(f"  + Inserted: {brand_name} {name} (id={mid})")
    return mid

# ── BMW i4 ──────────────────────────────────
insert_full_model(
    'BMW', 'i4', 'berlina', 'premium', '2021-present',
    comfort=8, driving_fun=9, city=6, highway=9, family=5,
    description='Gran Coupe EV. BMW dynamics preserved electrically — praised over Tesla M3 for driving feel. 590km WLTP range. Large for city parking.',
    engines_list=[
        ('eletrico', 340, 430, 'automatico', 15.5, 0, 7.5, 1200),  # eDrive40
        ('eletrico', 544, 795, 'automatico', 18.5, 0, 7.0, 1400),  # M50 xDrive
    ],
    avg_price=52000, min_price=37000, max_price=65000
)

# ── Dacia Spring ─────────────────────────────
insert_full_model(
    'Dacia', 'Spring', 'citadino', 'economico', '2021-present',
    comfort=4, driving_fun=3, city=9, highway=3,  family=3,
    description='Cheapest EV in Portugal. Ultra-urban: 230km range, tiny, very affordable. Not for highway use. Simple, reliable platform.',
    engines_list=[
        ('eletrico', 65,  113, 'automatico', 14.5, 0, 8.5, 400),
        ('eletrico', 83,  113, 'automatico', 14.5, 0, 8.5, 400),
    ],
    avg_price=14000, min_price=10000, max_price=18500
)

# ── Renault Zoe ──────────────────────────────
insert_full_model(
    'Renault', 'Zoe', 'citadino', 'medio', '2012-2023',
    comfort=6, driving_fun=5, city=8, highway=5, family=4,
    description='Veteran EV — proven reliability in Portuguese market. 390km WLTP. Discontinued new but abundant used. Ideal city EV under €20k.',
    engines_list=[
        ('eletrico', 108, 245, 'automatico', 17.2, 0, 8.0, 500),
        ('eletrico', 135, 245, 'automatico', 17.2, 0, 8.2, 500),
    ],
    avg_price=17000, min_price=12000, max_price=22000
)

# ── Renault Megane E-Tech Electric ───────────
insert_full_model(
    'Renault', 'Megane E-Tech Electric', 'compacto', 'medio', '2022-present',
    comfort=8, driving_fun=6, city=8, highway=7, family=6,
    description='Landmark EV design. 450km range. Supple ride, great tech. New platform, no legacy ICE issues. Strong Portugal sales.',
    engines_list=[
        ('eletrico', 130, 250, 'automatico', 16.5, 0, 8.0, 600),
        ('eletrico', 218, 300, 'automatico', 16.5, 0, 8.0, 600),
    ],
    avg_price=29000, min_price=24000, max_price=36000
)

# ── CUPRA Born ───────────────────────────────
insert_full_model(
    'Cupra', 'Born', 'compacto', 'premium', '2021-present',
    comfort=7, driving_fun=8, city=7, highway=8, family=5,
    description='MEB platform EV. Sharp handling, 420km range, distinctive design. VW Group reliability with sporty character. Strong Portugal visibility.',
    engines_list=[
        ('eletrico', 170, 310, 'automatico', 16.5, 0, 7.8, 700),
        ('eletrico', 231, 310, 'automatico', 16.5, 0, 7.8, 700),
    ],
    avg_price=31000, min_price=25000, max_price=40000
)

# ── VW ID.4 ──────────────────────────────────
insert_full_model(
    'Volkswagen', 'ID.4', 'suv', 'medio', '2021-present',
    comfort=8, driving_fun=5, city=7, highway=8, family=7,
    description='MEB platform C-SUV EV. 500km range. Practical, comfortable, VW quality. Less exciting than CUPRA Born but more family-friendly. ADAC: VW ID.7 won "very good" 2024.',
    engines_list=[
        ('eletrico', 170, 310, 'automatico', 16.0, 0, 8.0, 700),
        ('eletrico', 204, 310, 'automatico', 16.0, 0, 8.0, 700),
        ('eletrico', 299, 460, 'automatico', 17.0, 0, 7.8, 800),  # GTX AWD
    ],
    avg_price=40000, min_price=32000, max_price=52000
)

# ── Skoda Enyaq iV ───────────────────────────
insert_full_model(
    'Skoda', 'Enyaq iV', 'suv', 'medio', '2021-present',
    comfort=8, driving_fun=5, city=7, highway=8, family=8,
    description='MEB platform. Best value EV SUV in its class. 510km range, huge boot (585L), sensible pricing. Practical family EV SUV.',
    engines_list=[
        ('eletrico', 150, 310, 'automatico', 15.5, 0, 8.0, 650),
        ('eletrico', 204, 310, 'automatico', 15.5, 0, 8.0, 650),
        ('eletrico', 265, 425, 'automatico', 17.0, 0, 7.8, 750),  # vRS
    ],
    avg_price=36000, min_price=29000, max_price=46000
)

# ── Hyundai Ioniq 6 ──────────────────────────
# model_id=174 already exists but has NULL data — populate it
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Hyundai' AND vm.name='Ioniq 6' LIMIT 1
""")
ioniq6_row = cur.fetchone()
if ioniq6_row:
    i6_id = ioniq6_row[0]
    # Check if driving_character exists
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (i6_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,8,7,7,9,5,'Aerodynamic berlina EV (0.21 Cd). 614km WLTP range. Sleek, efficient, excellent highway. Same ICCU issue as Ioniq 5 (recall required). Limited rear headroom.')
        """, (i6_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (i6_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'eletrico',229,350,'automatico',14.3,6.5,800),
              (%s,'eletrico',325,605,'automatico',14.3,6.5,900)
        """, (i6_id, i6_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (i6_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,40000,33000,50000,'research_2024')
        """, (i6_id,))
    print(f"  Populated Hyundai Ioniq 6 (id={i6_id})")

# ── BYD Atto 3 ───────────────────────────────
# model_id=162 exists but NULL
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='BYD' AND vm.name='Atto 3' LIMIT 1
""")
atto3_row = cur.fetchone()
if atto3_row:
    atto3_id = atto3_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (atto3_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,5,7,7,7,'BYD Blade battery. Competitive C-SUV EV. 420km range. Good value, improving quality. BYD +593%% growth in Portugal 2024.')
        """, (atto3_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (atto3_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES (%s,'eletrico',204,310,'automatico',16.5,7.5,600)
        """, (atto3_id,))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (atto3_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,30000,24000,38000,'research_2024')
        """, (atto3_id,))
    print(f"  Populated BYD Atto 3 (id={atto3_id})")

# ── Renault 5 E-Tech ─────────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Renault' AND vm.name='5 E-Tech' LIMIT 1
""")
r5_row = cur.fetchone()
if r5_row:
    r5_id = r5_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (r5_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,6,7,9,5,3,'Retro-modern EV citadino. 400km range. Fun urban car, Renault native EV platform. Huge Portugal buzz — affordable, stylish, practical for city.')
        """, (r5_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (r5_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'eletrico',120,225,'automatico',15.0,8.0,500),
              (%s,'eletrico',150,245,'automatico',15.0,8.0,500)
        """, (r5_id, r5_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (r5_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,20000,16000,26000,'research_2024')
        """, (r5_id,))
    print(f"  Populated Renault 5 E-Tech (id={r5_id})")

# ── Citroën ë-C3 (2024 new model — genuinely different from old C3) ──
insert_full_model(
    'Citroen', 'e-C3', 'citadino', 'economico', '2024-present',
    comfort=7, driving_fun=4, city=9, highway=5, family=5,
    description='New 2024 EV from €22k. Smart platform (not PureTech). 320km range. Disrupts budget EV segment. Hydro-formed suspension = surprisingly comfortable. Different from old C3.',
    engines_list=[
        ('eletrico', 113, 120, 'automatico', 15.0, 0, 8.5, 450),
    ],
    avg_price=20000, min_price=16000, max_price=26000
)

# ── Mercedes EQA ─────────────────────────────
insert_full_model(
    'Mercedes-Benz', 'EQA', 'suv', 'premium', '2021-present',
    comfort=8, driving_fun=5, city=7, highway=7, family=6,
    description='Premium compact EV SUV. 426km range. GLA-based so familiar packaging. Less dynamic than BMW iX1 but more luxurious feel. Mercedes #5 EV brand in Portugal 2024.',
    engines_list=[
        ('eletrico', 190, 385, 'automatico', 17.2, 0, 7.3, 900),
        ('eletrico', 292, 520, 'automatico', 18.5, 0, 7.3, 1000),  # AMG
    ],
    avg_price=40000, min_price=33000, max_price=50000
)

# ── BMW 2 Series Active Tourer (premium MPV, #1 Portuguese corporate fleet) ──
# Already exists as model_id=160 but NULL — populate
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='BMW' AND vm.name='Serie 2 Active Tourer' LIMIT 1
""")
at_row = cur.fetchone()
if at_row:
    at_id = at_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (at_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,8,6,8,8,9,'Premium MPV. #1 corporate fleet car in Portugal (xDrive25e PHEV). 5 proper seats, tall roof, sliding rear. BMW dynamics in practical packaging. Ideal empresa.')
        """, (at_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (at_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'gasolina',136,220,'automatico',6.5,7.2,900),
              (%s,'gasolina',170,280,'automatico',6.8,7.2,950),
              (%s,'hibrido',218,385,'automatico',1.9,7.5,1000),   -- xDrive25e PHEV
              (%s,'eletrico',218,400,'automatico',16.0,7.8,800)   -- 230e / Active Tourer EV
        """, (at_id, at_id, at_id, at_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (at_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,32000,25000,42000,'research_2024')
        """, (at_id,))
    print(f"  Populated BMW 2 Series Active Tourer (id={at_id})")

# ── Polestar 2 ───────────────────────────────
# Need to add Polestar brand first
cur.execute("SELECT id FROM brands WHERE name='Polestar' LIMIT 1")
ps_brand = cur.fetchone()
if not ps_brand:
    cur.execute("INSERT INTO brands (name) VALUES ('Polestar') RETURNING id")
    ps_brand_id = cur.fetchone()[0]
    print(f"  + Added brand: Polestar (id={ps_brand_id})")
else:
    ps_brand_id = ps_brand[0]

cur.execute("""
    SELECT vm.id FROM vehicle_models vm
    WHERE vm.brand_id=%s AND vm.name='2' LIMIT 1
""", (ps_brand_id,))
if not cur.fetchone():
    cur.execute("""
        INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced)
        VALUES (%s,'2','berlina','premium','2020-present') RETURNING id
    """, (ps_brand_id,))
    p2_id = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
        VALUES (%s,7,8,7,9,5,'Fastback EV sedan. Volvo/Geely platform. 540km range. Excellent highway GT, sporty character. Good build quality. One-pedal driving. Alternative to Tesla M3 for brand-conscious buyers.')
    """, (p2_id,))
    cur.execute("""
        INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
        VALUES
          (%s,'eletrico',231,490,'automatico',16.5,7.8,800),
          (%s,'eletrico',295,490,'automatico',16.5,7.8,850)
    """, (p2_id, p2_id))
    cur.execute("""
        INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
        VALUES (%s,'used_pt',2024,38000,30000,50000,'research_2024')
    """, (p2_id,))
    print(f"  + Inserted: Polestar 2 (id={p2_id})")

# ── Range Rover Evoque (premium small SUV — popular in PT) ──
# model_id=126 exists but NULL — populate
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Land Rover' AND vm.name='Range Rover Evoque' LIMIT 1
""")
evoque_row = cur.fetchone()
if evoque_row:
    evoque_id = evoque_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (evoque_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,8,6,6,7,5,'Premium compact SUV. L551 (2019+): Ingenium 2.0d diesel AVOID (timing chain catastrophe). P200/P250 petrol: decent. P300e PHEV: best option. Style over substance but status is undeniable.')
        """, (evoque_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (evoque_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'gasolina',200,320,'automatico',8.5,6.5,1400),   -- P200 Ingenium petrol (moderate)
              (%s,'gasolina',250,365,'automatico',9.0,6.5,1500),   -- P250
              (%s,'hibrido',309,540,'automatico',2.0,7.5,1600),    -- P300e PHEV (best option)
              (%s,'diesel',163,380,'automatico',6.5,4.5,2000)      -- D165 Ingenium diesel (catastrophic risk)
        """, (evoque_id, evoque_id, evoque_id, evoque_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (evoque_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,35000,26000,50000,'research_2024')
        """, (evoque_id,))
    print(f"  Populated Range Rover Evoque (id={evoque_id})")

# ── Alfa Romeo Stelvio (SUV counterpart to Giulia) ──
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Alfa Romeo' AND vm.name='Stelvio' LIMIT 1
""")
stelvio_row = cur.fetchone()
if stelvio_row:
    stelvio_id = stelvio_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (stelvio_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,9,5,8,6,'Best-driving SUV in its class. 2.0T petrol same electrical issues as Giulia. Emotional choice — head-turning, engaging, Italian. Water ingress recall (2019). Buy with extended warranty.')
        """, (stelvio_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (stelvio_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'gasolina',200,330,'automatico',8.8,5.5,1600),
              (%s,'gasolina',280,400,'automatico',9.5,5.8,1800),
              (%s,'gasolina',510,600,'automatico',11.5,5.5,2500)   -- Quadrifoglio
        """, (stelvio_id, stelvio_id, stelvio_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (stelvio_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,34000,26000,46000,'research_2024')
        """, (stelvio_id,))
    print(f"  Populated Alfa Romeo Stelvio (id={stelvio_id})")

# ── Jeep Compass ──────────────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Jeep' AND vm.name='Compass' LIMIT 1
""")
compass_row = cur.fetchone()
if compass_row:
    compass_id = compass_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (compass_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,5,6,7,7,'Practical C-SUV. 4xe PHEV popular in Portugal fleet market. Good space, decent quality. 1.3 T4 petrol (MultiAir): moderate reliability. 4xe PHEV adds off-road credibility.')
        """, (compass_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (compass_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'gasolina',130,270,'automatico',7.5,6.5,1100),
              (%s,'gasolina',150,270,'automatico',7.8,6.5,1100),
              (%s,'hibrido',240,400,'automatico',2.0,7.0,1300)    -- 4xe PHEV
        """, (compass_id, compass_id, compass_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (compass_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,25000,19000,36000,'research_2024')
        """, (compass_id,))
    print(f"  Populated Jeep Compass (id={compass_id})")

# ── Jeep Avenger ──────────────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Jeep' AND vm.name='Avenger' LIMIT 1
""")
avenger_row = cur.fetchone()
if avenger_row:
    av_id = avenger_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (av_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,5,8,6,5,'Stellantis e-CMP platform. European Car of the Year 2023. EV version recommended — new chain platform avoids PureTech issues. Compact, city-friendly, Jeep styling.')
        """, (av_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (av_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'eletrico',156,260,'automatico',16.5,8.5,500),   -- EV (new chain platform = reliable)
              (%s,'gasolina',100,190,'manual',6.0,5.5,900),        -- 1.2 PureTech (avoid)
              (%s,'hibrido',136,250,'automatico',5.5,6.5,1000)     -- mild hybrid
        """, (av_id, av_id, av_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (av_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,24000,19000,30000,'research_2024')
        """, (av_id,))
    print(f"  Populated Jeep Avenger (id={av_id})")

# ── Smart #1 ──────────────────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Smart' AND vm.name='#1' LIMIT 1
""")
smart1_row = cur.fetchone()
if smart1_row:
    s1_id = smart1_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (s1_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,6,7,7,5,'Smart/Mercedes-Benz/Geely joint EV. 440km range. Compact premium SUV. Good build quality. Growing Portugal presence.')
        """, (s1_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (s1_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES (%s,'eletrico',272,343,'automatico',17.5,7.5,700)
        """, (s1_id,))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (s1_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,32000,26000,40000,'research_2024')
        """, (s1_id,))
    print(f"  Populated Smart #1 (id={s1_id})")

# ── MG ZS EV ──────────────────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='MG' AND vm.name='ZS EV' LIMIT 1
""")
mgzs_row = cur.fetchone()
if mgzs_row:
    mgzs_id = mgzs_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (mgzs_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,7,4,8,6,6,'Budget EV SUV from SAIC/MG. 440km range (long range). Best value EV SUV per km of range. Quality improving but not at VW level. Good city and family use.')
        """, (mgzs_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (mgzs_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'eletrico',143,280,'automatico',17.0,7.3,550),
              (%s,'eletrico',176,280,'automatico',17.0,7.3,600)
        """, (mgzs_id, mgzs_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (mgzs_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,24000,18000,32000,'research_2024')
        """, (mgzs_id,))
    print(f"  Populated MG ZS EV (id={mgzs_id})")

# ── Skoda Superb Combi (already in DB id=107 with engine) ──
# Populate driving_character if missing
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Skoda' AND vm.name='Superb Combi' LIMIT 1
""")
scombi_row = cur.fetchone()
if scombi_row:
    scombi_id = scombi_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (scombi_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,9,5,5,9,10,'Best value family carrinha on the market. 660L boot. VW Group quality at Skoda price. Premium feel, practical. Ideal estrada+familia.')
        """, (scombi_id,))
        print(f"  Populated Skoda Superb Combi DC (id={scombi_id})")

# ── Peugeot E-308 (already model_id=50, NULL) ──
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Peugeot' AND vm.name='E-308' LIMIT 1
""")
e308_row = cur.fetchone()
if e308_row:
    e308_id = e308_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (e308_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,8,6,7,7,6,'Electric 308. 410km range. i-Cockpit interior. Good EV on new chain platform (no wet belt). Peugeot quality up. Available as SW (estate) too.')
        """, (e308_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (e308_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES (%s,'eletrico',156,260,'automatico',16.0,8.0,600)
        """, (e308_id,))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (e308_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,30000,25000,38000,'research_2024')
        """, (e308_id,))
    print(f"  Populated Peugeot E-308 (id={e308_id})")

# ── BYD Seal (berlina EV) ──────────────────────
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='BYD' AND vm.name='Seal' LIMIT 1
""")
seal_row = cur.fetchone()
if seal_row:
    seal_id = seal_row[0]
    cur.execute("SELECT id FROM driving_character WHERE model_id=%s LIMIT 1", (seal_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO driving_character
              (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, description)
            VALUES (%s,8,7,7,8,5,'BYD Blade battery berlina. Tesla M3 competitor. 570km range, AWD available. Growing Portuguese presence. Better interior than expected. Competitive pricing.')
        """, (seal_id,))
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (seal_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'eletrico',313,360,'automatico',15.5,7.5,650),
              (%s,'eletrico',523,670,'automatico',16.0,7.5,750)
        """, (seal_id, seal_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (seal_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,36000,29000,46000,'research_2024')
        """, (seal_id,))
    print(f"  Populated BYD Seal (id={seal_id})")

print("\n[5/6] New models complete.")

# ─────────────────────────────────────────────
# PART 6: POPULATE REMAINING NULL VOLVO MODELS
# ─────────────────────────────────────────────
print("\n[6/6] Populate remaining NULL-data Volvo/other models...")

# Hyundai Kona electric already has engine 189.
# Ensure driving_character has correct scores for EV suitability.
# (already in DB with full data)

# Populate Volvo S60 if has no engines
cur.execute("""
    SELECT vm.id FROM vehicle_models vm JOIN brands b ON b.id=vm.brand_id
    WHERE b.name='Volvo' AND vm.name='S60' LIMIT 1
""")
s60_row = cur.fetchone()
if s60_row:
    s60_id = s60_row[0]
    cur.execute("SELECT id FROM engines WHERE model_id=%s LIMIT 1", (s60_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO engines (model_id, fuel_type, power_hp, torque_nm, transmission, consumption_mixed, reliability_score, maintenance_cost_year)
            VALUES
              (%s,'gasolina',190,320,'automatico',7.8,6.8,1200),
              (%s,'hibrido',250,350,'automatico',1.8,6.5,1400),
              (%s,'hibrido',390,500,'automatico',1.6,6.5,1600)    -- T8 PHEV (ERAD risk)
        """, (s60_id, s60_id, s60_id))
    cur.execute("SELECT id FROM market_price_stats WHERE model_id=%s LIMIT 1", (s60_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO market_price_stats (model_id, price_context, year, avg_price, min_price, max_price, source)
            VALUES (%s,'used_pt',2024,32000,26000,39000,'research_2024')
        """, (s60_id,))
    print(f"  Populated Volvo S60 engines (id={s60_id})")

# ── COMMIT ───────────────────────────────────
conn.commit()
print("\n✅ ALL CHANGES COMMITTED SUCCESSFULLY.")

# ── VERIFICATION ─────────────────────────────
print("\n=== VERIFICATION ===")
cur.execute("""
    SELECT COUNT(DISTINCT vm.id) FROM vehicle_models vm
    JOIN brands b ON b.id=vm.brand_id
    JOIN engines e ON e.model_id=vm.id
""")
row = cur.fetchone()
print(f"  Models with engines: {row[0] if row else 0}")

cur.execute("SELECT COUNT(*) FROM vehicle_models")
print(f"  Total models: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM engines")
print(f"  Total engines: {cur.fetchone()[0]}")

# Spot-check key reliability scores
checks = [
    ('Peugeot','208'),
    ('Citroen','C3'),
    ('DS','4'),
    ('Hyundai','Ioniq 5'),
    ('Kia','EV6'),
    ('Land Rover','Defender'),
    ('Alfa Romeo','Giulia'),
    ('Volvo','V60'),
    ('BMW','i4'),
    ('Dacia','Spring'),
    ('Renault','Megane E-Tech Electric'),
    ('CUPRA','Born'),
    ('Volkswagen','ID.4'),
]
print("\n  Key reliability spot-check:")
for brand_n, model_n in checks:
    cur.execute("""
        SELECT ROUND(AVG(e.reliability_score)::numeric,2), COUNT(e.id)
        FROM vehicle_models vm
        JOIN brands b ON b.id=vm.brand_id
        LEFT JOIN engines e ON e.model_id=vm.id
        WHERE b.name=%s AND vm.name=%s
    """, (brand_n, model_n))
    result = cur.fetchone()
    avg_rel = result[0] if result else 'N/A'
    eng_count = result[1] if result else 0
    print(f"    {brand_n:20} {model_n:30} → avg_reliability={avg_rel} ({eng_count} engines)")

conn.close()
print("\n=== DONE ===")
