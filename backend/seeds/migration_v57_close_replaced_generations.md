# Migration v5.7 — close replaced generations

Companion to `migration_v57_close_replaced_generations.sql`. **Not applied to production yet — awaiting approval.**

A read-only audit of all 366 generation rows (2026-11-13) found open-ended rows (`year_end` NULL) whose generation has since been replaced or discontinued. Such a row keeps growing, so a car is priced against its successor — the failure v5.6 fixed for the BMW 530.

39 rows updated, 27 inserted, 49 `reliability_evidence` rows re-pointed.

## Rules

Same as v5.6: windows of one model do not overlap, and a changeover year goes to the generation on sale for most of it (launch in the second half of the year: the outgoing generation keeps that year). The existing row keeps its id, score history and score; successor rows start with no score.

## Part 1a — discontinued, no successor under the same name (7)

| Model | Row | Today | Proposed | Basis |
|---|---|---|---|---|
| Audi A4 | B9 (196) | 2015–now | 2015–2024 | Off sale in 2024, replaced by the A5 — [evo](https://www.evo.co.uk/audi/a4-saloon/15664/audi-a4-b9-2016-2024-review-the-last-a4-for-now) |
| Fiat Tipo | Tipo (95) | 2015–now | 2015–2026 | Last car built 30 June 2026 — [auto motor und sport](https://www.auto-motor-und-sport.de/kompakt/gebrauchtwagenfiat-tipo-produktion-eingestellt-das-ende-fuer-den-letzten-guenstigen-diesel/) |
| Ford Focus | Focus IV (65) | 2018–now | 2018–2025 | Last car built 14 November 2025 — [Motor1](https://www.motor1.com/news/779127/ford-focus-production-ends-official/) |
| Jaguar E-Pace | E-Pace I (267) | 2017–now | 2017–2024 | Graz production ended 2024 — [Electrek](https://electrek.co/2024/07/17/jaguar-to-end-ev-production-magna-steyrtransitions-more-exclusive-luxury-brand/) |
| Kia Ceed | Ceed III (72) | 2018–now | 2018–2025 | Žilina production ended mid-2025 — [Slovak Spectator](https://spectator.sme.sk/business/c/kia-launches-ev-production-in-slovakia-as-ceed-era-ends) |
| Kia Rio | Rio IV (26) | 2017–now | 2017–2023 | Dropped from Europe in 2023 — [Motor1](https://www.motor1.com/news/651665/kia-rio-discontinued-europe/) |
| Peugeot 508 | 508 II (118) | 2018–now | 2018–2025 | Production stopped 12 May 2025 — [Motor1 France](https://fr.motor1.com/news/760776/peugeot-508-fin-production-2025-berline/) |

## Part 1b — replaced (26)

| Model | Existing row closes | New row | Successor reached customers |
|---|---|---|---|
| Audi A5 | A5 F5 (325) 2016–2024 | A5 B10 2025– | November 2024 — [Audi MediaCenter](https://www.audi-mediacenter.com/en/press-releases/new-audi-a5-e-hybrids-combine-dynamics-efficiency-and-long-electric-range-16582) |
| Audi A6 | C8 (211) 2018–2024 | C9 2025– | Avant at dealers 16 May 2025 — [Audi](https://www.audi.com/en/press-releases/nine-generations-of-success-the-new-audi-a6-meets-its-elders-16670) |
| Audi Q3 | Q3 F3 (221) 2018–2025 | Q3 III 2026– | October 2025 — [Autohaus](https://www.autohaus.de/nachrichten/autohersteller/weltpremiere-in-ingolstadt-audi-enthuellt-den-neuen-q3-3677803) |
| Audi Q5 | Q5 FY (228) 2016–2024 | Q5 III 2025– | First quarter of 2025 (planned) — [CarExpert](https://carexpert.com.au/car-news/2025-audi-q5-new-bmw-x3-rival-revealed) |
| BMW Série 1 | F40 (82) 2019–2024 | F70 2025– | October 2024 — [AutoBuzz](https://autobuzz.my/2024/07/02/f70-bmw-1-series-begins-production-market-launch-planned-for-october-2024/) |
| BMW Série 2 Gran Coupé | F44 (112) 2019–2024 | F74 2025– | March 2025 — [BMW Group](https://www.press.bmwgroup.com/global/article/detail/T0447752EN/bmw-model-updates-spring-2025) |
| BMW Série 5 | G30 (205) 2016–now → **2017**–2023 | G60 2024– | October 2023 — same windows as the BMW 530 rows in v5.6 |
| BMW X3 | X3 G01 (223) 2017–2024 | X3 G45 2025– | Fourth quarter of 2024 — [engear](https://en.engear.tv/tag/g45/?amp=1) |
| Citroën C3 | C3 III (6) 2016–2024 | C3 IV 2025– | September–October 2024 — [Passionnément Citroën](https://en.passionnement-citroen.com/post/citroen-c3-2024-successful-launch-november-sales-up-4-in-europe) |
| Citroën C5 Aircross | C5 Aircross I (177) 2018–2025 | C5 Aircross II 2026– | Fourth quarter of 2025 — [Stellantis](https://www.media.stellantis.com/em-en/citroen/press/all-new-c5-aircross-offers-peace-of-mind-with-more-space-comfort-technologies-now-available-in-electric) |
| Jeep Compass | Compass II (337) 2017–2025 | Compass III 2026– | Production from 29 October 2025 — [Stellantis](https://www.media.stellantis.com/uk-en/jeep/press/jeep-launches-production-of-the-all-new-compass-at-stellantis-melfi-plant) |
| Mazda CX-5 | CX-5 II (164) 2017–2025 | CX-5 III 2026– | Early 2026 — [Mazda](https://newsroom.mazda.com/en/publicity/release/2025/202507/250710a.html) |
| Mercedes-Benz CLA | C118 (110) 2019–2025 | CLA III 2026– | C118 left the order books November 2025 — [MBpassion](https://mbpassion.de/2025/11/mehrere-mercedes-baureihen-nun-mehr-bestellbar/) |
| MG HS | MG HS I (301) 2018–2024 | MG HS II 2025– | July 2024 (UK) — [Autocar](https://www.autocar.co.uk/node/148371) |
| Nissan Micra | Micra K14 (30) 2017–2023 | Micra EV 2026– | K14 ended July 2023 — [motor.es](https://www.motor.es/noticias/nissan-micra-cese-produccion-202394693.html); electric Micra deliveries from late 2025 / January 2026 — [Nissan Insider](https://nissaninsider.co.uk/the-all-new-all-electric-nissan-micra-hits-streets-for-the-first-time/). 2024–2025 has no Micra. |
| Opel Grandland | "Grandland II" (173) 2021–now → **Grandland (facelift)** 2021–2024 | Grandland II 2025– | October 2024 — [electrive](https://www.electrive.com/2024/04/23/grandland-world-premiere-opel-completes-its-electric-range). The 2021 row was the facelift of the first generation, not a new one. |
| Peugeot 5008 | 5008 II (292) 2016–2024 | 5008 III 2025– | Autumn 2024 — [Stellantis](https://www.media.stellantis.com/em-en/peugeot/press/new-peugeot-e-5008-class-above-electric-large-suv) |
| Porsche Panamera | Panamera II (271) 2016–2023 | Panamera III 2024– | March 2024 — [Porsche](https://www.porsche.com/stories/mobility/the-new-2024-porsche-panamera) |
| Renault Clio | Clio V (1) 2019–2025 | Clio VI 2026– | January 2026 — [Motors Actu](https://motorsactu.com/renault-clio-6-voici-la-date-des-premieres-livraisons-en-france/) |
| Skoda Superb | Superb III (113) 2015–2023 | Superb IV 2024– | First half of 2024 — [Škoda Storyboard](https://skoda-storyboard.com/en/press-releases/skoda-launches-all-new-superb-production-in-bratislava) |
| Skoda Superb Combi | Superb Combi III (203) 2015–2023 | Superb Combi IV 2024– | as Superb |
| Subaru Forester | Forester V (344) 2018–2024 | Forester VI 2025– | Late 2024 to spring 2025 depending on country — [Fleet News](https://www.fleetnews.co.uk/news/all-new-subaru-forester-to-launch-in-uk-spring-2025) |
| Suzuki Swift | Swift V (348) 2017–2023 | Swift VI 2024– | April 2024 — [MarkLines](https://www.marklines.com/en/news/305220) |
| Toyota RAV4 | RAV4 V (143) 2018–2025 | RAV4 VI 2026– | Spring 2026 — [Automotive World](https://www.automotiveworld.com/news/toyota-launches-sixth-generation-rav4-across-europe/) |
| Volkswagen T-Roc | T-Roc I (138) 2017–2025 | T-Roc II 2026– | November 2025 — [Volkswagen Newsroom](https://www.volkswagen-newsroom.com/en/press-releases/world-premiere-of-the-t-roc-new-generation-of-the-best-seller-is-high-quality-and-innovative-19769) |
| Volkswagen Tiguan | Tiguan II (139) 2016–2023 | Tiguan III 2024– | First quarter of 2024 — [Volkswagen Newsroom](https://www.volkswagen-newsroom.com/en/press-releases/the-new-tiguan-is-now-available-to-order-in-europe-17886) |

## Part 2 — wrong years (4 models)

| Model | Change | Basis |
|---|---|---|
| MINI Cooper | F56 (106) 2013–2022 → 2013–2023; J01 (105) 2023–now → **F66 / J01** 2024–now | F56 built until February–March 2024; new Cooper production from 11 March 2024 — [MotoringFile](https://www.motoringfile.com/2023/05/30/the-f56-mini-end-of-production-dates-and-details/) |
| Porsche Macan | Macan I (247) 2014–2023 → 2014–2024; "Macan II" (246) 2023–now, platform J1 → **Macan Electric** 2025–now, platform PPE | Petrol Macan sold in the EU until the 1 July 2024 cybersecurity deadline — [Auto Express](https://www.autoexpress.co.uk/news/361808/porsche-macan-canned-european-sales-stop-2024). Electric Macan deliveries in autumn 2024 are from general knowledge. |
| Cupra Ateca | Ateca I (234) 2016–now → 2018–now | Cupra became a brand in 2018 and the Ateca was its first car — [Motor1](https://www.motor1.com/news/233864/ateca-suv-cupras-first-model/) |
| Volkswagen Touran | new **Touran I facelift** 2011–2015; Touran II (280) 2015–now → 2016–now | First generation (1T) ran 2003–2015 with a facelift in August 2010; 2011–2014 had no row — [Volkswagen Newsroom](https://www.volkswagen-newsroom.com/en/vehicle-data-touran-1-profile-19720). Second-generation sales from September 2015 are from general knowledge. |

## Evidence that moves (49 rows)

Evidence dated entirely after the old row's new end year follows the successor. Everything else stays where it is, and so do all `reliability_scores_history` rows. `price_observations` and `market_price_stats_history` have no rows for these generations.

| To | Evidence ids |
|---|---|
| Audi A5 B10 | 447, 448, 451, 1334, 3056 |
| Audi A6 C9 | 519, 590, 1335, 3057 |
| Audi Q3 III | 564, 566 |
| Audi Q5 III | 716–721, 2694 |
| BMW X3 G45 | 1454–1466, 1468–1474, 2070 |
| Jeep Compass III | 131 |
| Mercedes CLA III | 102 |
| Nissan Micra EV | 3242 |
| Opel Grandland II | 947 |
| Peugeot 5008 III | 190, 954, 2845, 2854 |
| Porsche Panamera III | 979 |
| Volkswagen Tiguan III | 4763 |

One row ends up outside its generation's window: Audi A4 evidence 399 is a US model-year-2025 complaint and the A4 has no successor row to move to.

## Tested

Run twice against a throwaway local Postgres 18 loaded with a copy of all 75 generation rows of the 37 models touched plus two untouched controls, their 1,490 evidence rows and 174 score rows. First run: 39 rows changed, 27 inserted, 49 evidence rows moved, 36 rows untouched. Second run: no-op. No evidence or score row lost, no overlapping windows, no model with two open-ended rows.

## Left out

- **Volvo S60** and **DS 7**: probably ended, but I could not confirm a European end date.
- **132 changeover years** where two generations share a boundary year and the newer one wins. Needs a launch month per model; separate job.
- **Genuinely long generations** (Volvo XC90, Mazda MX-5, VW up!, about 35 rows): real, and covered by the ±2-year safety net.
- Platform labels: Volkswagen Passat B9 ("MEB hybrid") and Lexus IS ("GA-L") are wrong but cosmetic. New rows for Mazda CX-5 III and MG HS II have no platform label because I am not sure of it.
