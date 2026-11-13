-- Migration v6.1 — engines and driving character for the models that had none
--
-- 70 of the catalogue's 201 models had no engine row, and the recommender only
-- considers models with at least one: BMW Série 5, Mercedes Classe E, Audi A6,
-- BMW X5, Volvo XC90, VW Touran ... were never recommended. Those models hold
-- about 18% of the listings of catalogue models.
--
-- Built once from the Standvirtual market snapshot of 2026-11-13
-- (scripts/market_snapshot.py): the listings of each model were grouped by
-- fuel, engine size and power, and the most-listed groups became rows. This
-- file is the record from here on. 216 engines for 79 models
-- (the 70 with none, and those with a single one). Each row is an engine
-- variant actually on sale:
--
--   fuel, displacement, power, gearbox, years   measured: the listings of that variant
--                                               (listings_seen says how many)
--   CO2, consumption                            measured where listing pages state the
--                                               car's CO2 (consumption = CO2 / 23.2 for
--                                               petrol, / 26.4 for diesel); otherwise
--                                               estimated; electric: WLTP kWh/100 km
--   reliability_score                           ESTIMATE: the average of the brand's
--                                               engines of that fuel already in the
--                                               catalogue (plug-in 0.5 lower). Six brands
--                                               new to the table are set by the group
--                                               they share engines with: Jaguar 6.3 (Land
--                                               Rover), Jeep 6.7, Maserati 6.0, BYD and
--                                               Smart 7.5, Omoda 7.0
--   maintenance_cost_year                       ESTIMATE: brand level + 0.97 EUR per cv,
--                                               fitted on the existing rows (error ~44 EUR)
--
-- Not in this file: Cupra Ateca, Mercedes GLS, Subaru Forester and Outback
-- have too few listings in Portugal to tell their engines from.
--
-- `source` records which of these applies to the row.
--
-- New columns on engines: year_from / year_to (model years the variant is on
-- sale with), plug_in, source, listings_seen. One existing row spelled
-- "híbrido" becomes "hibrido"; existing plug-in hybrids get plug_in = TRUE.
--
-- Also: driving-character scores and a one-line description for the
-- 72 models that had none (written by hand, same scale as the others).
--
-- Idempotent: an engine is inserted only if its model has no engine of that
-- code, a character row only if the model has none.

BEGIN;

ALTER TABLE engines
    ADD COLUMN IF NOT EXISTS year_from     INTEGER,
    ADD COLUMN IF NOT EXISTS year_to       INTEGER,
    ADD COLUMN IF NOT EXISTS plug_in       BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS source        VARCHAR(200),
    ADD COLUMN IF NOT EXISTS listings_seen INTEGER;

UPDATE engines SET fuel_type = 'hibrido' WHERE fuel_type = 'híbrido';

UPDATE engines
SET plug_in = TRUE
WHERE fuel_type = 'hibrido' AND NOT plug_in
  AND (code ILIKE '%PHEV%' OR code ILIKE '%plug%' OR code ILIKE '%e-hybrid%'
       OR code ILIKE '%TFSIe%' OR code ILIKE '%recharge%' OR consumption_mixed < 4.0);

INSERT INTO engines
    (model_id, code, fuel_type, displacement_cc, power_hp, transmission,
     consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year,
     year_from, year_to, plug_in, source, listings_seen)
SELECT vm.id, v.code, v.fuel_type, v.displacement_cc, v.power_hp, v.transmission,
       v.consumption_mixed, v.co2_emissions, v.reliability_score, v.maintenance_cost_year,
       v.year_from, v.year_to, v.plug_in, v.source, v.listings_seen
