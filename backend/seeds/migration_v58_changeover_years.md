# Migration v5.8 — changeover years

Companion to `migration_v58_changeover_years.sql`. **Applied to production on 2026-11-13.**

Consecutive generations of a model shared their boundary year (Clio IV 2012–2019, Clio V 2019–now). The lookup returns the newest row containing the car's year, so every car registered in a changeover year was treated as the newer generation and priced against it.

129 changeover pairs resolved with 132 single-column updates (29 end years, 103 start years), plus one end year for the Volvo S60. No row is inserted or deleted; nothing that references `generations.id` changes.

## Rule

The changeover year goes to the generation on sale for most of it:

- new generation with customers in the **first half** of the year: the older row ends a year earlier;
- **second half**, or the following year: the newer row starts a year later.

"On sale" means cars at dealers or delivered, not the reveal or the opening of order books. Where a source gives only the start of production, the decision is taken only if that already settles it (production starting in July or later cannot mean first-half deliveries). German dealer dates are used as the European date when nothing broader is stated.

⚠ marks a June launch: a close call under this rule. Giving these years to the older generation instead is a defensible alternative.

## Pairs

Numbers in brackets are generation ids. Windows shown are after the migration.

| Model | Older generation | Newer generation | Newer generation reached customers |
|---|---|---|---|
| Audi A1 | A1 8X (109) 2010–2018 | A1 GB (108) 2019–now | late 2018 (production from October 2018) — [Wikipedia](https://en.wikipedia.org/wiki/Audi_A1) |
| Audi A3 | A3 8P (81) 2003–2012 | A3 8V (80) 2013–2019 | September 2012 — [Wikipedia](https://en.wikipedia.org/wiki/Audi_A3) |
| Audi A3 | A3 8V (80) 2013–2019 | A3 8Y (79) 2020–now | early May 2020 — [Audi](https://www.audi.com/en/more-dynamic-than-ever-the-new-audi-a3-sportback-2020-12699/market-launch-and-special-edition-model-12709) |
| Audi A4 | B8 (197) 2007–2015 | B9 (196) 2016–2024 | autumn 2015 (production from October 2015) — [Carsession](https://www.carsession.com/car-news/2015-audi-a4-starts-from-30-650-euros) |
| Audi A5 | A5 8T (326) 2007–2016 | A5 F5 (325) 2017–2024 | unveiled June 2016, so on sale in the second half at the earliest — [Wikipedia](https://en.wikipedia.org/wiki/Audi_A5) |
| Audi A6 | C7 (212) 2011–2017 | C8 (211) 2018–2024 | June 2018 ⚠ — [Wikipedia](https://de.wikipedia.org/wiki/Audi_A6) |
| Audi Q3 | Q3 8U (222) 2011–2018 | Q3 F3 (221) 2019–2025 | unveiled 25 July 2018, production from August 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Audi_Q3) |
| Audi Q5 | Q5 8R (229) 2008–2016 | Q5 FY (228) 2017–2024 | production from 30 September 2016 — [Wikipedia](https://en.wikipedia.org/wiki/Audi_Q5) |
| Audi Q7 | Q7 4L (261) 2005–2014 | Q7 4M (260) 2015–now | June 2015 ⚠ — [Automotive World](https://www.automotiveworld.com/news-releases/audi-ag-first-time-900000-customers-initial-half-year/) |
| Audi TT | TT 8J (323) 2006–2014 | TT 8S (322) 2015–2023 | production from July 2014 — [Wikipedia](https://de.wikipedia.org/wiki/Audi_TT) |
| BMW Série 1 | E87 (84) 2004–2011 | F20 (83) 2012–2019 | 17 September 2011 — [Wikipedia](https://de.wikipedia.org/wiki/BMW_F20) |
| BMW Série 1 | F20 (83) 2012–2019 | F40 (82) 2020–2024 | 28 September 2019 — [Wikipedia](https://en.wikipedia.org/wiki/BMW_1_Series_(F40)) |
| BMW Série 2 Active Tourer | F45 (295) 2014–2021 | U06 (294) 2022–now | February 2022 — [Wikipedia](https://de.wikipedia.org/wiki/BMW_2er_Active_Tourer) |
| BMW Série 4 | F32 (314) 2013–2020 | G22 (313) 2021–now | 24 October 2020 — [Wikipedia](https://de.wikipedia.org/wiki/BMW_G22) |
| BMW X1 | X1 E84 (185) 2009–2015 | X1 F48 (184) 2016–2022 | 24 October 2015 — [BMW Group](https://www.press.bmwgroup.com/united-kingdom/article/detail/T0235146EN_GB/the-new-bmw-x1) |
| BMW X1 | X1 F48 (184) 2016–2022 | X1 U11 (183) 2023–now | late 2022 (production from October 2022) — [Wikipedia](https://en.wikipedia.org/wiki/BMW_X1_(U11)) |
| BMW X3 | X3 E83 (225) 2003–2010 | X3 F25 (224) 2011–2017 | November 2010 — [Wikipedia](https://en.wikipedia.org/wiki/BMW_X3) |
| BMW X3 | X3 F25 (224) 2011–2017 | X3 G01 (223) 2018–2024 | 11 November 2017 — [Wikipedia](https://de.wikipedia.org/wiki/BMW_G01) |
| BMW X5 | X5 E70 (252) 2006–2013 | X5 F15 (251) 2014–2018 | 16 November 2013 — [Openers](https://openers.jp/en/car/car_news/19164) |
| BMW X5 | X5 F15 (251) 2014–2018 | X5 G05 (250) 2019–now | November 2018 — [Wikipedia](https://en.wikipedia.org/wiki/BMW_X5_(G05)) |
| BMW X6 | X6 E71 (255) 2008–2014 | X6 F16 (254) 2015–2019 | end of 2014 — [Wikipedia](https://en.wikipedia.org/wiki/BMW_X6_(F16)) |
| BMW X6 | X6 F16 (254) 2015–2019 | X6 G06 (253) 2020–now | November 2019 — [Wikipedia](https://en.wikipedia.org/wiki/BMW_X6) |
| Citroën Berlingo | Berlingo II (277) 2008–2018 | Berlingo III (276) 2019–now | summer 2018 — [Wikipedia](https://fr.wikipedia.org/wiki/Citro%C3%ABn_Berlingo) |
| Citroën C1 | C1 I (48) 2005–2014 | C1 II (47) 2015–2022 | July 2014 — [Auto Express](https://www.autoexpress.co.uk/citroen/c1/85872/citroen-c1-2014-price-specs-and-sale-date) |
| Citroën C3 | C3 II (7) 2009–2016 | C3 III (6) 2017–2024 | November 2016 — [Wikipedia](https://fr.wikipedia.org/wiki/Citro%C3%ABn_C3) |
| Cupra Leon | Leon I (91) 2014–2020 | Leon II (90) 2021–now | revealed February 2020, deliveries from late 2020 — [Autocar](https://www.autocar.co.uk/car-news/new-cars/cupra-top-new-leon-line-241bhp-phev) |
| Dacia Duster | Duster I (126) 2010–2017 | Duster II (125) 2018–2023 | November 2017 in Romania, January 2018 elsewhere — [Wikipedia](https://en.wikipedia.org/wiki/Dacia_Duster) |
| Dacia Sandero | Sandero I (10) 2008–2012 | Sandero II (9) 2013–2020 | orders from October 2012 — [Wikipedia](https://en.wikipedia.org/wiki/Dacia_Sandero) |
| Ford Fiesta | Fiesta VI (29) 2008–2017 | Fiesta VII (28) 2018–2023 | 8 July 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Ford_Fiesta_%E2%80%9918) |
| Ford Focus | Focus III (66) 2010–2018 | Focus IV (65) 2019–2025 | September 2018 — [Wikipedia](https://de.wikipedia.org/wiki/Ford_Focus_%2718) |
| Ford Kuga | Kuga II (153) 2012–2019 | Kuga III (152) 2020–now | orders September 2019, deliveries April 2020 — [Wikipedia](https://de.wikipedia.org/wiki/Ford_Kuga) |
| Ford Mustang | Mustang VI (329) 2015–2023 | Mustang VII (328) 2024–now | US production from May 2023; Europe in 2024 — [Wikipedia](https://en.wikipedia.org/wiki/Ford_Mustang_(seventh_generation)) |
| Honda CR-V | CR-V IV (170) 2012–2018 | CR-V V (169) 2019–2023 | September 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Honda_CR-V_(fifth_generation)) |
| Honda CR-V | CR-V V (169) 2019–2023 | CR-V VI (168) 2024–now | August 2023 — [Wikipedia](https://en.wikipedia.org/wiki/Honda_CR-V_(sixth_generation)) |
| Honda Civic | Civic IX (78) 2011–2016 | Civic X (77) 2017–2022 | 18 March 2017 in Europe (the table had US dates) — [Wikipedia](https://de.wikipedia.org/wiki/Honda_Civic_10._Generation) |
| Honda Civic | Civic X (77) 2017–2022 | Civic XI (76) 2023–now | August 2022 in Europe (the table had US dates) — [Wikipedia](https://en.wikipedia.org/wiki/Honda_Civic_(eleventh_generation)) |
| Honda HR-V | HR-V I (167) 2015–2021 | HR-V II (166) 2022–now | September 2021 — [Wikipedia](https://de.wikipedia.org/wiki/Honda_HR-V) |
| Honda Jazz | Jazz III (34) 2015–2019 | Jazz IV (33) 2020–now | June 2020 ⚠ — [Wikipedia](https://en.wikipedia.org/wiki/Honda_Fit) |
| Hyundai Tucson | Tucson III (134) 2015–2020 | Tucson IV (133) 2021–now | end of 2020 — [Wikipedia](https://de.wikipedia.org/wiki/Hyundai_Tucson) |
| Hyundai i10 | i10 I (41) 2007–2013 | i10 II (40) 2014–2019 | November 2013 in Germany, January 2014 elsewhere — [Wikipedia](https://en.wikipedia.org/wiki/Hyundai_i10) |
| Hyundai i10 | i10 II (40) 2014–2019 | i10 III (39) 2020–now | December 2019 (production from January 2020) — [Wikipedia](https://de.wikipedia.org/wiki/Hyundai_i10) |
| Hyundai i20 | i20 I (25) 2008–2014 | i20 II (24) 2015–2020 | November 2014 — [Wikipedia](https://en.wikipedia.org/wiki/Hyundai_i20) |
| Hyundai i20 | i20 II (24) 2015–2020 | i20 III (23) 2021–now | August 2020 — [Wikipedia](https://de.wikipedia.org/wiki/Hyundai_i20) |
| Hyundai i30 | i30 II (71) 2011–2016 | i30 III (70) 2017–now | January 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Hyundai_i30) |
| Kia Ceed | Ceed II (73) 2012–2017 | Ceed III (72) 2018–2025 | June 2018 ⚠ — [Wikipedia](https://en.wikipedia.org/wiki/Kia_Ceed) |
| Kia Niro | Niro I (161) 2016–2021 | Niro II (160) 2022–now | June 2022 ⚠ — [Wikipedia](https://de.wikipedia.org/wiki/Kia_Niro) |
| Kia Picanto | Picanto II (43) 2011–2016 | Picanto III (42) 2017–now | from the start of the second quarter of 2017 — [Kia](https://press.kia.com/ie/en/home/media-resouces/press-releases/2017/17_02_16_all-new_picanto_press_kit.html) |
| Kia Rio | Rio III (27) 2011–2016 | Rio IV (26) 2017–2023 | 11 February 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Kia_Rio) |
| Kia Sportage | Sportage III (137) 2010–2015 | Sportage IV (136) 2016–2021 | shown September 2015, on sale 2016 — [Wikipedia](https://en.wikipedia.org/wiki/Kia_Sportage) |
| Kia Sportage | Sportage IV (136) 2016–2021 | Sportage V (135) 2022–now | end of January 2022 — [Wikipedia](https://de.wikipedia.org/wiki/Kia_Sportage) |
| Land Rover Range Rover Sport | Sport I (243) 2005–2013 | Sport II (242) 2014–2022 | 20 September 2013 — [Wikipedia](https://de.wikipedia.org/wiki/Range_Rover_Sport) |
| Land Rover Range Rover Sport | Sport II (242) 2014–2022 | Sport III (241) 2023–now | September 2022 — [Wikipedia](https://de.wikipedia.org/wiki/Range_Rover_Sport) |
| Lexus NX | NX I (237) 2014–2021 | NX II (236) 2022–now | November 2021 — [Wikipedia](https://de.wikipedia.org/wiki/Lexus_NX) |
| Lexus RX | RX IV (270) 2015–2022 | RX V (269) 2023–now | unveiled May 2022, production from October 2022 — [Wikipedia](https://en.wikipedia.org/wiki/Lexus_RX) |
| MINI Clubman | R55 (332) 2007–2015 | F54 (331) 2016–2024 | production from October 2015 — [Wikipedia](https://en.wikipedia.org/wiki/Mini_Clubman_(2007)) |
| MINI Cooper | R56 (107) 2006–2013 | F56 (106) 2014–2023 | production from November 2013 — [Wikipedia](https://en.wikipedia.org/wiki/Mini_Hatch) |
| MINI Countryman | R60 (335) 2010–2016 | F60 (334) 2017–2023 | February 2017 — [Wikipedia](https://en.wikipedia.org/wiki/Mini_Countryman) |
| MINI Countryman | F60 (334) 2017–2023 | U25 (333) 2024–now | 17 February 2024 — [Wikipedia](https://de.wikipedia.org/wiki/Mini_Countryman) |
| Mazda 3 | Mazda 3 III (75) 2013–2018 | Mazda 3 IV (74) 2019–now | March 2019 — [Wikipedia](https://de.wikipedia.org/wiki/Mazda3) |
| Mazda CX-5 | CX-5 I (165) 2012–2016 | CX-5 II (164) 2017–2025 | 20 May 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Mazda_CX-5) |
| Mazda MX-5 | MX-5 NC (321) 2005–2015 | MX-5 ND (320) 2016–now | 12 September 2015 — [Wikipedia](https://de.wikipedia.org/wiki/Mazda_MX-5_ND) |
| Mercedes-Benz CLA | C117 (111) 2013–2018 | C118 (110) 2019–2025 | production from February 2019; May 2019 launch is from general knowledge — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_CLA) |
| Mercedes-Benz Classe A | W168 (88) 1997–2004 | W169 (87) 2005–2012 | October 2004 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_A-Klasse) |
| Mercedes-Benz Classe A | W169 (87) 2005–2012 | W176 (86) 2013–2017 | 15 September 2012 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_W_176) |
| Mercedes-Benz Classe A | W176 (86) 2013–2017 | W177 (85) 2018–now | orders March 2018, production from April 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_A-Class_(W177)) |
| Mercedes-Benz Classe B | W245 (220) 2005–2011 | W246 (219) 2012–2018 | November 2011 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_B-Class_(W246)) |
| Mercedes-Benz Classe B | W246 (219) 2012–2018 | W247 (218) 2019–now | production from December 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_B-Class) |
| Mercedes-Benz Classe C | W203 (195) 2000–2006 | W204 (194) 2007–2013 | late March 2007 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_C-Class_(W204)) |
| Mercedes-Benz Classe C | W204 (194) 2007–2013 | W205 (193) 2014–2020 | March 2014 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_C-Class_(W205)) |
| Mercedes-Benz Classe C | W205 (193) 2014–2020 | W206 (192) 2021–now | orders from 30 March 2021 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_Baureihe_206) |
| Mercedes-Benz Classe E | W211 (210) 2002–2008 | W212 (209) 2009–2015 | March 2009 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_E-Class_(W212)) |
| Mercedes-Benz Classe E | W212 (209) 2009–2015 | W213 (208) 2016–2023 | April 2016 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_Baureihe_213) |
| Mercedes-Benz Classe E | W213 (208) 2016–2023 | W214 (207) 2024–now | summer 2023 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_Baureihe_214) |
| Mercedes-Benz E Coupé | C207 (354) 2009–2016 | C238 (353) 2017–2023 | spring 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Mercedes-Benz_Baureihe_213) |
| Mercedes-Benz GLC | GLC X253 (227) 2015–2022 | GLC X254 (226) 2023–now | revealed 1 June 2022, so on sale in the second half at the earliest (from general knowledge) — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_GLC) |
| Mercedes-Benz GLE | GLE W166 (257) 2015–2018 | GLE V167 (256) 2019–now | production from October 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_GLE) |
| Mercedes-Benz GLS | GLS X166 (259) 2015–2019 | GLS X167 (258) 2020–now | end of 2019 — [Wikipedia](https://en.wikipedia.org/wiki/Mercedes-Benz_GLS_(X167)) |
| Nissan Juke | Juke I (155) 2010–2019 | Juke II (154) 2020–now | late November 2019 — [Wikipedia](https://en.wikipedia.org/wiki/Nissan_Juke) |
| Nissan Micra | Micra K13 (31) 2010–2016 | Micra K14 (30) 2017–2023 | March 2017 — [Wikipedia](https://en.wikipedia.org/wiki/Nissan_Micra) |
| Nissan Qashqai | Qashqai I (129) 2006–2013 | Qashqai II (128) 2014–2021 | February 2014 — [Wikipedia](https://en.wikipedia.org/wiki/Nissan_Qashqai) |
| Nissan Qashqai | Qashqai II (128) 2014–2021 | Qashqai III (127) 2022–now | summer 2021 — [Wikipedia](https://de.wikipedia.org/wiki/Nissan_Qashqai) |
| Opel Astra | Astra J (69) 2009–2015 | Astra K (68) 2016–2021 | production from July 2015 — [Wikipedia](https://de.wikipedia.org/wiki/Opel_Astra_K) |
| Opel Astra | Astra K (68) 2016–2021 | Astra L (67) 2022–now | orders from 12 November 2021 — [Wikipedia](https://en.wikipedia.org/wiki/Opel_Astra) |
| Opel Corsa | Corsa D (13) 2006–2014 | Corsa E (12) 2015–2019 | 24 January 2015 — [Wikipedia](https://de.wikipedia.org/wiki/Opel_Corsa_E) |
| Opel Corsa | Corsa E (12) 2015–2019 | Corsa F (11) 2020–now | orders June 2019, production from October 2019 — [Wikipedia](https://de.wikipedia.org/wiki/Opel_Corsa) |
| Opel Grandland | Grandland X (174) 2017–2021 | Grandland (facelift) (173) 2022–2024 | postponed to early 2022 — [Wikipedia](https://de.wikipedia.org/wiki/Opel_Grandland) |
| Peugeot 2008 | 2008 I (121) 2013–2019 | 2008 II (120) 2020–now | February 2020 — [Wikipedia](https://fr.wikipedia.org/wiki/Peugeot_2008_II) |
| Peugeot 208 | 208 I (5) 2012–2019 | 208 II (4) 2020–now | 6 October 2019 — [Wikipedia](https://fr.wikipedia.org/wiki/Peugeot_208_II) |
| Peugeot 3008 | 3008 I (132) 2008–2016 | 3008 II (131) 2017–2023 | late October 2016 — [Wikipedia](https://en.wikipedia.org/wiki/Peugeot_3008) |
| Peugeot 3008 | 3008 II (131) 2017–2023 | 3008 III (130) 2024–now | February 2024 — [Wikipedia](https://en.wikipedia.org/wiki/Peugeot_3008) |
| Peugeot 308 | 308 I (56) 2007–2013 | 308 II (55) 2014–2021 | 12 September 2013 — [Wikipedia](https://fr.wikipedia.org/wiki/Peugeot_308_II) |
| Peugeot 308 | 308 II (55) 2014–2021 | 308 III (54) 2022–now | 29 September 2021 — [Wikipedia](https://en.wikipedia.org/wiki/Peugeot_308) |
| Peugeot 5008 | 5008 I (293) 2009–2016 | 5008 II (292) 2017–2024 | 17 June 2017 ⚠ — [Wikipedia](https://fr.wikipedia.org/wiki/Peugeot_5008_II) |
| Peugeot 508 | 508 I (119) 2010–2018 | 508 II (118) 2019–2025 | September 2018 — [Wikipedia](https://fr.wikipedia.org/wiki/Peugeot_508_II) |
| Porsche Cayenne | Cayenne II (249) 2010–2017 | Cayenne III (248) 2018–now | production from August 2017 — [Wikipedia](https://en.wikipedia.org/wiki/Porsche_Cayenne) |
| Porsche Panamera | Panamera I (272) 2009–2016 | Panamera II (271) 2017–2023 | November 2016 — [Wikipedia](https://de.wikipedia.org/wiki/Porsche_Panamera) |
| Renault Captur | Captur I (123) 2013–2019 | Captur II (122) 2020–now | January 2020 — [Wikipedia](https://fr.wikipedia.org/wiki/Renault_Captur_II) |
| Renault Clio | Clio III (3) 2005–2012 | Clio IV (2) 2013–2019 | 10 October 2012 — [Wikipedia](https://fr.wikipedia.org/wiki/Renault_Clio_IV) |
| Renault Clio | Clio IV (2) 2013–2019 | Clio V (1) 2020–2025 | September 2019 — [Wikipedia](https://de.wikipedia.org/wiki/Renault_Clio) |
| Renault Mégane | Mégane III (58) 2008–2015 | Mégane IV (57) 2016–2022 | production from December 2015, on sale 2016 — [Wikipedia](https://en.wikipedia.org/wiki/Renault_M%C3%A9gane) |
| Renault Scénic | Scénic IV (275) 2016–2023 | Scénic E-Tech (274) 2024–now | spring 2024 — [Wikipedia](https://de.wikipedia.org/wiki/Renault_Sc%C3%A9nic_E-Tech) |
| Renault Twingo | Twingo II (46) 2007–2014 | Twingo III (45) 2015–2022 | September 2014 — [Wikipedia](https://en.wikipedia.org/wiki/Renault_Twingo) |
| SEAT Ibiza | Ibiza IV (19) 2008–2016 | Ibiza V (18) 2017–now | 10 June 2017 ⚠ — [Wikipedia](https://de.wikipedia.org/wiki/Seat_Ibiza) |
| SEAT Leon | Leon III (62) 2012–2019 | Leon IV (61) 2020–now | second quarter of 2020 — [Carscoops](https://carscoops.com/?p=1997252) |
| Skoda Fabia | Fabia II (22) 2007–2014 | Fabia III (21) 2015–2021 | November 2014 — [Wikipedia](https://de.wikipedia.org/wiki/%C5%A0koda_Fabia_III) |
| Skoda Fabia | Fabia III (21) 2015–2021 | Fabia IV (20) 2022–now | September 2021 — [Wikipedia](https://de.wikipedia.org/wiki/%C5%A0koda_Fabia) |
| Skoda Kodiaq | Kodiaq I (150) 2016–2023 | Kodiaq II (149) 2024–now | orders December 2023, production from January 2024 — [Wikipedia](https://de.wikipedia.org/wiki/%C5%A0koda_Kodiaq_II) |
| Skoda Superb | Superb II (114) 2008–2014 | Superb III (113) 2015–2023 | mid-June 2015 ⚠ — [Wikipedia](https://de.wikipedia.org/wiki/%C5%A0koda_Superb_III) |
| Skoda Superb Combi | Superb Combi II (204) 2009–2015 | Superb Combi III (203) 2016–2023 | September 2015 — [Wikipedia](https://en.wikipedia.org/wiki/%C5%A0koda_Superb) |
| Subaru BRZ | BRZ I (347) 2012–2021 | BRZ II (346) 2023–now | offered in Europe from 2023 — [Wikipedia](https://de.wikipedia.org/wiki/Toyota_GT86) |
| Subaru Forester | Forester IV (345) 2012–2018 | Forester V (344) 2019–2024 | June 2019 in central Europe — [Wikipedia](https://de.wikipedia.org/wiki/Subaru_Forester) |
| Subaru Outback | Outback V (343) 2014–2020 | Outback VI (342) 2021–now | April 2021 in Europe — [Wikipedia](https://en.wikipedia.org/wiki/Subaru_Outback) |
| Suzuki S-Cross | S-Cross I (352) 2013–2021 | S-Cross II (351) 2022–now | presented end of November 2021, production from 2022 — [Wikipedia](https://de.wikipedia.org/wiki/Suzuki_S-Cross) |
| Suzuki Swift | Swift IV (349) 2010–2016 | Swift V (348) 2017–2023 | 13 May 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Suzuki_Swift) |
| Tesla Model 3 | Model 3 (216) 2017–2023 | Model 3 Highland (215) 2024–now | October 2023 — [Wikipedia](https://en.wikipedia.org/wiki/Tesla_Model_3) |
| Toyota C-HR | C-HR I (142) 2016–2023 | C-HR II (141) 2024–now | production from October 2023 — [Wikipedia](https://en.wikipedia.org/wiki/Toyota_C-HR) |
| Toyota Corolla | E170 (60) 2013–2018 | E210 (59) 2019–now | March 2019 — [Wikipedia](https://en.wikipedia.org/wiki/Toyota_Corolla_(E210)) |
| Toyota Prius | Prius IV (102) 2015–2022 | Prius V (101) 2023–now | first quarter of 2023 — [Wikipedia](https://en.wikipedia.org/wiki/Toyota_Prius_(XW60)) |
| Toyota RAV4 | RAV4 IV (144) 2012–2018 | RAV4 V (143) 2019–2025 | 26 January 2019 — [Wikipedia](https://de.wikipedia.org/wiki/Toyota_RAV4) |
| Toyota Yaris | Yaris III (15) 2011–2020 | Yaris IV (14) 2021–now | European production from 6 July 2020 — [Wikipedia](https://en.wikipedia.org/wiki/Toyota_Yaris_(XP210)) |
| Volkswagen Golf | Mk6 (53) 2008–2012 | Mk7 (52) 2013–2019 | November 2012 — [Wikipedia](https://en.wikipedia.org/wiki/Volkswagen_Golf_Mk7) |
| Volkswagen Passat | B7 (117) 2010–2014 | B8 (116) 2015–2023 | November 2014 — [Wikipedia](https://en.wikipedia.org/wiki/Volkswagen_Passat_(B8)) |
| Volkswagen Passat | B8 (116) 2015–2023 | B9 (115) 2024–now | February 2024 — [Wikipedia](https://de.wikipedia.org/wiki/VW_Passat_B9) |
| Volkswagen Polo | Polo V (17) 2009–2017 | Polo VI (16) 2018–now | 29 September 2017 — [Wikipedia](https://de.wikipedia.org/wiki/VW_Polo_VI) |
| Volkswagen Tiguan | Tiguan I (140) 2007–2015 | Tiguan II (139) 2016–2023 | January 2016 — [Wikipedia](https://de.wikipedia.org/wiki/VW_Tiguan) |
| Volvo S60 | S60 II (199) 2010–2018 | S60 III (198) 2019–2024 | production from September 2018 in the US; Europe in 2019 — [Wikipedia](https://en.wikipedia.org/wiki/Volvo_S60) |
| Volvo V60 | V60 I (201) 2010–2018 | V60 II (200) 2019–now | July 2018 — [Wikipedia](https://en.wikipedia.org/wiki/Volvo_V60) |
| Volvo XC60 | XC60 I (232) 2008–2017 | XC60 II (231) 2018–now | 15 July 2017 — [Wikipedia](https://de.wikipedia.org/wiki/Volvo_XC60) |
| Volvo XC90 | XC90 I (264) 2002–2014 | XC90 II (263) 2015–now | production from January 2015 — [Wikipedia](https://de.wikipedia.org/wiki/Volvo_XC90) |

## Also closed

| Model | Row | Today | Proposed | Basis |
|---|---|---|---|---|
| Volvo S60 | S60 III (198) | 2018–now | 2019–2024 | Production for Europe ended in 2024 — [Wikipedia](https://en.wikipedia.org/wiki/Volvo_S60) |

## Notes on individual decisions

- **Honda Civic**: the table had US dates. In Europe the ninth generation ran to 2016, the tenth arrived in March 2017 and the eleventh in August 2022, so those rows move by more than one year.
- **Subaru Outback and BRZ**: same — the sixth-generation Outback reached Europe in April 2021 and the second-generation BRZ in 2023. 2022 has no BRZ row because none was sold.
- **Renault Mégane IV**: Wikipedia's "sales from July 2016" is the UK date; production started in December 2015 and the car was on sale on the continent in early 2016 (from general knowledge).
- **Renault Clio V**: on sale in France from mid-2019 and in most other markets, Portugal included, from September 2019.
- **Toyota Yaris IV and Opel Corsa F**: order books opened in June of the changeover year, but European production only began in July and October respectively.
- **Mercedes CLA C118 and GLC X254**: no source found for the sale month. CLA production began in February 2019 and the car was at dealers in May (general knowledge). The GLC was revealed on 1 June 2022, so it cannot have been on sale in the first half.

## Tested

Run twice against a throwaway local Postgres 18 loaded with a copy of every generation row of the models touched. First run applies every listed update; second run changes nothing. Afterwards no model has overlapping windows except Fiat 500 / 500e (two different cars sold side by side, unchanged) and the one pair left out, and no generation ends before it starts.

## Left out

- **Audi TT 8N → 8J (2006)**: no confirmed sale month; Wikipedia gives the production start as April or August 2006. The two rows still share 2006.
- **DS 7**: still open-ended; no confirmed end date.
- **Fiat 500 / 500e**: the petrol 500 (to 2024) and the electric 500e (from 2020) overlap on purpose. The lookup is fuel-blind, so every 2020-or-later Fiat 500 resolves to the 500e row; fixing that needs a code change, not a data change.