FROM (VALUES
    ('Alfa Romeo', 'Stelvio', '2.2 D 190cv', 'diesel', 2143::int, 190, 'auto 8', 5.6::numeric, 148::int, 6.5::numeric, 690, 2019, 2022, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 3 anúncios', 12),
    ('Alfa Romeo', 'Stelvio', '2.2 D 180cv', 'diesel', 2143::int, 180, 'auto 8', 4.7::numeric, 124::int, 6.5::numeric, 690, 2017, 2020, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 2 anúncios', 8),
    ('Alfa Romeo', 'Stelvio', '2.2 D 160cv', 'diesel', 2143::int, 160, 'auto 8', 5.7::numeric, 149::int, 6.5::numeric, 670, 2021, 2026, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 2 anúncios', 7),
    ('Alfa Romeo', 'Stelvio', '2.9 T 510cv', 'gasolina', 2891::int, 510, 'auto 8', 10.2::numeric, 235::int, 5.8::numeric, 900, 2018, 2021, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Alfa Romeo', 'Stelvio', '2.2 D 210cv', 'diesel', 2143::int, 210, 'auto', 7.9::numeric, 209::int, 6.5::numeric, 710, 2017, 2026, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Audi', 'A5', '2.0 TDI 190cv', 'diesel', 1968::int, 190, 'auto 7', 5.2::numeric, 138::int, 7.3::numeric, 610, 2014, 2019, FALSE, 'Standvirtual 2026-11-13: 43 anúncios; consumo: CO2 declarado em 2 anúncios', 43),
    ('Audi', 'A5', '2.0 TDI 150cv', 'diesel', 1968::int, 150, 'auto 7', 4.3::numeric, 113::int, 7.3::numeric, 570, 2013, 2019, FALSE, 'Standvirtual 2026-11-13: 23 anúncios; consumo: CO2 declarado em 1 anúncio', 23),
    ('Audi', 'A5', '40 TDI 204cv', 'diesel', 1968::int, 204, 'auto 7', 4.9::numeric, 130::int, 7.3::numeric, 620, 2022, 2026, FALSE, 'Standvirtual 2026-11-13: 18 anúncios; consumo: CO2 declarado em 1 anúncio', 18),
    ('Audi', 'A5', '35 TDI 163cv', 'diesel', 1968::int, 163, 'auto 7', 4.7::numeric, 125::int, 7.3::numeric, 580, 2010, 2023, FALSE, 'Standvirtual 2026-11-13: 16 anúncios; consumo: CO2 declarado em 2 anúncios', 16),
    ('Audi', 'A6', '40 TDI 204cv', 'diesel', 1968::int, 204, 'auto', 5.4::numeric, NULL::int, 7.3::numeric, 620, 2019, 2024, FALSE, 'Standvirtual 2026-11-13: 34 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 34),
    ('Audi', 'A6', '2.0 TDi 190cv', 'diesel', 1968::int, 190, 'auto 7', 4.5::numeric, 119::int, 7.3::numeric, 610, 2014, 2018, FALSE, 'Standvirtual 2026-11-13: 30 anúncios; consumo: CO2 declarado em 2 anúncios', 30),
    ('Audi', 'A6', '2.0 TDi 177cv', 'diesel', 1968::int, 177, 'auto', 5.1::numeric, 133::int, 7.3::numeric, 590, 2011, 2014, FALSE, 'Standvirtual 2026-11-13: 19 anúncios; consumo: CO2 declarado em 2 anúncios', 19),
    ('Audi', 'A6', '50 TFSIe PHEV 299cv', 'hibrido', 1984::int, 299, 'auto 7', 1.5::numeric, NULL::int, 7.0::numeric, 710, 2020, 2026, TRUE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 13),
    ('Audi', 'A6', '3.0 TDi 218cv', 'diesel', 2967::int, 218, 'auto 7', 5.2::numeric, 137::int, 7.3::numeric, 630, 2014, 2022, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 2 anúncios', 9),
    ('Audi', 'Q3', '45 TFSIe PHEV 245cv', 'hibrido', 1395::int, 245, 'auto', 1.3::numeric, 31::int, 7.0::numeric, 660, 2021, 2024, TRUE, 'Standvirtual 2026-11-13: 49 anúncios; consumo: CO2 declarado em 2 anúncios', 49),
    ('Audi', 'Q3', '35 TDI 150cv', 'diesel', 1968::int, 150, 'auto 7', 5.0::numeric, 131::int, 7.3::numeric, 570, 2015, 2023, FALSE, 'Standvirtual 2026-11-13: 20 anúncios; consumo: CO2 declarado em 3 anúncios', 20),
    ('Audi', 'Q3', '35 TFSI 150cv', 'gasolina', 1498::int, 150, 'auto 7', 6.1::numeric, NULL::int, 7.3::numeric, 570, 2019, 2026, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 9),
    ('Audi', 'Q7', '3.0 TDI 240cv', 'diesel', 2967::int, 240, 'auto 8', 7.4::numeric, 195::int, 7.3::numeric, 650, 2006, 2016, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 2 anúncios', 11),
    ('Audi', 'Q7', '3.0 TDi 272cv', 'diesel', 2967::int, 272, 'auto 8', 6.0::numeric, 158::int, 7.3::numeric, 690, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Audi', 'Q7', '3.0 TDi PHEV 373cv', 'hibrido', 2967::int, 373, 'auto', 2.2::numeric, 50::int, 7.0::numeric, 780, 2017, 2020, TRUE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 1 anúncio', 5),
    ('Audi', 'Q7', '3.0 TDi 218cv', 'diesel', 2967::int, 218, 'auto 8', 5.6::numeric, 149::int, 7.3::numeric, 630, 2016, 2018, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Audi', 'Q8', '55 TFSIe PHEV 381cv', 'hibrido', 2995::int, 381, 'auto', 1.5::numeric, NULL::int, 7.0::numeric, 790, 2022, 2025, TRUE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 5),
    ('Audi', 'Q8', '50 TDI 286cv', 'diesel', 2967::int, 286, 'auto 8', 7.9::numeric, 208::int, 7.3::numeric, 700, 2018, 2020, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Audi', 'TT', '2.0 TDI 170cv', 'diesel', 1968::int, 170, 'manual 6', 5.3::numeric, 139::int, 7.3::numeric, 590, 2009, 2014, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 3 anúncios', 11),
    ('Audi', 'TT', '2.0 TDI 184cv', 'diesel', 1968::int, 184, 'manual 6', 4.6::numeric, 122::int, 7.3::numeric, 600, 2014, 2017, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Audi', 'TT', '2.0 TFSI 230cv', 'gasolina', 1984::int, 230, 'auto 6', 6.6::numeric, 153::int, 7.3::numeric, 640, 2015, 2017, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 3 anúncios', 8),
    ('Audi', 'TT', '1.8 TFSI 160cv', 'gasolina', 1798::int, 160, 'manual 6', 6.9::numeric, 159::int, 7.3::numeric, 580, 2010, 2013, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('BMW', 'Série 2 Active Tourer', '216d 116cv', 'diesel', 1496::int, 116, 'manual 6', 4.8::numeric, 125::int, 7.2::numeric, 560, 2015, 2021, FALSE, 'Standvirtual 2026-11-13: 49 anúncios; consumo: CO2 declarado em 2 anúncios', 49),
    ('BMW', 'Série 2 Active Tourer', '225xe PHEV 245cv', 'hibrido', 1499::int, 245, 'auto', 1.5::numeric, NULL::int, 7.0::numeric, 690, 2022, 2026, TRUE, 'Standvirtual 2026-11-13: 47 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 47),
    ('BMW', 'Série 2 Active Tourer', '225xe PHEV 224cv', 'hibrido', 1499::int, 224, 'auto 8', 1.5::numeric, 35::int, 7.0::numeric, 670, 2016, 2021, TRUE, 'Standvirtual 2026-11-13: 33 anúncios; consumo: CO2 declarado em 3 anúncios', 33),
    ('BMW', 'Série 2 Active Tourer', '218d 150cv', 'diesel', 1995::int, 150, 'auto 8', 4.5::numeric, 117::int, 7.2::numeric, 590, 2015, 2023, FALSE, 'Standvirtual 2026-11-13: 20 anúncios; consumo: CO2 declarado em 2 anúncios', 20),
    ('BMW', 'Série 2 Active Tourer', '218i 136cv', 'gasolina', 1499::int, 136, 'auto 7', 6.0::numeric, 140::int, 7.3::numeric, 580, 2021, 2024, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 1 anúncio', 11),
    ('BMW', 'Série 4', '420d 190cv', 'diesel', 1995::int, 190, 'auto 8', 5.1::numeric, 134::int, 7.2::numeric, 630, 2015, 2025, FALSE, 'Standvirtual 2026-11-13: 176 anúncios; consumo: CO2 declarado em 3 anúncios', 176),
    ('BMW', 'Série 4', '420d 184cv', 'diesel', 1995::int, 184, 'auto 8', 4.7::numeric, 124::int, 7.2::numeric, 630, 2014, 2016, FALSE, 'Standvirtual 2026-11-13: 51 anúncios; consumo: CO2 declarado em 2 anúncios', 51),
    ('BMW', 'Série 4', '418d 150cv', 'diesel', 1995::int, 150, 'auto 8', 5.6::numeric, 149::int, 7.2::numeric, 590, 2015, 2021, FALSE, 'Standvirtual 2026-11-13: 39 anúncios; consumo: CO2 declarado em 3 anúncios', 39),
    ('BMW', 'Série 4', '420i 184cv', 'gasolina', 1998::int, 184, 'auto 8', 6.1::numeric, 142::int, 7.3::numeric, 630, 2014, 2024, FALSE, 'Standvirtual 2026-11-13: 25 anúncios; consumo: CO2 declarado em 2 anúncios', 25),
    ('BMW', 'Série 5', '520d 190cv', 'diesel', 1995::int, 190, 'auto', 5.1::numeric, 134::int, 7.2::numeric, 630, 2015, 2023, FALSE, 'Standvirtual 2026-11-13: 154 anúncios; consumo: CO2 declarado em 3 anúncios', 154),
    ('BMW', 'Série 5', '530e PHEV 292cv', 'hibrido', 1998::int, 292, 'auto', 1.5::numeric, NULL::int, 7.0::numeric, 730, 2020, 2026, TRUE, 'Standvirtual 2026-11-13: 120 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 120),
    ('BMW', 'Série 5', '520d 184cv', 'diesel', 1995::int, 184, 'auto 8', 5.2::numeric, 136::int, 7.2::numeric, 630, 2010, 2014, FALSE, 'Standvirtual 2026-11-13: 77 anúncios; consumo: CO2 declarado em 2 anúncios', 77),
    ('BMW', 'Série 5', '530e PHEV 252cv', 'hibrido', 1998::int, 252, 'auto 8', 1.6::numeric, 36::int, 7.0::numeric, 690, 2017, 2021, TRUE, 'Standvirtual 2026-11-13: 38 anúncios; consumo: CO2 declarado em 1 anúncio', 38),
    ('BMW', 'X5', 'X5 25d 231cv', 'diesel', 1995::int, 231, 'auto 8', 5.4::numeric, NULL::int, 7.2::numeric, 670, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 33 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 33),
    ('BMW', 'X5', 'X5 45e PHEV 394cv', 'hibrido', 2998::int, 394, 'auto 8', 1.2::numeric, 27::int, 7.0::numeric, 830, 2020, 2023, TRUE, 'Standvirtual 2026-11-13: 32 anúncios; consumo: CO2 declarado em 1 anúncio', 32),
    ('BMW', 'X5', 'X5 50e PHEV 489cv', 'hibrido', 2998::int, 489, 'auto 8', 1.5::numeric, NULL::int, 7.0::numeric, 840, 2023, 2025, TRUE, 'Standvirtual 2026-11-13: 16 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 16),
    ('BMW', 'X5', 'X5 25d 218cv', 'diesel', 1995::int, 218, 'auto 8', 5.6::numeric, 149::int, 7.2::numeric, 660, 2014, 2017, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('BMW', 'X5', 'X5 30d 265cv', 'diesel', 2993::int, 265, 'auto 8', 7.6::numeric, 201::int, 7.2::numeric, 710, 2014, 2020, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('BMW', 'X6', 'X6 40d 313cv', 'diesel', 2993::int, 313, 'auto 8', 7.2::numeric, 190::int, 7.2::numeric, 750, 2010, 2019, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 2 anúncios', 12),
    ('BMW', 'X6', 'X6 30d 265cv', 'diesel', 2993::int, 265, 'auto 8', 6.9::numeric, 181::int, 7.2::numeric, 710, 2015, 2022, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 2 anúncios', 9),
    ('BMW', 'X6', 'X6 30d 286cv', 'diesel', 2993::int, 286, 'auto 6', 8.3::numeric, 220::int, 7.2::numeric, 730, 2020, 2024, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('BMW', 'Z4', 'Z4 23i 204cv', 'gasolina', 2497::int, 204, 'auto 6', 8.3::numeric, 192::int, 7.3::numeric, 650, 2009, 2011, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 3 anúncios', 9),
    ('BMW', 'Z4', 'Z4 20i 197cv', 'gasolina', 1998::int, 197, 'auto 8', 5.7::numeric, 133::int, 7.3::numeric, 640, 2019, 2026, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 2 anúncios', 9),
    ('BMW', 'Z4', 'Z4 28i 245cv', 'gasolina', 1997::int, 245, 'auto 7', 6.9::numeric, 159::int, 7.3::numeric, 690, 2012, 2016, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 2 anúncios', 7),
    ('BMW', 'Z4', 'Z4 30i 258cv', 'gasolina', 1998::int, 258, 'auto 8', 6.9::numeric, 161::int, 7.3::numeric, 700, 2020, 2023, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 2 anúncios', 7),
    ('BMW', 'Z4', 'Z4 M40i 340cv', 'gasolina', 2998::int, 340, 'auto 8', 7.7::numeric, 179::int, 7.3::numeric, 780, 2021, 2025, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('BYD', 'Atto 3', '60.48 kWh 204cv', 'eletrico', 0::int, 204, 'auto', 15.6::numeric, 0::int, 7.5::numeric, 240, 2022, 2024, FALSE, 'Standvirtual 2026-11-13: 114 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 114),
    ('BYD', 'Dolphin', '60.4 kWh 204cv', 'eletrico', 0::int, 204, 'auto', 15.9::numeric, 0::int, 7.5::numeric, 240, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 27 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 27),
    ('BYD', 'Seal', '82.5 kWh 313cv', 'eletrico', 0::int, 313, 'auto', 16.6::numeric, 0::int, 7.5::numeric, 240, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 18 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 18),
    ('BYD', 'Seal', '82.5 kWh 530cv', 'eletrico', 0::int, 530, 'auto', 16.6::numeric, 0::int, 7.5::numeric, 240, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 7),
    ('Citroën', 'Berlingo', '1.5 BlueHDi 102cv', 'diesel', 1499::int, 102, 'manual 5', 4.7::numeric, 124::int, 7.5::numeric, 380, 2020, 2025, FALSE, 'Standvirtual 2026-11-13: 14 anúncios; consumo: CO2 declarado em 2 anúncios', 14),
    ('Citroën', 'Berlingo', '1.6 BlueHDi 102cv', 'diesel', 1560::int, 102, 'manual 5', 4.7::numeric, 124::int, 7.5::numeric, 380, 2016, 2019, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Citroën', 'Berlingo', '1.2 PureTech 110cv', 'gasolina', 1199::int, 110, 'manual 6', 5.3::numeric, 122::int, 6.8::numeric, 390, 2018, 2021, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Citroën', 'Berlingo', '50 kWh 136cv', 'eletrico', 0::int, 136, 'auto', 19.0::numeric, 0::int, 7.5::numeric, 220, 2022, 2026, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 6),
    ('Citroën', 'Berlingo', '1.6 HDi 90cv', 'diesel', 1560::int, 90, 'auto 5', 5.3::numeric, 139::int, 7.5::numeric, 370, 2010, 2012, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Citroën', 'C1', '1.4 HDi 54cv', 'diesel', 1398::int, 54, 'manual 5', 4.1::numeric, 109::int, 7.5::numeric, 340, 2007, 2010, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 3 anúncios', 10),
    ('DS', '7', 'E-Tense PHEV 225cv', 'hibrido', 1598::int, 225, 'auto 8', 1.5::numeric, 35::int, 6.5::numeric, 560, 2021, 2024, TRUE, 'Standvirtual 2026-11-13: 70 anúncios; consumo: CO2 declarado em 2 anúncios', 70),
    ('DS', '7', '1.5 BlueHDi 130cv', 'diesel', 1499::int, 130, 'auto 6', 4.6::numeric, NULL::int, 6.2::numeric, 460, 2018, 2025, FALSE, 'Standvirtual 2026-11-13: 46 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 46),
    ('DS', '7', 'E-Tense PHEV 300cv', 'hibrido', 1598::int, 300, 'auto 8', 1.3::numeric, 31::int, 6.5::numeric, 630, 2020, 2024, TRUE, 'Standvirtual 2026-11-13: 28 anúncios; consumo: CO2 declarado em 2 anúncios', 28),
    ('Fiat', '500X', '1.3 MJ 95cv', 'diesel', 1248::int, 95, 'manual 5', 4.6::numeric, 122::int, 6.9::numeric, 370, 2016, 2024, FALSE, 'Standvirtual 2026-11-13: 60 anúncios; consumo: CO2 declarado em 2 anúncios', 60),
    ('Fiat', '500X', '1.0 FireFly 120cv', 'gasolina', 999::int, 120, 'manual 6', 5.8::numeric, NULL::int, 6.5::numeric, 400, 2019, 2024, FALSE, 'Standvirtual 2026-11-13: 27 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 27),
    ('Fiat', 'Panda', '1.0 Hybrid 70cv', 'gasolina', 999::int, 70, 'manual 6', 4.9::numeric, 114::int, 6.5::numeric, 350, 2022, 2025, FALSE, 'Standvirtual 2026-11-13: 106 anúncios; consumo: CO2 declarado em 2 anúncios', 106),
    ('Ford', 'S-Max', '2.0 TDCi 163cv', 'diesel', 1997::int, 163, 'auto 6', 5.6::numeric, 149::int, 7.5::numeric, 450, 2010, 2016, FALSE, 'Standvirtual 2026-11-13: 15 anúncios; consumo: CO2 declarado em 2 anúncios', 15),
    ('Ford', 'S-Max', '2.0 TDCi 150cv', 'diesel', 1997::int, 150, 'manual 7', 6.2::numeric, 164::int, 7.5::numeric, 440, 2016, 2021, FALSE, 'Standvirtual 2026-11-13: 14 anúncios; consumo: CO2 declarado em 2 anúncios', 14),
    ('Ford', 'S-Max', '2.0 TDCi 140cv', 'diesel', 1997::int, 140, 'manual 6', 6.0::numeric, 159::int, 7.5::numeric, 430, 2006, 2015, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: CO2 declarado em 3 anúncios', 13),
    ('Ford', 'S-Max', '1.8 TDCi 125cv', 'diesel', 1753::int, 125, 'manual 5', 6.2::numeric, 164::int, 7.5::numeric, 420, 2006, 2010, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: CO2 declarado em 2 anúncios', 13),
    ('Ford', 'S-Max', '2.0 TDCi 190cv', 'diesel', 1997::int, 190, 'auto 8', 6.5::numeric, 171::int, 7.5::numeric, 480, 2018, 2022, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Ford', 'Tourneo Connect', '1.5 TDCi 100cv', 'diesel', 1499::int, 100, 'manual 6', 4.9::numeric, 130::int, 7.5::numeric, 390, 2016, 2025, FALSE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: CO2 declarado em 3 anúncios', 3),
    ('Honda', 'HR-V', '1.5 i-VTEC 130cv', 'gasolina', 1498::int, 130, 'auto', 5.8::numeric, 134::int, 8.2::numeric, 340, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 3 anúncios', 8),
    ('Honda', 'HR-V', '1.6 i-DTEC 120cv', 'diesel', 1597::int, 120, 'manual 6', 3.9::numeric, 104::int, 8.8::numeric, 330, 2016, 2019, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 1 anúncio', 4),
    ('Honda', 'Jazz', '1.3 I-VTEC 102cv', 'gasolina', 1318::int, 102, 'manual 6', 5.4::numeric, 125::int, 8.2::numeric, 310, 2009, 2020, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Honda', 'Jazz', '1.2 i-VTEC 90cv', 'gasolina', 1198::int, 90, 'manual 5', 5.3::numeric, 123::int, 8.2::numeric, 300, 2009, 2014, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 3 anúncios', 5),
    ('Honda', 'Jazz', '1.5 i-MMD Híbrido 122cv', 'hibrido', 1498::int, 122, 'auto', 4.4::numeric, 102::int, 9.0::numeric, 330, 2025, 2026, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 3 anúncios', 5),
    ('Honda', 'e:Ny1', '68.8 kWh 204cv', 'eletrico', 0::int, 204, 'auto', 18.2::numeric, 0::int, 8.8::numeric, 250, 2023, 2026, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 8),
    ('Hyundai', 'Ioniq', '1.6 GDI PHEV 141cv', 'hibrido', 1580::int, 141, 'auto 6', 1.1::numeric, 26::int, 7.5::numeric, 390, 2018, 2021, TRUE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: CO2 declarado em 2 anúncios', 3),
    ('Hyundai', 'Ioniq', '1.6 GDI Híbrido 141cv', 'hibrido', 1580::int, 141, 'auto 6', 4.5::numeric, 105::int, 8.0::numeric, 390, 2019, 2020, FALSE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: CO2 declarado em 3 anúncios', 3),
    ('Hyundai', 'Ioniq 6', '77 kWh 228cv', 'eletrico', 0::int, 228, 'auto', 14.3::numeric, 0::int, 8.0::numeric, 240, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 5),
    ('Jaguar', 'E-Pace', '2.0 i4D 150cv', 'diesel', 1999::int, 150, 'manual 6', 6.0::numeric, 158::int, 6.3::numeric, 760, 2018, 2020, FALSE, 'Standvirtual 2026-11-13: 18 anúncios; consumo: CO2 declarado em 2 anúncios', 18),
    ('Jaguar', 'E-Pace', '1.5 P300e PHEV 309cv', 'hibrido', 1498::int, 309, 'auto 8', 1.4::numeric, 32::int, 5.8::numeric, 910, 2021, 2024, TRUE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Jaguar', 'E-Pace', '1.5 P160 160cv', 'gasolina', 1498::int, 160, 'auto 8', 7.8::numeric, 181::int, 6.3::numeric, 770, 2021, 2022, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 3 anúncios', 5),
    ('Jaguar', 'F-Pace', '2.0 i4D 180cv', 'diesel', 1999::int, 180, 'auto 8', 5.2::numeric, NULL::int, 6.3::numeric, 790, 2016, 2020, FALSE, 'Standvirtual 2026-11-13: 43 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 43),
    ('Jaguar', 'F-Pace', '2.0 P400e PHEV 404cv', 'hibrido', 1997::int, 404, 'auto 8', 1.6::numeric, 37::int, 5.8::numeric, 1000, 2021, 2024, TRUE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 2 anúncios', 12),
    ('Jeep', 'Avenger', '1.2 GSE 101cv', 'gasolina', 1199::int, 101, 'manual', 4.3::numeric, 100::int, 6.7::numeric, 430, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 70 anúncios; consumo: CO2 declarado em 3 anúncios', 70),
    ('Jeep', 'Avenger', '54 kWh 156cv', 'eletrico', 0::int, 156, 'auto', 15.4::numeric, 0::int, 7.2::numeric, 250, 2023, 2026, FALSE, 'Standvirtual 2026-11-13: 29 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 29),
    ('Jeep', 'Avenger', '1.2 e-Hybrid 110cv', 'hibrido', 1199::int, 110, 'auto 6', 4.3::numeric, 100::int, 6.7::numeric, 440, 2025, 2026, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 3 anúncios', 7),
    ('Jeep', 'Compass', '1.3 TG PHEV 240cv', 'hibrido', 1332::int, 240, 'auto', 2.0::numeric, 47::int, 6.2::numeric, 570, 2020, 2025, TRUE, 'Standvirtual 2026-11-13: 19 anúncios; consumo: CO2 declarado em 1 anúncio', 19),
    ('Jeep', 'Compass', '1.6 M-Jet 120cv', 'diesel', 1598::int, 120, 'manual 6', 4.6::numeric, NULL::int, 6.7::numeric, 450, 2017, 2021, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 12),
    ('Jeep', 'Compass', '1.3 TG PHEV 190cv', 'hibrido', 1332::int, 190, 'auto 6', 2.0::numeric, 45::int, 6.2::numeric, 520, 2021, 2023, TRUE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 2 anúncios', 12),
    ('Jeep', 'Compass', '1.5 TG 130cv', 'gasolina', 1469::int, 130, 'auto 7', 5.8::numeric, 134::int, 6.7::numeric, 460, 2021, 2025, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 2 anúncios', 8),
    ('Jeep', 'Compass', '1.6 e-Hybrid PHEV 225cv', 'hibrido', 1596::int, 225, 'auto', 2.5::numeric, 58::int, 6.2::numeric, 550, 2026, 2026, TRUE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Jeep', 'Compass', '74 kWh 213cv', 'eletrico', 0::int, 213, 'auto', 16.0::numeric, 0::int, 7.2::numeric, 250, 2025, 2026, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 6),
    ('Kia', 'EV3', '58.3 kWh 204cv', 'eletrico', 0::int, 204, 'auto', 14.9::numeric, 0::int, 7.9::numeric, 260, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 11),
    ('Land Rover', 'Discovery Sport', '2.0 eD4 150cv', 'diesel', 1999::int, 150, 'manual 6', 6.4::numeric, 168::int, 6.5::numeric, 580, 2016, 2020, FALSE, 'Standvirtual 2026-11-13: 36 anúncios; consumo: CO2 declarado em 3 anúncios', 36),
    ('Land Rover', 'Discovery Sport', '1.5 I3 PHEV 309cv', 'hibrido', 1497::int, 309, 'auto 8', 1.5::numeric, 34::int, 6.0::numeric, 730, 2020, 2024, TRUE, 'Standvirtual 2026-11-13: 26 anúncios; consumo: CO2 declarado em 2 anúncios', 26),
    ('Land Rover', 'Discovery Sport', '1.5 I3 PHEV 269cv', 'hibrido', 1498::int, 269, 'auto 8', 1.5::numeric, 35::int, 6.0::numeric, 690, 2023, 2026, TRUE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 2 anúncios', 12),
    ('Land Rover', 'Discovery Sport', '2.0 D165 163cv', 'diesel', 1998::int, 163, 'manual 6', 4.5::numeric, 119::int, 6.5::numeric, 590, 2021, 2022, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 1 anúncio', 6),
    ('Land Rover', 'Range Rover Evoque', '2.0 eD4 150cv', 'diesel', 1999::int, 150, 'manual 6', 6.4::numeric, 168::int, 6.5::numeric, 580, 2016, 2020, FALSE, 'Standvirtual 2026-11-13: 64 anúncios; consumo: CO2 declarado em 3 anúncios', 64),
    ('Land Rover', 'Range Rover Evoque', '1.5 P300e PHEV 309cv', 'hibrido', 1498::int, 309, 'auto 8', 1.5::numeric, NULL::int, 6.0::numeric, 730, 2020, 2024, TRUE, 'Standvirtual 2026-11-13: 43 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 43),
    ('Land Rover', 'Range Rover Evoque', '2.2 eD4 150cv', 'diesel', 2179::int, 150, 'manual 6', 6.4::numeric, 168::int, 6.5::numeric, 580, 2012, 2015, FALSE, 'Standvirtual 2026-11-13: 31 anúncios; consumo: CO2 declarado em 3 anúncios', 31),
    ('Land Rover', 'Range Rover Evoque', '1.5 P270e PHEV 269cv', 'hibrido', 1498::int, 269, 'auto 8', 1.5::numeric, NULL::int, 6.0::numeric, 690, 2023, 2026, TRUE, 'Standvirtual 2026-11-13: 23 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 23),
    ('Land Rover', 'Range Rover Sport', '2.0 Si4 PHEV 404cv', 'hibrido', 1997::int, 404, 'auto 8', 1.5::numeric, NULL::int, 6.0::numeric, 820, 2018, 2022, TRUE, 'Standvirtual 2026-11-13: 35 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 35),
    ('Land Rover', 'Range Rover Sport', '3.0 TDV6 258cv', 'diesel', 2993::int, 258, 'auto 8', 6.9::numeric, 182::int, 6.5::numeric, 680, 2012, 2019, FALSE, 'Standvirtual 2026-11-13: 20 anúncios; consumo: CO2 declarado em 2 anúncios', 20),
    ('Land Rover', 'Range Rover Sport', '3.0 SDV6 306cv', 'diesel', 2993::int, 306, 'auto 8', 7.5::numeric, 197::int, 6.5::numeric, 730, 2015, 2023, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 2 anúncios', 11),
    ('Land Rover', 'Range Rover Sport', '3.0 SDV6 Híbrido 340cv', 'hibrido', 2993::int, 340, 'auto 8', 6.3::numeric, 166::int, 6.3::numeric, 760, 2015, 2017, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Land Rover', 'Range Rover Velar', '2.0 P400e PHEV 404cv', 'hibrido', 1997::int, 404, 'auto 8', 1.7::numeric, 39::int, 6.0::numeric, 820, 2021, 2026, TRUE, 'Standvirtual 2026-11-13: 35 anúncios; consumo: CO2 declarado em 1 anúncio', 35),
    ('Land Rover', 'Range Rover Velar', '2.0 D 241cv', 'diesel', 1999::int, 241, 'auto 8', 7.2::numeric, 189::int, 6.5::numeric, 660, 2017, 2020, FALSE, 'Standvirtual 2026-11-13: 24 anúncios; consumo: CO2 declarado em 2 anúncios', 24),
    ('Land Rover', 'Range Rover Velar', '2.0 D 180cv', 'diesel', 1999::int, 180, 'auto 8', 6.0::numeric, 158::int, 6.5::numeric, 610, 2017, 2021, FALSE, 'Standvirtual 2026-11-13: 14 anúncios; consumo: CO2 declarado em 2 anúncios', 14),
    ('Land Rover', 'Range Rover Velar', '3.0 D 300cv', 'diesel', 2993::int, 300, 'auto 8', 7.7::numeric, 203::int, 6.5::numeric, 720, 2017, 2021, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 2 anúncios', 9),
    ('Lexus', 'ES', 'ES 300h 218cv', 'hibrido', 2487::int, 218, 'auto', 5.4::numeric, 126::int, 9.0::numeric, 370, 2019, 2025, FALSE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: CO2 declarado em 1 anúncio', 3),
    ('Lexus', 'IS', 'IS 220 d 177cv', 'diesel', 2231::int, 177, 'manual 6', 6.4::numeric, 168::int, 8.8::numeric, 330, 2007, 2010, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 3 anúncios', 5),
    ('Lexus', 'IS', 'IS 300h 223cv', 'hibrido', 2494::int, 223, 'auto', 5.0::numeric, 117::int, 9.0::numeric, 370, 2016, 2017, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Lexus', 'RX', 'RX 450h 299cv', 'hibrido', 3456::int, 299, 'auto', 6.0::numeric, 140::int, 9.0::numeric, 450, 2009, 2011, FALSE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: CO2 declarado em 3 anúncios', 3),
    ('Lexus', 'UX', 'UX 250h 184cv', 'hibrido', 1987::int, 184, 'auto', 5.4::numeric, 124::int, 9.0::numeric, 340, 2019, 2024, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: CO2 declarado em 2 anúncios', 13),
    ('Lexus', 'UX', 'UX 300e 204cv', 'eletrico', 0::int, 204, 'auto', 16.7::numeric, 0::int, 8.8::numeric, 250, 2021, 2022, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 7),
    ('MG', '5', '61 kWh 156cv', 'eletrico', 0::int, 156, 'auto', 17.5::numeric, 0::int, 7.0::numeric, 220, 2022, 2024, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 13),
    ('MG', '5', '51 kWh 177cv', 'eletrico', 0::int, 177, 'auto', 17.5::numeric, 0::int, 7.0::numeric, 220, 2022, 2024, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 7),
    ('MG', 'HS', '1.5 T-GDI EHS PHEV 258cv', 'hibrido', 1490::int, 258, 'auto 10', 1.9::numeric, 43::int, 7.0::numeric, 480, 2021, 2025, TRUE, 'Standvirtual 2026-11-13: 34 anúncios; consumo: CO2 declarado em 2 anúncios', 34),
    ('MG', 'HS', '1.5 T-GDI PHEV 272cv', 'hibrido', 1496::int, 272, 'auto', 1.5::numeric, NULL::int, 7.0::numeric, 500, 2024, 2026, TRUE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 9),
    ('MG', 'HS', '1.5 T 170cv', 'gasolina', 1498::int, 170, 'auto 7', 7.5::numeric, 173::int, 7.0::numeric, 400, 2023, 2026, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 3 anúncios', 8),
    ('MG', 'ZS EV', 'EV 143cv', 'eletrico', 0::int, 143, 'auto', 17.3::numeric, 0::int, 7.0::numeric, 220, 2019, 2021, FALSE, 'Standvirtual 2026-11-13: 19 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 19),
    ('MG', 'ZS EV', 'EV 156cv', 'eletrico', 0::int, 156, 'auto', 17.3::numeric, 0::int, 7.0::numeric, 220, 2020, 2024, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 9),
    ('MG', 'ZS EV', 'EV 177cv', 'eletrico', 0::int, 177, 'auto', 17.3::numeric, 0::int, 7.0::numeric, 220, 2022, 2024, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 8),
    ('MINI', 'Clubman', 'One D 116cv', 'diesel', 1496::int, 116, 'manual 7', 4.8::numeric, 126::int, 7.2::numeric, 510, 2016, 2022, FALSE, 'Standvirtual 2026-11-13: 58 anúncios; consumo: CO2 declarado em 2 anúncios', 58),
    ('MINI', 'Clubman', 'Cooper D 150cv', 'diesel', 1995::int, 150, 'auto 8', 4.7::numeric, NULL::int, 7.2::numeric, 540, 2015, 2023, FALSE, 'Standvirtual 2026-11-13: 28 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 28),
    ('MINI', 'Clubman', 'Cooper D 110cv', 'diesel', 1560::int, 110, 'manual 6', 4.0::numeric, 106::int, 7.2::numeric, 500, 2008, 2014, FALSE, 'Standvirtual 2026-11-13: 26 anúncios; consumo: CO2 declarado em 2 anúncios', 26),
    ('MINI', 'Clubman', 'One 102cv', 'gasolina', 1499::int, 102, 'manual 6', 6.2::numeric, 144::int, 7.0::numeric, 500, 2016, 2021, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('MINI', 'Clubman', 'Cooper SD 190cv', 'diesel', 1995::int, 190, 'auto 8', 5.0::numeric, 131::int, 7.2::numeric, 580, 2016, 2022, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('MINI', 'Countryman', 'Cooper SE PHEV 220cv', 'hibrido', 1499::int, 220, 'auto 8', 1.9::numeric, 44::int, 6.5::numeric, 610, 2018, 2023, TRUE, 'Standvirtual 2026-11-13: 64 anúncios; consumo: CO2 declarado em 2 anúncios', 64),
    ('MINI', 'Countryman', 'One D 116cv', 'diesel', 1496::int, 116, 'manual 6', 5.0::numeric, 131::int, 7.2::numeric, 510, 2017, 2021, FALSE, 'Standvirtual 2026-11-13: 27 anúncios; consumo: CO2 declarado em 3 anúncios', 27),
    ('MINI', 'Countryman', 'Cooper D 112cv', 'diesel', 1598::int, 112, 'manual 6', 4.2::numeric, 111::int, 7.2::numeric, 510, 2011, 2016, FALSE, 'Standvirtual 2026-11-13: 26 anúncios; consumo: CO2 declarado em 2 anúncios', 26),
    ('MINI', 'Countryman', 'Cooper D 150cv', 'diesel', 1995::int, 150, 'auto 8', 4.5::numeric, 120::int, 7.2::numeric, 540, 2017, 2024, FALSE, 'Standvirtual 2026-11-13: 22 anúncios; consumo: CO2 declarado em 3 anúncios', 22),
    ('MINI', 'Countryman', 'Cooper S 184cv', 'gasolina', 1598::int, 184, 'manual 6', 6.2::numeric, 143::int, 7.0::numeric, 580, 2009, 2014, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Maserati', 'Grecale', '2.0 GT 300cv', 'gasolina', 1995::int, 300, 'auto 8', 9.0::numeric, 209::int, 6.0::numeric, 1250, 2022, 2025, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 2 anúncios', 8),
    ('Mazda', 'CX-3', '1.5 Skyactiv-D 105cv', 'diesel', 1499::int, 105, 'manual 6', 4.0::numeric, 105::int, 8.0::numeric, 360, 2015, 2018, FALSE, 'Standvirtual 2026-11-13: 19 anúncios; consumo: CO2 declarado em 3 anúncios', 19),
    ('Mazda', 'CX-3', '1.8 Skyactiv-D 115cv', 'diesel', 1759::int, 115, 'manual 6', 5.2::numeric, 138::int, 8.0::numeric, 370, 2019, 2019, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Mercedes-Benz', 'CLE', 'CLE 300 e PHEV 313cv', 'hibrido', 1999::int, 313, 'auto 9', 2.1::numeric, 49::int, 7.0::numeric, 750, 2024, 2026, TRUE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 2 anúncios', 8),
    ('Mercedes-Benz', 'CLE', 'CLE 53 AMG 449cv', 'gasolina', 2999::int, 449, 'auto 9', 8.9::numeric, 207::int, 7.1::numeric, 840, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 1 anúncio', 6),
    ('Mercedes-Benz', 'CLE', 'CLE 220 d 197cv', 'diesel', 1993::int, 197, 'auto 9', 4.7::numeric, 124::int, 7.5::numeric, 640, 2023, 2026, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 1 anúncio', 6),
    ('Mercedes-Benz', 'Classe B', 'B 180 d 109cv', 'diesel', 1461::int, 109, 'manual 7', 3.9::numeric, 104::int, 7.5::numeric, 560, 2013, 2018, FALSE, 'Standvirtual 2026-11-13: 38 anúncios; consumo: CO2 declarado em 2 anúncios', 38),
    ('Mercedes-Benz', 'Classe B', 'B 180 d (1.9) 116cv', 'diesel', 1950::int, 116, 'auto 8', 5.2::numeric, 136::int, 7.5::numeric, 560, 2021, 2026, FALSE, 'Standvirtual 2026-11-13: 33 anúncios; consumo: CO2 declarado em 3 anúncios', 33),
    ('Mercedes-Benz', 'Classe B', 'B 250 e PHEV 218cv', 'hibrido', 1332::int, 218, 'auto 8', 2.4::numeric, 56::int, 7.0::numeric, 660, 2021, 2025, TRUE, 'Standvirtual 2026-11-13: 32 anúncios; consumo: CO2 declarado em 3 anúncios', 32),
    ('Mercedes-Benz', 'Classe B', 'B 180 d (1.5) 116cv', 'diesel', 1461::int, 116, 'auto 8', 5.2::numeric, 136::int, 7.5::numeric, 560, 2019, 2020, FALSE, 'Standvirtual 2026-11-13: 21 anúncios; consumo: CO2 declarado em 3 anúncios', 21),
    ('Mercedes-Benz', 'Classe B', 'B 180 CDI 109cv', 'diesel', 1991::int, 109, 'manual 7', 3.9::numeric, 104::int, 7.5::numeric, 560, 2006, 2010, FALSE, 'Standvirtual 2026-11-13: 14 anúncios; consumo: CO2 declarado em 2 anúncios', 14),
    ('Mercedes-Benz', 'Classe B', 'B 200 163cv', 'gasolina', 1332::int, 163, 'auto 7', 6.1::numeric, 142::int, 7.1::numeric, 610, 2019, 2023, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 2 anúncios', 12),
    ('Mercedes-Benz', 'Classe E', 'E 300 de PHEV 306cv', 'hibrido', 1950::int, 306, 'auto 9', 1.6::numeric, 37::int, 7.0::numeric, 750, 2019, 2026, TRUE, 'Standvirtual 2026-11-13: 197 anúncios; consumo: CO2 declarado em 2 anúncios', 197),
    ('Mercedes-Benz', 'Classe E', 'E 220 d 194cv', 'diesel', 1950::int, 194, 'auto 9', 4.9::numeric, 129::int, 7.5::numeric, 640, 2016, 2025, FALSE, 'Standvirtual 2026-11-13: 174 anúncios; consumo: CO2 declarado em 3 anúncios', 174),
    ('Mercedes-Benz', 'Classe E', 'E 250 CDI 204cv', 'diesel', 2143::int, 204, 'auto 9', 4.8::numeric, 128::int, 7.5::numeric, 650, 2009, 2016, FALSE, 'Standvirtual 2026-11-13: 81 anúncios; consumo: CO2 declarado em 3 anúncios', 81),
    ('Mercedes-Benz', 'Classe E', 'E 300 BlueTEC Híbrido 231cv', 'hibrido', 2143::int, 231, 'auto 7', 5.2::numeric, NULL::int, 7.2::numeric, 670, 2012, 2020, FALSE, 'Standvirtual 2026-11-13: 29 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 29),
    ('Mercedes-Benz', 'Classe V', 'V 250 d (1.9) 190cv', 'diesel', 1950::int, 190, 'auto 9', 7.4::numeric, 196::int, 7.5::numeric, 640, 2020, 2025, FALSE, 'Standvirtual 2026-11-13: 26 anúncios; consumo: CO2 declarado em 2 anúncios', 26),
    ('Mercedes-Benz', 'Classe V', 'V 250 d (2.1) 190cv', 'diesel', 2143::int, 190, 'auto 9', 7.4::numeric, 196::int, 7.5::numeric, 640, 2014, 2023, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('Mercedes-Benz', 'Classe V', 'V 220 d 163cv', 'diesel', 2143::int, 163, 'auto 7', 5.8::numeric, 153::int, 7.5::numeric, 610, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 2 anúncios', 8),
    ('Mercedes-Benz', 'Classe V', 'V 300 d 237cv', 'diesel', 1950::int, 237, 'auto 9', 7.5::numeric, 198::int, 7.5::numeric, 680, 2022, 2026, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Mercedes-Benz', 'GLE', 'GLE 350 de PHEV 320cv', 'hibrido', 1950::int, 320, 'auto 9', 0.9::numeric, 20::int, 7.0::numeric, 760, 2020, 2023, TRUE, 'Standvirtual 2026-11-13: 70 anúncios; consumo: CO2 declarado em 1 anúncio', 70),
    ('Mercedes-Benz', 'GLE', 'GLE 350 de PHEV 333cv', 'hibrido', 1993::int, 333, 'auto 9', 0.8::numeric, 17::int, 7.0::numeric, 770, 2021, 2025, TRUE, 'Standvirtual 2026-11-13: 24 anúncios; consumo: CO2 declarado em 2 anúncios', 24),
    ('Mercedes-Benz', 'GLE', 'GLE 53 AMG 435cv', 'gasolina', 2999::int, 435, 'auto 9', 10.0::numeric, 231::int, 7.1::numeric, 840, 2020, 2026, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 2 anúncios', 11),
    ('Mercedes-Benz', 'GLE', 'GLE 400 d 330cv', 'diesel', 2925::int, 330, 'auto 9', NULL::numeric, NULL::int, 7.5::numeric, 770, 2020, 2022, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: sem dados', 8),
    ('Omoda', '5', '1.5 T-GDi Híbrido 224cv', 'hibrido', 1499::int, 224, 'auto', 5.1::numeric, NULL::int, 7.0::numeric, 450, 2026, 2026, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 5),
    ('Opel', 'Adam', '1.0 T 115cv', 'gasolina', 999::int, 115, 'manual 6', 5.7::numeric, 132::int, 6.6::numeric, 420, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Opel', 'Combo Life', '1.5 CDTi 102cv', 'diesel', 1499::int, 102, 'manual 5', 5.3::numeric, 140::int, 7.2::numeric, 410, 2021, 2026, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: CO2 declarado em 3 anúncios', 12),
    ('Peugeot', '108', '1.2 VTi 82cv', 'gasolina', 1199::int, 82, 'manual 5', 4.3::numeric, 99::int, 6.5::numeric, 390, 2014, 2017, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 2 anúncios', 7),
    ('Peugeot', 'E-308', '54 kWh 156cv', 'eletrico', 0::int, 156, 'auto', 15.2::numeric, 0::int, 7.8::numeric, 210, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 30 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 30),
    ('Peugeot', 'Rifter', '1.2 PureTech 110cv', 'gasolina', 1199::int, 110, 'manual 6', 5.3::numeric, 123::int, 6.5::numeric, 410, 2019, 2026, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 1 anúncio', 5),
    ('Peugeot', 'Rifter', '1.5 BlueHDi 102cv', 'diesel', 1499::int, 102, 'manual 5', 4.8::numeric, 128::int, 7.5::numeric, 400, 2019, 2021, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Porsche', 'Panamera', '4 E-Hybrid PHEV 462cv', 'hibrido', 2894::int, 462, 'auto 8', 1.5::numeric, NULL::int, 7.0::numeric, 950, 2017, 2025, TRUE, 'Standvirtual 2026-11-13: 81 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 81),
    ('Porsche', 'Panamera', '3.0 V6 Diesel 250cv', 'diesel', 2967::int, 250, 'auto 8', 6.5::numeric, 172::int, 7.4::numeric, 800, 2011, 2013, FALSE, 'Standvirtual 2026-11-13: 21 anúncios; consumo: CO2 declarado em 2 anúncios', 21),
    ('Porsche', 'Panamera', 'S Hybrid 380cv', 'hibrido', 2995::int, 380, 'auto 8', NULL::numeric, NULL::int, 7.4::numeric, 930, 2012, 2018, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: sem dados', 13),
    ('Renault', '5 E-Tech', '52 kWh 150cv', 'eletrico', 0::int, 150, 'auto', 15.0::numeric, 0::int, 7.1::numeric, 250, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 20 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 20),
    ('Renault', '5 E-Tech', '40 kWh 122cv', 'eletrico', 0::int, 122, 'auto', 15.0::numeric, 0::int, 7.1::numeric, 250, 2025, 2026, FALSE, 'Standvirtual 2026-11-13: 15 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 15),
    ('Renault', 'Scénic', '1.5 dCi 110cv', 'diesel', 1461::int, 110, 'manual 6', 4.4::numeric, 116::int, 7.5::numeric, 380, 2010, 2017, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: CO2 declarado em 2 anúncios', 13),
    ('Renault', 'Scénic', '87 kWh 218cv', 'eletrico', 0::int, 218, 'auto', 16.8::numeric, 0::int, 7.1::numeric, 250, 2024, 2025, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 5),
    ('Renault', 'Scénic', '1.6 dCi 130cv', 'diesel', 1598::int, 130, 'manual 6', 4.4::numeric, 115::int, 7.5::numeric, 400, 2012, 2018, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Renault', 'Scénic', '1.7 Blue dCi 120cv', 'diesel', 1750::int, 120, 'manual 6', 5.5::numeric, 145::int, 7.5::numeric, 390, 2019, 2020, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Renault', 'Scénic', '1.2 TCe 115cv', 'gasolina', 1197::int, 115, 'manual 6', 6.0::numeric, 140::int, 6.9::numeric, 380, 2012, 2022, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 1 anúncio', 4),
    ('Renault', 'Twingo', 'Electric 82cv', 'eletrico', 0::int, 82, 'auto', 16.0::numeric, 0::int, 7.1::numeric, 250, 2020, 2024, FALSE, 'Standvirtual 2026-11-13: 17 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 17),
    ('Renault', 'Twingo', '1.2 16V 75cv', 'gasolina', 1149::int, 75, 'manual 5', 5.4::numeric, NULL::int, 6.9::numeric, 350, 2003, 2014, FALSE, 'Standvirtual 2026-11-13: 15 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 15),
    ('Renault', 'Twingo', '0.9 TCe 93cv', 'gasolina', 898::int, 93, 'manual 5', 4.6::numeric, 106::int, 6.9::numeric, 360, 2015, 2020, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 3 anúncios', 6),
    ('SEAT', 'Alhambra', '2.0 TDi 150cv', 'diesel', 1968::int, 150, 'manual 6', 4.7::numeric, NULL::int, 7.5::numeric, 450, 2015, 2019, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 13),
    ('SEAT', 'Alhambra', '2.0 TDi 140cv', 'diesel', 1968::int, 140, 'manual 5', 5.5::numeric, 146::int, 7.5::numeric, 440, 2007, 2014, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 2 anúncios', 10),
    ('SEAT', 'Alhambra', '2.0 TDi 115cv', 'diesel', 1896::int, 115, 'manual 6', 6.6::numeric, 174::int, 7.5::numeric, 420, 2004, 2016, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Skoda', 'Superb Combi', '2.0 TDI 150cv', 'diesel', 1968::int, 150, 'auto 7', 5.0::numeric, 131::int, 7.4::numeric, 450, 2022, 2026, FALSE, 'Standvirtual 2026-11-13: 9 anúncios; consumo: CO2 declarado em 2 anúncios', 9),
    ('Smart', '#1', '66 kWh 272cv', 'eletrico', 0::int, 272, 'auto', 16.8::numeric, 0::int, 7.5::numeric, 250, 2023, 2026, FALSE, 'Standvirtual 2026-11-13: 23 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 23),
    ('Smart', '#1', '66 kWh 428cv', 'eletrico', 0::int, 428, 'auto', 16.8::numeric, 0::int, 7.5::numeric, 250, 2022, 2025, FALSE, 'Standvirtual 2026-11-13: 12 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 12),
    ('Smart', '#3', '66 kWh 272cv', 'eletrico', 0::int, 272, 'auto', 16.3::numeric, 0::int, 7.5::numeric, 250, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 23 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 23),
    ('Smart', '#3', '66 kWh 428cv', 'eletrico', 0::int, 428, 'auto', 16.3::numeric, 0::int, 7.5::numeric, 250, 2024, 2025, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 5),
    ('Tesla', 'Model S', '100D 525cv', 'eletrico', 0::int, 525, 'auto', 17.5::numeric, 0::int, 7.5::numeric, 360, 2016, 2018, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 13),
    ('Tesla', 'Model S', 'Long Range 572cv', 'eletrico', 0::int, 572, 'auto', 17.5::numeric, 0::int, 7.5::numeric, 360, 2018, 2020, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 6),
    ('Toyota', 'GR Yaris', '1.6 T 280cv', 'gasolina', 1618::int, 280, 'auto 8', 8.9::numeric, 206::int, 8.4::numeric, 450, 2024, 2024, FALSE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Toyota', 'Prius', '2.0 Plug-in Híbrido 223cv', 'hibrido', 1987::int, 223, 'auto', 5.1::numeric, NULL::int, 9.3::numeric, 390, 2025, 2025, FALSE, 'Standvirtual 2026-11-13: 3 anúncios; consumo: estimativa: motores do catálogo com o mesmo combustível e potência', 3),
    ('Toyota', 'Proace City Verso', '1.5D 102cv', 'diesel', 1499::int, 102, 'manual 6', 5.4::numeric, 143::int, 9.0::numeric, 270, 2021, 2024, FALSE, 'Standvirtual 2026-11-13: 6 anúncios; consumo: CO2 declarado em 2 anúncios', 6),
    ('Volkswagen', 'Caddy', '2.0 TDI 102cv', 'diesel', 1968::int, 102, 'manual 6', 5.4::numeric, 142::int, 7.4::numeric, 430, 2022, 2026, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: CO2 declarado em 3 anúncios', 10),
    ('Volkswagen', 'Caddy', '1.5 TSI PHEV 150cv', 'hibrido', 1498::int, 150, 'auto 6', 1.7::numeric, 40::int, 7.0::numeric, 480, 2026, 2026, TRUE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Volkswagen', 'Sharan', '2.0 TDI 150cv', 'diesel', 1968::int, 150, 'manual 6', 5.8::numeric, 153::int, 7.4::numeric, 480, 2014, 2020, FALSE, 'Standvirtual 2026-11-13: 15 anúncios; consumo: CO2 declarado em 2 anúncios', 15),
    ('Volkswagen', 'Sharan', '2.0 TDI 140cv', 'diesel', 1968::int, 140, 'manual 6', 5.6::numeric, 147::int, 7.4::numeric, 470, 2006, 2015, FALSE, 'Standvirtual 2026-11-13: 13 anúncios; consumo: CO2 declarado em 2 anúncios', 13),
    ('Volkswagen', 'Touran', '1.6 TDI 115cv', 'diesel', 1598::int, 115, 'auto 7', 4.0::numeric, 106::int, 7.4::numeric, 450, 2016, 2019, FALSE, 'Standvirtual 2026-11-13: 15 anúncios; consumo: CO2 declarado em 2 anúncios', 15),
    ('Volkswagen', 'Touran', '1.6 TDI 105cv', 'diesel', 1598::int, 105, 'manual 6', 4.6::numeric, 121::int, 7.4::numeric, 440, 2011, 2015, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 3 anúncios', 7),
    ('Volkswagen', 'Touran', '2.0 TDI 140cv', 'diesel', 1968::int, 140, 'manual 6', 5.4::numeric, 142::int, 7.4::numeric, 470, 2005, 2015, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Volkswagen', 'Touran', '2.0 TDI 122cv', 'diesel', 1968::int, 122, 'manual 6', 5.2::numeric, 136::int, 7.4::numeric, 450, 2021, 2022, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Volkswagen', 'up!', '1.0 BlueMotion 75cv', 'gasolina', 999::int, 75, 'manual 5', 4.1::numeric, 96::int, 7.4::numeric, 410, 2013, 2021, FALSE, 'Standvirtual 2026-11-13: 11 anúncios; consumo: CO2 declarado em 2 anúncios', 11),
    ('Volvo', 'EX30', '69 kWh 428cv', 'eletrico', 0::int, 428, 'auto', 16.7::numeric, 0::int, 7.5::numeric, 240, 2024, 2026, FALSE, 'Standvirtual 2026-11-13: 10 anúncios; consumo: WLTP do fabricante (kWh/100 km)', 10),
    ('Volvo', 'S90', '2.0 D4 190cv', 'diesel', 1969::int, 190, 'auto 8', 5.6::numeric, 147::int, 7.5::numeric, 530, 2016, 2020, FALSE, 'Standvirtual 2026-11-13: 8 anúncios; consumo: CO2 declarado em 3 anúncios', 8),
    ('Volvo', 'S90', '2.0 T8 PHEV 391cv', 'hibrido', 1969::int, 391, 'auto 8', 1.8::numeric, 42::int, 7.0::numeric, 730, 2019, 2021, TRUE, 'Standvirtual 2026-11-13: 4 anúncios; consumo: CO2 declarado em 2 anúncios', 4),
    ('Volvo', 'V90', '2.0 D4 190cv', 'diesel', 1969::int, 190, 'auto 8', 5.9::numeric, 155::int, 7.5::numeric, 530, 2016, 2019, FALSE, 'Standvirtual 2026-11-13: 22 anúncios; consumo: CO2 declarado em 2 anúncios', 22),
    ('Volvo', 'V90', '2.0 T6 PHEV 350cv', 'hibrido', 1969::int, 350, 'auto 8', 0.8::numeric, 19::int, 7.0::numeric, 690, 2021, 2025, TRUE, 'Standvirtual 2026-11-13: 14 anúncios; consumo: CO2 declarado em 3 anúncios', 14),
    ('Volvo', 'V90', '2.0 B4 197cv', 'diesel', 1969::int, 197, 'auto 8', 6.2::numeric, 164::int, 7.5::numeric, 540, 2021, 2022, FALSE, 'Standvirtual 2026-11-13: 7 anúncios; consumo: CO2 declarado em 3 anúncios', 7),
    ('Volvo', 'V90', '2.0 T8 PHEV 391cv', 'hibrido', 1969::int, 391, 'auto 8', 2.0::numeric, 46::int, 7.0::numeric, 730, 2018, 2021, TRUE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 3 anúncios', 5),
    ('Volvo', 'V90', '2.0 B5 235cv', 'diesel', 1969::int, 235, 'auto 8', 5.7::numeric, 150::int, 7.5::numeric, 580, 2016, 2022, FALSE, 'Standvirtual 2026-11-13: 5 anúncios; consumo: CO2 declarado em 2 anúncios', 5),
    ('Volvo', 'XC90', '2.0 T8 PHEV 455cv', 'hibrido', 1969::int, 455, 'auto 8', 1.5::numeric, NULL::int, 7.0::numeric, 740, 2022, 2025, TRUE, 'Standvirtual 2026-11-13: 59 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 59),
    ('Volvo', 'XC90', '2.0 D4 190cv', 'diesel', 1969::int, 190, 'auto 8', 5.2::numeric, 136::int, 7.5::numeric, 530, 2016, 2018, FALSE, 'Standvirtual 2026-11-13: 30 anúncios; consumo: CO2 declarado em 2 anúncios', 30),
    ('Volvo', 'XC90', '2.0 T8 PHEV 391cv', 'hibrido', 1969::int, 391, 'auto 8', 1.5::numeric, NULL::int, 7.0::numeric, 730, 2018, 2022, TRUE, 'Standvirtual 2026-11-13: 24 anúncios; consumo: estimativa: mediana dos plug-in do catálogo', 24)
) AS v(brand, model, code, fuel_type, displacement_cc, power_hp, transmission,
       consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year,
       year_from, year_to, plug_in, source, listings_seen)
JOIN brands b ON b.name = v.brand
JOIN vehicle_models vm ON vm.brand_id = b.id AND vm.name = v.model
WHERE NOT EXISTS (SELECT 1 FROM engines e WHERE e.model_id = vm.id AND e.code = v.code);

INSERT INTO driving_character
    (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score,
     noise_level, description)
SELECT vm.id, v.comfort, v.fun, v.city, v.highway, v.family, v.noise, v.description
FROM (VALUES
    ('Alfa Romeo', 'Stelvio', 7, 9, 5, 8, 7, 'medio', 'O SUV para quem gosta de conduzir. Direção rápida e chassis de berlina desportiva. Interior e eletrónica abaixo dos rivais alemães.'),
    ('Audi', 'A5', 8, 7, 6, 9, 5, 'baixo', 'A4 com linha de coupé. O Sportback junta estilo e uma mala prática. Refinado em viagem, bancos traseiros mais justos.'),
    ('Audi', 'A6', 9, 6, 5, 10, 6, 'baixo', 'Berlina de estrada por excelência. Silêncio e conforto para grandes distâncias. Interior tecnológico. A Avant é das carrinhas mais completas.'),
    ('Audi', 'Q3', 8, 6, 7, 8, 7, 'baixo', 'SUV compacto premium com espaço honesto. Banco traseiro deslizante e boa mala. Qualidade Audi, condução fácil e segura.'),
    ('Audi', 'Q7', 9, 6, 4, 10, 10, 'baixo', 'SUV grande de sete lugares. Conforto de topo com suspensão pneumática. Enorme para a cidade, feito para a estrada e para a família.'),
    ('Audi', 'Q8', 9, 7, 4, 10, 7, 'baixo', 'Q7 com perfil de coupé e cinco lugares. Presença forte e interior de luxo. Custos de utilização a condizer.'),
    ('Audi', 'TT', 6, 8, 7, 7, 2, 'medio', 'Coupé de design marcante. Ágil e fácil de conduzir depressa. Bancos traseiros simbólicos, mala razoável no coupé.'),
    ('BMW', 'Série 2 Active Tourer', 8, 6, 7, 8, 8, 'baixo', 'O monovolume da BMW. Posição de condução alta, interior espaçoso e modular. Tração dianteira, pensado para a família.'),
    ('BMW', 'Série 4', 7, 9, 6, 9, 4, 'baixo', 'Série 3 em formato coupé. Condução envolvente e tração traseira. O Gran Coupé de quatro portas é o mais prático.'),
    ('BMW', 'Série 5', 9, 8, 5, 10, 6, 'baixo', 'A berlina executiva de referência na condução. Conforto de estrada com dinâmica BMW. A Touring acrescenta uma mala grande.'),
    ('BMW', 'X5', 9, 7, 4, 10, 9, 'baixo', 'SUV grande que se conduz como um BMW. Interior espaçoso e bem construído. Sete lugares em opção. Custos de manutenção elevados.'),
    ('BMW', 'X6', 8, 8, 4, 9, 6, 'baixo', 'X5 com tejadilho de coupé. Mais estilo, menos espaço atrás e na mala. Dinâmica forte para o tamanho.'),
    ('BMW', 'Z4', 6, 9, 6, 7, 1, 'medio', 'Roadster de dois lugares e tração traseira. Feito para o prazer de conduzir. Mala pequena, utilização de segundo carro.'),
    ('BYD', 'Atto 3', 7, 5, 8, 6, 7, 'baixo', 'SUV elétrico compacto com muito equipamento de série. Suspensão macia e condução descontraída. Interior original. Marca recente em Portugal.'),
    ('BYD', 'Dolphin', 7, 4, 9, 5, 5, 'baixo', 'Elétrico compacto acessível. Espaçoso por dentro para o tamanho. Pensado para a cidade e percursos diários.'),
    ('BYD', 'Seal', 8, 7, 6, 8, 5, 'baixo', 'Berlina elétrica rival do Model 3. Boa autonomia e condução equilibrada. Interior bem acabado. Rede de assistência ainda em crescimento.'),
    ('Citroën', 'Berlingo', 7, 3, 7, 6, 10, 'medio', 'Espaço e praticidade acima de tudo. Portas laterais de correr, mala enorme, três bancos individuais atrás. Sem pretensões, muito útil.'),
    ('Cupra', 'Ateca', 6, 8, 6, 8, 7, 'medio', 'SUV familiar com motor de desportivo. Rápido e com tração integral. Suspensão firme, consumos a condizer.'),
    ('DS', '7', 9, 5, 6, 8, 7, 'baixo', 'SUV francês virado para o conforto. Interior distinto, com materiais cuidados. Suspensão suave. Valor de revenda abaixo dos alemães.'),
    ('Fiat', '500X', 6, 5, 8, 6, 5, 'medio', 'O estilo do 500 num crossover. Posição de condução alta e fácil na cidade. Mala modesta para o segmento.'),
    ('Ford', 'S-Max', 8, 7, 5, 9, 10, 'baixo', 'O monovolume de sete lugares que se conduz bem. Espaçoso e confortável em viagem. Já não é produzido: só em usados.'),
    ('Ford', 'Tourneo Connect', 7, 4, 7, 7, 10, 'medio', 'Furgão de passageiros prático. Portas de correr e muito espaço para pessoas e bagagem. A geração atual partilha a base com o Volkswagen Caddy.'),
    ('Honda', 'e:Ny1', 7, 5, 8, 6, 6, 'baixo', 'SUV elétrico compacto da Honda. Condução suave e interior simples com ecrã grande. Mala pequena para o segmento.'),
    ('Hyundai', 'Ioniq', 7, 4, 8, 7, 6, 'baixo', 'Feito para gastar pouco: híbrido, plug-in ou elétrico. Aerodinâmico e fácil de conduzir. Sem emoção, com custos baixos.'),
    ('Hyundai', 'Ioniq 6', 8, 6, 6, 9, 5, 'baixo', 'Berlina elétrica muito aerodinâmica. Grande autonomia e carregamento rápido a 800 V. Tejadilho baixo limita o espaço atrás.'),
    ('Jaguar', 'E-Pace', 7, 6, 6, 7, 6, 'medio', 'SUV compacto com estilo Jaguar. Agradável de conduzir, mas pesado para o tamanho. Espaço e consumos atrás dos rivais.'),
    ('Jaguar', 'F-Pace', 8, 8, 5, 9, 7, 'baixo', 'SUV com condução de desportivo. Direção precisa e bom espaço interior. Custos de manutenção de marca premium.'),
    ('Jeep', 'Avenger', 7, 5, 9, 6, 5, 'medio', 'O Jeep mais pequeno. Compacto, alto e fácil na cidade. Disponível a gasolina, híbrido e elétrico. Espaço atrás limitado.'),
    ('Jeep', 'Compass', 7, 4, 6, 7, 7, 'medio', 'SUV familiar com imagem de todo-o-terreno. Posição de condução alta e habitáculo razoável. Versões 4xe com tração integral elétrica.'),
    ('Kia', 'EV3', 8, 5, 8, 7, 7, 'baixo', 'SUV elétrico compacto com autonomia longa na bateria grande. Interior espaçoso e bem pensado. Garantia de sete anos.'),
    ('Land Rover', 'Discovery Sport', 8, 5, 5, 8, 9, 'baixo', 'SUV familiar com capacidade real fora de estrada. Sete lugares em opção. Confortável e versátil. Custos de manutenção elevados.'),
    ('Land Rover', 'Range Rover Evoque', 8, 6, 7, 7, 5, 'baixo', 'O Range Rover compacto. Design e interior de luxo num formato urbano. Espaço atrás e mala modestos. Manutenção cara.'),
    ('Land Rover', 'Range Rover Sport', 9, 7, 4, 10, 8, 'baixo', 'Luxo e desempenho num SUV grande. Conforto de topo em estrada e capacidade fora dela. Custos de utilização muito elevados.'),
    ('Land Rover', 'Range Rover Velar', 9, 6, 5, 9, 6, 'baixo', 'O Range Rover mais elegante. Interior minimalista e silencioso. Mais estilo do que espaço. Manutenção cara.'),
    ('Lexus', 'ES', 10, 4, 5, 9, 6, 'baixo', 'Berlina grande virada para o conforto. Híbrido silencioso e económico. Tração dianteira, condução serena. Fiabilidade Toyota.'),
    ('Lexus', 'IS', 8, 6, 6, 8, 4, 'baixo', 'Alternativa japonesa às berlinas alemãs. Tração traseira e híbrido suave. Muito fiável. Espaço atrás e mala reduzidos.'),
    ('Lexus', 'RX', 10, 5, 5, 9, 8, 'baixo', 'SUV grande de luxo, híbrido em quase todas as versões. Silêncio e conforto de referência. Construção cuidada e fiabilidade muito alta.'),
    ('Lexus', 'UX', 8, 5, 8, 7, 4, 'baixo', 'Crossover premium compacto e híbrido. Económico e fácil na cidade. Mala e bancos traseiros pequenos.'),
    ('MG', '5', 7, 4, 6, 7, 8, 'baixo', 'Carrinha elétrica, um formato raro. Mala prática e preço baixo para um elétrico. Interior simples.'),
    ('MG', 'HS', 7, 4, 6, 7, 8, 'medio', 'SUV familiar grande pelo preço de um compacto. Muito equipamento de série. Condução sem brilho. O plug-in tem boa autonomia elétrica.'),
    ('MG', 'ZS EV', 7, 4, 8, 6, 7, 'baixo', 'SUV elétrico entre os mais acessíveis. Espaçoso e simples de usar. Carregamento rápido modesto.'),
    ('MINI', 'Clubman', 7, 8, 7, 7, 5, 'medio', 'O MINI em formato de carrinha, com portas traseiras de abrir ao meio. Divertido e mais prático que o hatch. Já fora de produção.'),
    ('MINI', 'Countryman', 7, 7, 7, 8, 7, 'medio', 'O MINI familiar. Posição alta, espaço para quatro adultos e condução ágil. A geração de 2023 cresceu bastante.'),
    ('Maserati', 'Grecale', 8, 8, 5, 9, 7, 'baixo', 'SUV italiano de luxo. Condução desportiva e interior distinto. Exclusividade com custos de manutenção muito altos.'),
    ('Mercedes-Benz', 'CLE', 8, 7, 5, 9, 3, 'baixo', 'Coupé de quatro lugares que substituiu os Classe C e E Coupé. Elegante e confortável em viagem. Bancos traseiros para uso ocasional.'),
    ('Mercedes-Benz', 'Classe B', 8, 5, 7, 8, 8, 'baixo', 'Classe A com mais altura e espaço. Acesso fácil, boa visibilidade e mala prática. Interior MBUX. Escolha racional.'),
    ('Mercedes-Benz', 'Classe E', 10, 6, 5, 10, 6, 'baixo', 'A berlina executiva de referência em conforto. Feita para muitos quilómetros. Diesel muito eficiente. A Station tem uma das maiores malas.'),
    ('Mercedes-Benz', 'Classe V', 9, 3, 3, 8, 10, 'baixo', 'Monovolume de luxo com até oito lugares. Espaço de carrinha comercial com acabamento Mercedes. Grande para a cidade.'),
    ('Mercedes-Benz', 'E Coupé', 9, 6, 5, 9, 3, 'baixo', 'Coupé grande e elegante, sem pilar central. Conforto de Classe E para dois, mais dois atrás. Viajante por natureza.'),
    ('Mercedes-Benz', 'GLE', 9, 6, 4, 10, 9, 'baixo', 'SUV grande de luxo. Muito espaço, sete lugares em opção. Conforto em estrada de topo. Plug-in a gasóleo com grande autonomia elétrica.'),
    ('Mercedes-Benz', 'GLS', 10, 5, 3, 10, 10, 'baixo', 'O Classe S dos SUV. Sete lugares de adulto e suspensão pneumática. Enorme e caro de manter.'),
    ('Omoda', '5', 7, 4, 7, 6, 6, 'medio', 'SUV compacto de uma marca chinesa recente. Muito equipamento pelo preço. Rede de assistência e valor de revenda ainda por provar.'),
    ('Opel', 'Combo Life', 7, 3, 7, 6, 10, 'medio', 'Irmão do Berlingo e do Rifter. Portas de correr, mala enorme e versão de sete lugares. Funcional acima de tudo.'),
    ('Peugeot', 'E-308', 8, 6, 8, 7, 5, 'baixo', 'O 308 em versão elétrica. Mantém o conforto e o interior i-Cockpit. Autonomia média para o segmento.'),
    ('Peugeot', 'Rifter', 7, 4, 7, 6, 10, 'medio', 'O Berlingo com estilo Peugeot e i-Cockpit. Espaço enorme e portas de correr. Ideal para famílias com muita bagagem.'),
    ('Porsche', 'Panamera', 9, 9, 4, 10, 5, 'baixo', 'Berlina de luxo que se conduz como um desportivo. Quatro lugares a sério. Custos de compra e manutenção muito elevados.'),
    ('Renault', '5 E-Tech', 7, 7, 10, 6, 4, 'baixo', 'Citadino elétrico com estilo retro. Ágil e divertido na cidade. Espaço atrás limitado.'),
    ('Renault', 'Scénic', 8, 5, 7, 8, 8, 'baixo', 'Desde 2024 é um SUV familiar elétrico, com boa autonomia e espaço. As gerações anteriores são monovolumes práticos a gasolina e gasóleo.'),
    ('SEAT', 'Alhambra', 8, 4, 4, 8, 10, 'baixo', 'Monovolume de sete lugares com portas de correr. Gémeo do Volkswagen Sharan. Espaço real para sete. Só em usados.'),
    ('Skoda', 'Superb Combi', 9, 5, 5, 10, 10, 'baixo', 'Uma das maiores malas do mercado. Espaço para as pernas de classe superior. Confortável e racional. Imbatível em espaço pelo preço.'),
    ('Smart', '#1', 7, 6, 8, 6, 6, 'baixo', 'O novo Smart é um SUV elétrico compacto. Interior espaçoso e bem acabado. Rápido, com autonomia média.'),
    ('Smart', '#3', 7, 7, 7, 7, 5, 'baixo', 'Versão coupé do #1, mais baixa e aerodinâmica. Condução mais desportiva. Menos altura atrás.'),
    ('Subaru', 'Forester', 8, 4, 6, 7, 8, 'medio', 'SUV com tração integral permanente e boa visibilidade. Robusto e capaz fora de estrada. Motor sem pressa, consumos acima da média.'),
    ('Subaru', 'Outback', 8, 4, 5, 8, 9, 'medio', 'Carrinha elevada com tração integral. Grande mala e conforto em mau piso. Raro em Portugal.'),
    ('Tesla', 'Model S', 8, 8, 5, 10, 7, 'baixo', 'A berlina elétrica que abriu caminho. Grande autonomia, aceleração forte e rede Supercharger. Mala enorme com portão traseiro.'),
    ('Toyota', 'Proace City Verso', 7, 3, 7, 6, 10, 'medio', 'A versão Toyota do Berlingo, com garantia Toyota. Portas de correr e muito espaço. Prático e sem luxos.'),
    ('Volkswagen', 'Caddy', 7, 4, 7, 7, 10, 'medio', 'Furgão de passageiros com base de Golf na geração atual. Portas de correr, sete lugares em opção. Sólido e funcional.'),
    ('Volkswagen', 'Sharan', 8, 4, 4, 8, 10, 'baixo', 'Monovolume de sete lugares com portas de correr. Espaçoso e confortável em viagem. Só em usados.'),
    ('Volkswagen', 'Touran', 8, 5, 6, 8, 10, 'baixo', 'Monovolume compacto de sete lugares com base de Golf. Modular e fácil de conduzir. Uma das escolhas mais racionais para famílias.'),
    ('Volvo', 'S90', 10, 5, 4, 10, 6, 'baixo', 'Berlina grande de desenho escandinavo. Bancos entre os melhores do mercado. Serena em viagem.'),
    ('Volvo', 'V90', 10, 5, 4, 10, 8, 'baixo', 'Carrinha grande e elegante. Conforto e segurança Volvo. Mala menor do que o tamanho sugere.'),
    ('Volvo', 'XC90', 9, 5, 4, 9, 10, 'baixo', 'SUV de sete lugares de referência em segurança. Interior acolhedor e intemporal. O plug-in T8 junta potência e autonomia elétrica.')
) AS v(brand, model, comfort, fun, city, highway, family, noise, description)
JOIN brands b ON b.name = v.brand
JOIN vehicle_models vm ON vm.brand_id = b.id AND vm.name = v.model
WHERE NOT EXISTS (SELECT 1 FROM driving_character dc WHERE dc.model_id = vm.id);

COMMIT;

-- Verify: models still without an engine or without character scores.
SELECT b.name AS brand, vm.name AS model,
       (SELECT COUNT(*) FROM engines e WHERE e.model_id = vm.id) AS engines,
       EXISTS (SELECT 1 FROM driving_character dc WHERE dc.model_id = vm.id) AS has_character
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE NOT EXISTS (SELECT 1 FROM engines e WHERE e.model_id = vm.id)
   OR NOT EXISTS (SELECT 1 FROM driving_character dc WHERE dc.model_id = vm.id)
ORDER BY 1, 2;
