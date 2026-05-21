-- Migration v5.1 — Full generations table population
-- Covers all 200 vehicle models in the Caractr database.
-- Each generation has: name (e.g. 'Mk7', 'E90', 'F30'), year_start, year_end (NULL = still in production), platform/chassis code.
-- year_end is NULL for the current production generation.
--
-- Idempotent: clears existing rows and repopulates.
-- Run once after migration_v50_market_upsert.sql.

TRUNCATE TABLE generations RESTART IDENTITY CASCADE;

WITH gen_data (brand, model, name, year_start, year_end, platform) AS (VALUES

  -- ── CITADINOS ─────────────────────────────────────────────────────────────

  -- Renault Clio
  ('Renault',    'Clio',       'Clio III',   2005, 2012, 'B/C'),
  ('Renault',    'Clio',       'Clio IV',    2012, 2019, 'B98'),
  ('Renault',    'Clio',       'Clio V',     2019, NULL, 'CMF-B'),

  -- Peugeot 208
  ('Peugeot',    '208',        '208 I',      2012, 2019, 'PF1'),
  ('Peugeot',    '208',        '208 II',     2019, NULL, 'CMP'),

  -- Citroën C3
  ('Citroen',    'C3',         'C3 II',      2009, 2016, 'PF1'),
  ('Citroen',    'C3',         'C3 III',     2016, NULL, 'CMP'),

  -- Dacia Sandero
  ('Dacia',      'Sandero',    'Sandero I',  2008, 2012, 'B0'),
  ('Dacia',      'Sandero',    'Sandero II', 2012, 2020, 'B0'),
  ('Dacia',      'Sandero',    'Sandero III',2021, NULL, 'CMF-B'),

  -- Opel Corsa
  ('Opel',       'Corsa',      'Corsa D',    2006, 2014, 'Gamma'),
  ('Opel',       'Corsa',      'Corsa E',    2014, 2019, 'Gamma 2'),
  ('Opel',       'Corsa',      'Corsa F',    2019, NULL, 'CMP'),

  -- Toyota Yaris
  ('Toyota',     'Yaris',      'Yaris III',  2011, 2020, 'B'),
  ('Toyota',     'Yaris',      'Yaris IV',   2020, NULL, 'GR'),

  -- Volkswagen Polo
  ('Volkswagen', 'Polo',       'Polo V',     2009, 2017, 'PQ25'),
  ('Volkswagen', 'Polo',       'Polo VI',    2017, NULL, 'MQB A0'),

  -- SEAT Ibiza
  ('SEAT',       'Ibiza',      'Ibiza IV',   2008, 2017, 'PQ25'),
  ('SEAT',       'Ibiza',      'Ibiza V',    2017, NULL, 'MQB A0'),

  -- Skoda Fabia
  ('Skoda',      'Fabia',      'Fabia II',   2007, 2014, 'PQ25'),
  ('Skoda',      'Fabia',      'Fabia III',  2014, 2021, 'PQ25'),
  ('Skoda',      'Fabia',      'Fabia IV',   2021, NULL, 'MQB A0'),

  -- Hyundai i20
  ('Hyundai',    'i20',        'i20 I',      2008, 2014, 'PB'),
  ('Hyundai',    'i20',        'i20 II',     2014, 2020, 'GB'),
  ('Hyundai',    'i20',        'i20 III',    2020, NULL, 'BC3'),

  -- Kia Rio
  ('Kia',        'Rio',        'Rio III',    2011, 2017, 'UB'),
  ('Kia',        'Rio',        'Rio IV',     2017, NULL, 'YB'),

  -- Ford Fiesta
  ('Ford',       'Fiesta',     'Fiesta VI',  2008, 2017, 'B299'),
  ('Ford',       'Fiesta',     'Fiesta VII', 2017, 2023, 'B516'),

  -- Nissan Micra
  ('Nissan',     'Micra',      'Micra K13',  2010, 2017, 'V-platform'),
  ('Nissan',     'Micra',      'Micra K14',  2017, NULL, 'CMF-B'),

  -- Mazda 2
  ('Mazda',      '2',          'Mazda 2 III',2014, NULL, 'SkyActiv'),

  -- Honda Jazz
  ('Honda',      'Jazz',       'Jazz III',   2015, 2020, 'GK'),
  ('Honda',      'Jazz',       'Jazz IV',    2020, NULL, 'GR'),

  -- Fiat 500
  ('Fiat',       '500',        '500 (312)',  2007, 2023, '188/312'),
  ('Fiat',       '500',        '500e',       2020, NULL, 'STLA Small'),

  -- Fiat Panda
  ('Fiat',       'Panda',      'Panda III',  2012, NULL, '188'),

  -- Toyota Aygo X
  ('Toyota',     'Aygo X',     'Aygo X',     2022, NULL, 'GNA'),

  -- Hyundai i10
  ('Hyundai',    'i10',        'i10 I',      2007, 2013, 'PA'),
  ('Hyundai',    'i10',        'i10 II',     2013, 2019, 'BA'),
  ('Hyundai',    'i10',        'i10 III',    2019, NULL, 'AC3'),

  -- Kia Picanto
  ('Kia',        'Picanto',    'Picanto II', 2011, 2017, 'TA'),
  ('Kia',        'Picanto',    'Picanto III',2017, NULL, 'JA'),

  -- Volkswagen up!
  ('Volkswagen', 'up!',        'up! I',      2011, 2023, 'NSF'),

  -- Renault Twingo
  ('Renault',    'Twingo',     'Twingo II',  2007, 2014, 'X44'),
  ('Renault',    'Twingo',     'Twingo III', 2014, 2022, 'X07'),

  -- Citroën C1
  ('Citroen',    'C1',         'C1 I',       2005, 2014, 'A'),
  ('Citroen',    'C1',         'C1 II',      2014, 2022, 'B'),

  -- Peugeot 108
  ('Peugeot',    '108',        '108',        2014, 2021, 'B'),

  -- Opel Adam
  ('Opel',       'Adam',       'Adam',       2012, 2019, 'Gamma 2'),

  -- ── COMPACTOS (C-segment) ────────────────────────────────────────────────

  -- Volkswagen Golf
  ('Volkswagen', 'Golf',       'Mk6',        2008, 2012, 'PQ35'),
  ('Volkswagen', 'Golf',       'Mk7',        2012, 2019, 'MQB'),
  ('Volkswagen', 'Golf',       'Mk8',        2020, NULL, 'MQB Evo'),

  -- Peugeot 308
  ('Peugeot',    '308',        '308 I',      2007, 2013, 'PF2'),
  ('Peugeot',    '308',        '308 II',     2013, 2021, 'EMP2'),
  ('Peugeot',    '308',        '308 III',    2021, NULL, 'EMP2'),

  -- Renault Mégane
  ('Renault',    'Megane',     'Mégane III', 2008, 2015, 'C'),
  ('Renault',    'Megane',     'Mégane IV',  2015, 2022, 'CMF-CD'),

  -- Toyota Corolla
  ('Toyota',     'Corolla',    'E170',       2013, 2018, 'MC'),
  ('Toyota',     'Corolla',    'E210',       2018, NULL, 'TNGA-C'),

  -- SEAT Leon
  ('SEAT',       'Leon',       'Leon III',   2012, 2020, 'MQB'),
  ('SEAT',       'Leon',       'Leon IV',    2020, NULL, 'MQB Evo'),

  -- Skoda Octavia
  ('Skoda',      'Octavia',    'Octavia III',2012, 2019, 'MQB'),
  ('Skoda',      'Octavia',    'Octavia IV', 2020, NULL, 'MQB Evo'),

  -- Ford Focus
  ('Ford',       'Focus',      'Focus III',  2010, 2018, 'C1'),
  ('Ford',       'Focus',      'Focus IV',   2018, NULL, 'C2'),

  -- Opel Astra
  ('Opel',       'Astra',      'Astra J',    2009, 2015, 'Delta II'),
  ('Opel',       'Astra',      'Astra K',    2015, 2021, 'D2XX'),
  ('Opel',       'Astra',      'Astra L',    2021, NULL, 'STL-A'),

  -- Hyundai i30
  ('Hyundai',    'i30',        'i30 II',     2011, 2017, 'GD'),
  ('Hyundai',    'i30',        'i30 III',    2017, NULL, 'PD'),

  -- Kia Ceed
  ('Kia',        'Ceed',       'Ceed II',    2012, 2018, 'JD'),
  ('Kia',        'Ceed',       'Ceed III',   2018, NULL, 'CD'),

  -- Mazda 3
  ('Mazda',      '3',          'Mazda 3 III',2013, 2018, 'SkyActiv'),
  ('Mazda',      '3',          'Mazda 3 IV', 2018, NULL, 'SKY-VA'),

  -- Honda Civic
  ('Honda',      'Civic',      'Civic IX',   2011, 2015, 'FB/FG'),
  ('Honda',      'Civic',      'Civic X',    2015, 2021, 'FC/FK'),
  ('Honda',      'Civic',      'Civic XI',   2021, NULL, 'FL'),

  -- Audi A3
  ('Audi',       'A3',         'A3 8P',      2003, 2012, 'PQ35'),
  ('Audi',       'A3',         'A3 8V',      2012, 2020, 'MQB'),
  ('Audi',       'A3',         'A3 8Y',      2020, NULL, 'MQB Evo'),

  -- BMW Série 1
  ('BMW',        'Serie 1',    'E87',        2004, 2011, 'E87'),
  ('BMW',        'Serie 1',    'F20',        2011, 2019, 'UKL1'),
  ('BMW',        'Serie 1',    'F40',        2019, NULL, 'UKL3/FAAR'),

  -- Mercedes-Benz Classe A
  ('Mercedes-Benz','Classe A', 'W168',       1997, 2004, 'W168'),
  ('Mercedes-Benz','Classe A', 'W169',       2004, 2012, 'W169'),
  ('Mercedes-Benz','Classe A', 'W176',       2012, 2018, 'MFA'),
  ('Mercedes-Benz','Classe A', 'W177',       2018, NULL, 'MFA2'),

  -- Volvo V40
  ('Volvo',      'V40',        'V40 II',     2012, 2019, '525/526'),

  -- Cupra Leon
  ('Cupra',      'Leon',       'Leon I',     2014, 2020, 'MQB'),
  ('Cupra',      'Leon',       'Leon II',    2020, NULL, 'MQB Evo'),

  -- DS 4
  ('DS',         '4',          'DS 4',       2021, NULL, 'EMP2'),

  -- Citroën C4
  ('Citroen',    'C4',         'C4 II',      2010, 2018, 'PF2'),
  ('Citroen',    'C4',         'C4 III',     2020, NULL, 'EMP2'),

  -- Fiat Tipo
  ('Fiat',       'Tipo',       'Tipo',       2015, NULL, '356'),

  -- Skoda Scala
  ('Skoda',      'Scala',      'Scala I',    2018, NULL, 'MQB A0'),

  -- Volkswagen ID.3
  ('Volkswagen', 'ID.3',       'ID.3 I',     2020, NULL, 'MEB'),

  -- MG 4
  ('MG',         '4',          'MG 4 I',     2022, NULL, 'MSP'),

  -- Renault 5 E-Tech
  ('Renault',    '5 E-Tech',   'R5 E-Tech',  2024, NULL, 'AmpR Small'),

  -- Peugeot E-308
  ('Peugeot',    'E-308',      'E-308 I',    2023, NULL, 'STLA Medium'),

  -- Toyota Prius
  ('Toyota',     'Prius',      'Prius IV',   2015, 2022, 'TNGA-C'),
  ('Toyota',     'Prius',      'Prius V',    2022, NULL, 'TNGA-C'),

  -- Hyundai Ioniq
  ('Hyundai',    'Ioniq',      'Ioniq I',    2016, 2022, 'AE'),

  -- Honda e:Ny1
  ('Honda',      'e:Ny1',      'e:Ny1',      2023, NULL, 'e:N'),

  -- MINI Cooper
  ('MINI',       'Cooper',     'R56',        2006, 2013, 'R56'),
  ('MINI',       'Cooper',     'F56',        2013, 2022, 'UKL2'),
  ('MINI',       'Cooper',     'J01',        2023, NULL, 'FAAR'),

  -- ── PREMIUM COMPACTOS ────────────────────────────────────────────────────

  -- Audi A1
  ('Audi',       'A1',         'A1 8X',      2010, 2018, 'PQ25'),
  ('Audi',       'A1',         'A1 GB',      2018, NULL, 'MQB A0'),

  -- Mercedes-Benz CLA
  ('Mercedes-Benz','CLA',      'C117',       2013, 2019, 'MFA'),
  ('Mercedes-Benz','CLA',      'C118',       2019, NULL, 'MFA2'),

  -- BMW Série 2 Gran Coupé
  ('BMW',        'Serie 2 Gran Coupe','F44', 2019, NULL, 'UKL3'),

  -- ── BERLINAS MÉDIAS (D-segment) ──────────────────────────────────────────

  -- Skoda Superb
  ('Skoda',      'Superb',     'Superb II',  2008, 2015, 'PQ46'),
  ('Skoda',      'Superb',     'Superb III', 2015, NULL, 'MQB'),

  -- Skoda Superb Combi
  ('Skoda',      'Superb Combi','Superb Combi II', 2009, 2015, 'PQ46'),
  ('Skoda',      'Superb Combi','Superb Combi III',2015, NULL, 'MQB'),

  -- Volkswagen Passat
  ('Volkswagen', 'Passat',     'B7',         2010, 2014, 'PQ46'),
  ('Volkswagen', 'Passat',     'B8',         2014, 2023, 'MQB'),
  ('Volkswagen', 'Passat',     'B9',         2023, NULL, 'MEB hybrid'),

  -- Peugeot 508
  ('Peugeot',    '508',        '508 I',      2010, 2018, 'EMP2'),
  ('Peugeot',    '508',        '508 II',     2018, NULL, 'EMP2'),

  -- ── BERLINAS PREMIUM (D-segment) ─────────────────────────────────────────

  -- BMW Série 3
  ('BMW',        'Serie 3',    'E90',        2005, 2011, 'E9x'),
  ('BMW',        'Serie 3',    'F30',        2012, 2018, 'F3x'),
  ('BMW',        'Serie 3',    'G20',        2019, NULL, 'CLAR'),

  -- Mercedes-Benz Classe C
  ('Mercedes-Benz','Classe C', 'W203',       2000, 2007, 'W203'),
  ('Mercedes-Benz','Classe C', 'W204',       2007, 2014, 'W204'),
  ('Mercedes-Benz','Classe C', 'W205',       2014, 2021, 'W205'),
  ('Mercedes-Benz','Classe C', 'W206',       2021, NULL, 'W206'),

  -- Audi A4
  ('Audi',       'A4',         'B8',         2007, 2015, 'MLB'),
  ('Audi',       'A4',         'B9',         2015, NULL, 'MLB Evo'),

  -- Volvo S60
  ('Volvo',      'S60',        'S60 II',     2010, 2018, 'P24'),
  ('Volvo',      'S60',        'S60 III',    2018, NULL, 'SPA'),

  -- Volvo V60
  ('Volvo',      'V60',        'V60 I',      2010, 2018, 'P3'),
  ('Volvo',      'V60',        'V60 II',     2018, NULL, 'SPA'),

  -- Alfa Romeo Giulia
  ('Alfa Romeo', 'Giulia',     'Giulia I',   2016, NULL, 'Giorgio'),

  -- ── BERLINAS GRANDES (E-segment) ─────────────────────────────────────────

  -- BMW Série 5
  ('BMW',        'Serie 5',    'F10',        2009, 2016, 'F10'),
  ('BMW',        'Serie 5',    'G30',        2016, NULL, 'CLAR'),

  -- Mercedes-Benz Classe E
  ('Mercedes-Benz','Classe E', 'W211',       2002, 2009, 'W211'),
  ('Mercedes-Benz','Classe E', 'W212',       2009, 2016, 'W212'),
  ('Mercedes-Benz','Classe E', 'W213',       2016, 2023, 'W213'),
  ('Mercedes-Benz','Classe E', 'W214',       2023, NULL, 'W214'),

  -- Audi A6
  ('Audi',       'A6',         'C7',         2011, 2018, 'MLB'),
  ('Audi',       'A6',         'C8',         2018, NULL, 'MLB Evo'),

  -- Volvo S90
  ('Volvo',      'S90',        'S90 II',     2016, NULL, 'SPA'),

  -- Volvo V90
  ('Volvo',      'V90',        'V90 II',     2016, NULL, 'SPA'),

  -- ── ELÉTRICOS ────────────────────────────────────────────────────────────

  -- Tesla Model 3
  ('Tesla',      'Model 3',    'Model 3',    2017, 2023, 'E3'),
  ('Tesla',      'Model 3',    'Model 3 Highland',2023, NULL, 'E3 refresh'),

  -- Tesla Model Y
  ('Tesla',      'Model Y',    'Model Y',    2020, NULL, 'E4'),

  -- Tesla Model S
  ('Tesla',      'Model S',    'Model S',    2012, 2020, 'S'),
  ('Tesla',      'Model S',    'Model S Plaid',2021, NULL, 'S refresh'),

  -- Kia EV6
  ('Kia',        'EV6',        'EV6 I',      2021, NULL, 'E-GMP'),

  -- Kia EV3
  ('Kia',        'EV3',        'EV3 I',      2024, NULL, 'E-GMP'),

  -- Hyundai Ioniq 5
  ('Hyundai',    'Ioniq 5',    'Ioniq 5 I',  2021, NULL, 'E-GMP'),

  -- Hyundai Ioniq 6
  ('Hyundai',    'Ioniq 6',    'Ioniq 6 I',  2022, NULL, 'E-GMP'),

  -- Volkswagen ID.3 (already listed above)

  -- BYD Dolphin
  ('BYD',        'Dolphin',    'Dolphin I',  2021, NULL, 'e-Platform 3.0'),

  -- BYD Atto 3
  ('BYD',        'Atto 3',     'Atto 3 I',   2021, NULL, 'e-Platform 3.0'),

  -- BYD Seal
  ('BYD',        'Seal',       'Seal I',     2022, NULL, 'e-Platform 3.0'),

  -- MG ZS EV
  ('MG',         'ZS EV',      'ZS EV I',    2018, 2021, 'MSP'),
  ('MG',         'ZS EV',      'ZS EV II',   2022, NULL, 'MSP'),

  -- Volvo EX30
  ('Volvo',      'EX30',       'EX30 I',     2023, NULL, 'SEA'),

  -- Smart #1
  ('Smart',      '#1',         'Smart #1',   2022, NULL, 'SEA'),

  -- Smart #3
  ('Smart',      '#3',         'Smart #3',   2023, NULL, 'SEA'),

  -- ── PREMIUM / BERLINAS MÉDIAS-GRANDES ────────────────────────────────────

  -- Mercedes-Benz Classe B
  ('Mercedes-Benz','Classe B', 'W245',       2005, 2011, 'W245'),
  ('Mercedes-Benz','Classe B', 'W246',       2011, 2018, 'MFA'),
  ('Mercedes-Benz','Classe B', 'W247',       2018, NULL, 'MFA2'),

  -- Audi Q3
  ('Audi',       'Q3',         'Q3 8U',      2011, 2018, 'MQB'),
  ('Audi',       'Q3',         'Q3 F3',      2018, NULL, 'MQB'),

  -- Audi Q2
  ('Audi',       'Q2',         'Q2 GA',      2016, NULL, 'MQB A0'),

  -- BMW Série 4
  ('BMW',        'Serie 4',    'F32',        2013, 2020, 'F32'),
  ('BMW',        'Serie 4',    'G22',        2020, NULL, 'CLAR'),

  -- BMW Série 2 Active Tourer
  ('BMW',        'Serie 2 Active Tourer','F45',2014, 2021, 'UKL2'),
  ('BMW',        'Serie 2 Active Tourer','U06',2021, NULL, 'FAAR'),

  -- Mercedes-Benz CLE
  ('Mercedes-Benz','CLE',      'C236',       2023, NULL, 'W206'),

  -- Mercedes-Benz E Coupé
  ('Mercedes-Benz','E Coupe',  'C207',       2009, 2017, 'W212'),
  ('Mercedes-Benz','E Coupe',  'C238',       2017, 2023, 'W213'),

  -- Audi A5
  ('Audi',       'A5',         'A5 8T',      2007, 2016, 'MLB'),
  ('Audi',       'A5',         'A5 F5',      2016, NULL, 'MLB Evo'),

  -- Audi TT
  ('Audi',       'TT',         'TT 8N',      1998, 2006, '8N'),
  ('Audi',       'TT',         'TT 8J',      2006, 2014, 'PQ35'),
  ('Audi',       'TT',         'TT 8S',      2014, 2023, 'MQB'),

  -- MINI Clubman
  ('MINI',       'Clubman',    'R55',        2007, 2015, 'R55'),
  ('MINI',       'Clubman',    'F54',        2015, 2024, 'UKL2'),

  -- MINI Countryman
  ('MINI',       'Countryman', 'R60',        2010, 2016, 'R60'),
  ('MINI',       'Countryman', 'F60',        2016, 2023, 'UKL2'),
  ('MINI',       'Countryman', 'U25',        2023, NULL, 'FAAR'),

  -- Alfa Romeo Stelvio
  ('Alfa Romeo', 'Stelvio',    'Stelvio I',  2016, NULL, 'Giorgio'),

  -- Lexus IS
  ('Lexus',      'IS',         'IS III',     2013, NULL, 'GA-L'),

  -- Lexus ES
  ('Lexus',      'ES',         'ES VII',     2018, NULL, 'TNGA-K'),

  -- Lexus UX
  ('Lexus',      'UX',         'UX I',       2018, NULL, 'GA-C'),

  -- Lexus NX
  ('Lexus',      'NX',         'NX I',       2014, 2021, 'GA-K'),
  ('Lexus',      'NX',         'NX II',      2021, NULL, 'TNGA-K'),

  -- Lexus RX
  ('Lexus',      'RX',         'RX IV',      2015, 2022, 'GA-L'),
  ('Lexus',      'RX',         'RX V',       2022, NULL, 'GA-L'),

  -- BMW Z4
  ('BMW',        'Z4',         'Z4 E85',     2002, 2008, 'E85'),
  ('BMW',        'Z4',         'Z4 E89',     2009, 2016, 'E89'),
  ('BMW',        'Z4',         'Z4 G29',     2018, NULL, 'CLAR'),

  -- Porsche Panamera
  ('Porsche',    'Panamera',   'Panamera I', 2009, 2016, '970'),
  ('Porsche',    'Panamera',   'Panamera II',2016, NULL, '971'),

  -- Alpine A110
  ('Alpine',     'A110',       'A110 I',     2017, NULL, 'B10'),

  -- Ford Mustang
  ('Ford',       'Mustang',    'Mustang VI', 2015, 2023, 'S550'),
  ('Ford',       'Mustang',    'Mustang VII',2023, NULL, 'S650'),

  -- Mazda MX-5
  ('Mazda',      'MX-5',       'MX-5 NC',    2005, 2015, 'NC'),
  ('Mazda',      'MX-5',       'MX-5 ND',    2015, NULL, 'ND'),

  -- Toyota GR Yaris
  ('Toyota',     'GR Yaris',   'GR Yaris I', 2020, NULL, 'GR-Four'),

  -- Toyota GR86
  ('Toyota',     'GR86',       'GR86 II',    2021, NULL, 'ZN8'),

  -- Subaru BRZ
  ('Subaru',     'BRZ',        'BRZ I',      2012, 2021, 'ZC6'),
  ('Subaru',     'BRZ',        'BRZ II',     2021, NULL, 'ZD8'),

  -- ── SUVs URBANOS / COMPACTOS ─────────────────────────────────────────────

  -- Peugeot 2008
  ('Peugeot',    '2008',       '2008 I',     2013, 2019, 'PF1'),
  ('Peugeot',    '2008',       '2008 II',    2019, NULL, 'CMP'),

  -- Renault Captur
  ('Renault',    'Captur',     'Captur I',   2013, 2019, 'B'),
  ('Renault',    'Captur',     'Captur II',  2019, NULL, 'CMF-B'),

  -- Dacia Duster
  ('Dacia',      'Duster',     'Duster I',   2010, 2017, 'B0'),
  ('Dacia',      'Duster',     'Duster II',  2017, 2023, 'B0'),
  ('Dacia',      'Duster',     'Duster III', 2024, NULL, 'CMF-B'),

  -- Nissan Qashqai
  ('Nissan',     'Qashqai',    'Qashqai I',  2006, 2013, 'J10'),
  ('Nissan',     'Qashqai',    'Qashqai II', 2013, 2021, 'CMF-C'),
  ('Nissan',     'Qashqai',    'Qashqai III',2021, NULL, 'CMF-CD'),

  -- Volkswagen T-Cross
  ('Volkswagen', 'T-Cross',    'T-Cross I',  2018, NULL, 'MQB A0'),

  -- Volkswagen T-Roc
  ('Volkswagen', 'T-Roc',      'T-Roc I',   2017, NULL, 'MQB'),

  -- Toyota Yaris Cross
  ('Toyota',     'Yaris Cross','Yaris Cross I',2021, NULL, 'TNGA-B'),

  -- Toyota C-HR
  ('Toyota',     'C-HR',       'C-HR I',     2016, 2023, 'TNGA-C'),
  ('Toyota',     'C-HR',       'C-HR II',    2023, NULL, 'TNGA-C'),

  -- SEAT Arona
  ('SEAT',       'Arona',      'Arona I',    2017, NULL, 'MQB A0'),

  -- SEAT Ateca
  ('SEAT',       'Ateca',      'Ateca I',    2016, NULL, 'MQB'),

  -- Skoda Kamiq
  ('Skoda',      'Kamiq',      'Kamiq I',    2019, NULL, 'MQB A0'),

  -- Skoda Karoq
  ('Skoda',      'Karoq',      'Karoq I',    2017, NULL, 'MQB'),

  -- Skoda Kodiaq
  ('Skoda',      'Kodiaq',     'Kodiaq I',   2016, 2024, 'MQB'),
  ('Skoda',      'Kodiaq',     'Kodiaq II',  2024, NULL, 'MQB Evo'),

  -- Ford Puma
  ('Ford',       'Puma',       'Puma II',    2019, NULL, 'C2'),

  -- Nissan Juke
  ('Nissan',     'Juke',       'Juke I',     2010, 2019, 'F15'),
  ('Nissan',     'Juke',       'Juke II',    2019, NULL, 'CMF-B'),

  -- Hyundai Kona
  ('Hyundai',    'Kona',       'Kona I',     2017, 2022, 'OS'),
  ('Hyundai',    'Kona',       'Kona II',    2023, NULL, 'SX2'),

  -- Hyundai Bayon
  ('Hyundai',    'Bayon',      'Bayon I',    2021, NULL, 'BC3'),

  -- Kia Stonic
  ('Kia',        'Stonic',     'Stonic I',   2017, NULL, 'YB'),

  -- Kia Niro
  ('Kia',        'Niro',       'Niro I',     2016, 2022, 'DE'),
  ('Kia',        'Niro',       'Niro II',    2022, NULL, 'SG2'),

  -- Mazda CX-3
  ('Mazda',      'CX-3',       'CX-3 I',     2015, 2023, 'DK'),

  -- Mazda CX-30
  ('Mazda',      'CX-30',      'CX-30 I',    2019, NULL, 'DM'),

  -- Honda HR-V
  ('Honda',      'HR-V',       'HR-V I',     2015, 2021, 'RU'),
  ('Honda',      'HR-V',       'HR-V II',    2021, NULL, 'RS'),

  -- Opel Mokka
  ('Opel',       'Mokka',      'Mokka A',    2012, 2019, 'J13'),
  ('Opel',       'Mokka',      'Mokka B',    2020, NULL, 'CMP'),

  -- Citroën C3 Aircross
  ('Citroen',    'C3 Aircross','C3 Aircross I', 2017, 2023, 'EMP2'),
  ('Citroen',    'C3 Aircross','C3 Aircross II',2024, NULL, 'STLA Small'),

  -- Renault Arkana
  ('Renault',    'Arkana',     'Arkana I',   2019, NULL, 'CMF-B'),

  -- BMW X1
  ('BMW',        'X1',         'X1 E84',     2009, 2015, 'E84'),
  ('BMW',        'X1',         'X1 F48',     2015, 2022, 'UKL2'),
  ('BMW',        'X1',         'X1 U11',     2022, NULL, 'FAAR'),

  -- Mercedes-Benz GLA
  ('Mercedes-Benz','GLA',      'GLA X156',   2013, 2019, 'MFA'),
  ('Mercedes-Benz','GLA',      'GLA H247',   2020, NULL, 'MFA2'),

  -- Cupra Formentor
  ('Cupra',      'Formentor',  'Formentor I',2020, NULL, 'MQB'),

  -- Cupra Ateca
  ('Cupra',      'Ateca',      'Ateca I',    2016, NULL, 'MQB'),

  -- Jeep Avenger
  ('Jeep',       'Avenger',    'Avenger I',  2022, NULL, 'CMP'),

  -- Jeep Compass
  ('Jeep',       'Compass',    'Compass II', 2017, NULL, 'small-wide 4x4'),

  -- Fiat 500X
  ('Fiat',       '500X',       '500X I',     2014, NULL, '334'),

  -- DS 7
  ('DS',         '7',          'DS 7 I',     2017, NULL, 'EMP2'),

  -- MG HS
  ('MG',         'HS',         'MG HS I',    2018, NULL, 'MSP'),

  -- MG 5
  ('MG',         '5',          'MG 5 I',     2021, NULL, 'MSP'),

  -- Omoda 5
  ('Omoda',      '5',          'Omoda 5 I',  2022, NULL, 'CHERY'),

  -- ── SUVs MÉDIOS ──────────────────────────────────────────────────────────

  -- Peugeot 3008
  ('Peugeot',    '3008',       '3008 I',     2008, 2016, 'PF2'),
  ('Peugeot',    '3008',       '3008 II',    2016, 2023, 'EMP2'),
  ('Peugeot',    '3008',       '3008 III',   2023, NULL, 'STLA Medium'),

  -- Hyundai Tucson
  ('Hyundai',    'Tucson',     'Tucson III', 2015, 2020, 'TL'),
  ('Hyundai',    'Tucson',     'Tucson IV',  2020, NULL, 'NX4'),

  -- Kia Sportage
  ('Kia',        'Sportage',   'Sportage III',2010, 2015, 'SL'),
  ('Kia',        'Sportage',   'Sportage IV', 2015, 2021, 'QL'),
  ('Kia',        'Sportage',   'Sportage V',  2021, NULL, 'NQ5'),

  -- Volkswagen Tiguan
  ('Volkswagen', 'Tiguan',     'Tiguan I',   2007, 2016, 'PQ46'),
  ('Volkswagen', 'Tiguan',     'Tiguan II',  2016, NULL, 'MQB'),

  -- Toyota RAV4
  ('Toyota',     'RAV4',       'RAV4 IV',    2012, 2018, 'MC'),
  ('Toyota',     'RAV4',       'RAV4 V',     2018, NULL, 'TNGA-K'),

  -- Ford Kuga
  ('Ford',       'Kuga',       'Kuga II',    2012, 2019, 'C1'),
  ('Ford',       'Kuga',       'Kuga III',   2019, NULL, 'C2'),

  -- Mazda CX-5
  ('Mazda',      'CX-5',       'CX-5 I',     2012, 2017, 'SkyActiv'),
  ('Mazda',      'CX-5',       'CX-5 II',    2017, NULL, 'SKY-VA'),

  -- Honda CR-V
  ('Honda',      'CR-V',       'CR-V IV',    2012, 2018, 'RM'),
  ('Honda',      'CR-V',       'CR-V V',     2018, 2023, 'RW/RT'),
  ('Honda',      'CR-V',       'CR-V VI',    2023, NULL, 'RS'),

  -- Opel Grandland
  ('Opel',       'Grandland',  'Grandland X',2017, 2021, 'EMP2'),
  ('Opel',       'Grandland',  'Grandland II',2021, NULL, 'EMP2'),

  -- Citroën C5 Aircross
  ('Citroen',    'C5 Aircross','C5 Aircross I',2018, NULL, 'EMP2'),

  -- Renault Kadjar
  ('Renault',    'Kadjar',     'Kadjar I',   2015, 2022, 'CMF-CD'),

  -- Renault Austral
  ('Renault',    'Austral',    'Austral I',  2022, NULL, 'CMF-CD'),

  -- Audi Q5
  ('Audi',       'Q5',         'Q5 8R',      2008, 2016, 'MLB'),
  ('Audi',       'Q5',         'Q5 FY',      2016, NULL, 'MLB Evo'),

  -- Volvo XC40
  ('Volvo',      'XC40',       'XC40 I',     2017, NULL, 'CMA'),

  -- Volvo XC60
  ('Volvo',      'XC60',       'XC60 I',     2008, 2017, 'P3'),
  ('Volvo',      'XC60',       'XC60 II',    2017, NULL, 'SPA'),

  -- BMW X3
  ('BMW',        'X3',         'X3 E83',     2003, 2010, 'E83'),
  ('BMW',        'X3',         'X3 F25',     2010, 2017, 'F25'),
  ('BMW',        'X3',         'X3 G01',     2017, NULL, 'CLAR'),

  -- Mercedes-Benz GLC
  ('Mercedes-Benz','GLC',      'GLC X253',   2015, 2022, 'W205'),
  ('Mercedes-Benz','GLC',      'GLC X254',   2022, NULL, 'W206'),

  -- ── SUVs GRANDES ─────────────────────────────────────────────────────────

  -- BMW X5
  ('BMW',        'X5',         'X5 E70',     2006, 2013, 'E70'),
  ('BMW',        'X5',         'X5 F15',     2013, 2018, 'F15'),
  ('BMW',        'X5',         'X5 G05',     2018, NULL, 'CLAR'),

  -- BMW X6
  ('BMW',        'X6',         'X6 E71',     2008, 2014, 'E70'),
  ('BMW',        'X6',         'X6 F16',     2014, 2019, 'F15'),
  ('BMW',        'X6',         'X6 G06',     2019, NULL, 'CLAR'),

  -- Mercedes-Benz GLE
  ('Mercedes-Benz','GLE',      'GLE W166',   2015, 2019, 'W166'),
  ('Mercedes-Benz','GLE',      'GLE V167',   2019, NULL, 'W167'),

  -- Mercedes-Benz GLS
  ('Mercedes-Benz','GLS',      'GLS X166',   2015, 2019, 'W166'),
  ('Mercedes-Benz','GLS',      'GLS X167',   2019, NULL, 'W167'),

  -- Audi Q7
  ('Audi',       'Q7',         'Q7 4L',      2005, 2015, 'PL71'),
  ('Audi',       'Q7',         'Q7 4M',      2015, NULL, 'MLB Evo'),

  -- Audi Q8
  ('Audi',       'Q8',         'Q8 4M',      2018, NULL, 'MLB Evo'),

  -- Volvo XC90
  ('Volvo',      'XC90',       'XC90 I',     2002, 2014, 'P2'),
  ('Volvo',      'XC90',       'XC90 II',    2014, NULL, 'SPA'),

  -- Porsche Macan
  ('Porsche',    'Macan',      'Macan I',    2014, 2023, '95B'),
  ('Porsche',    'Macan',      'Macan II',   2023, NULL, 'J1 EV'),

  -- Porsche Cayenne
  ('Porsche',    'Cayenne',    'Cayenne II', 2010, 2017, '92A'),
  ('Porsche',    'Cayenne',    'Cayenne III',2017, NULL, '9YA'),

  -- Land Rover Range Rover Evoque
  ('Land Rover', 'Range Rover Evoque','Evoque I', 2011, 2018, 'L538'),
  ('Land Rover', 'Range Rover Evoque','Evoque II',2019, NULL, 'L551'),

  -- Land Rover Range Rover Velar
  ('Land Rover', 'Range Rover Velar','Velar I',   2017, NULL, 'L560'),

  -- Land Rover Range Rover Sport
  ('Land Rover', 'Range Rover Sport','Sport I',   2005, 2013, 'L320'),
  ('Land Rover', 'Range Rover Sport','Sport II',  2013, 2022, 'L494'),
  ('Land Rover', 'Range Rover Sport','Sport III', 2022, NULL, 'L461'),

  -- Land Rover Discovery Sport
  ('Land Rover', 'Discovery Sport','Disc Sport I',2014, NULL, 'L550'),

  -- Land Rover Defender
  ('Land Rover', 'Defender',   'Defender',   2020, NULL, 'D7u'),

  -- Jaguar F-Pace
  ('Jaguar',     'F-Pace',     'F-Pace I',   2016, NULL, 'X761'),

  -- Jaguar E-Pace
  ('Jaguar',     'E-Pace',     'E-Pace I',   2017, NULL, 'X540'),

  -- Maserati Grecale
  ('Maserati',   'Grecale',    'Grecale I',  2022, NULL, 'F160'),

  -- ── MPVs / FAMILIARES ────────────────────────────────────────────────────

  -- Citroën Berlingo
  ('Citroen',    'Berlingo',   'Berlingo II', 2008, 2018, 'B9'),
  ('Citroen',    'Berlingo',   'Berlingo III',2018, NULL, 'EMP2'),

  -- Peugeot Rifter
  ('Peugeot',    'Rifter',     'Rifter I',   2018, NULL, 'EMP2'),

  -- Opel Combo Life
  ('Opel',       'Combo Life', 'Combo Life E',2018, NULL, 'EMP2'),

  -- Volkswagen Touran
  ('Volkswagen', 'Touran',     'Touran I',   2003, 2010, 'PQ35'),
  ('Volkswagen', 'Touran',     'Touran II',  2015, NULL, 'MQB'),

  -- Volkswagen Caddy
  ('Volkswagen', 'Caddy',      'Caddy III',  2003, 2020, 'PQ35'),
  ('Volkswagen', 'Caddy',      'Caddy V',    2020, NULL, 'MQB'),

  -- Ford Tourneo Connect
  ('Ford',       'Tourneo Connect','Tourneo II', 2013, 2021, 'C1'),
  ('Ford',       'Tourneo Connect','Tourneo III',2022, NULL, 'MQB'),

  -- Ford S-Max
  ('Ford',       'S-Max',      'S-Max I',    2006, 2014, 'CD3'),
  ('Ford',       'S-Max',      'S-Max II',   2015, 2023, 'CD4'),

  -- SEAT Alhambra
  ('SEAT',       'Alhambra',   'Alhambra II',2010, 2022, 'PQ46'),

  -- Volkswagen Sharan
  ('Volkswagen', 'Sharan',     'Sharan II',  2010, 2022, 'PQ46'),

  -- Mercedes-Benz Classe V
  ('Mercedes-Benz','Classe V', 'W447',       2014, NULL, 'VS30'),

  -- Toyota Proace City Verso
  ('Toyota',     'Proace City Verso','Proace City Verso',2019, NULL, 'EMP2'),

  -- Peugeot 5008
  ('Peugeot',    '5008',       '5008 I',     2009, 2016, 'PF2'),
  ('Peugeot',    '5008',       '5008 II',    2016, NULL, 'EMP2'),

  -- Renault Scénic
  ('Renault',    'Scenic',     'Scénic IV',  2016, 2023, 'CMF-CD'),
  ('Renault',    'Scenic',     'Scénic E-Tech',2023, NULL, 'CMF-EV'),

  -- Dacia Jogger
  ('Dacia',      'Jogger',     'Jogger I',   2021, NULL, 'CMF-B'),

  -- ── SUBARU / SUZUKI ──────────────────────────────────────────────────────

  -- Subaru Outback
  ('Subaru',     'Outback',    'Outback V',  2014, 2019, 'BS'),
  ('Subaru',     'Outback',    'Outback VI', 2019, NULL, 'SGP'),

  -- Subaru Forester
  ('Subaru',     'Forester',   'Forester IV',2012, 2018, 'SJ'),
  ('Subaru',     'Forester',   'Forester V', 2018, NULL, 'SK'),

  -- Suzuki Swift
  ('Suzuki',     'Swift',      'Swift IV',   2010, 2017, 'FZ'),
  ('Suzuki',     'Swift',      'Swift V',    2017, NULL, 'AZ'),

  -- Suzuki Vitara
  ('Suzuki',     'Vitara',     'Vitara IV',  2015, NULL, 'LY'),

  -- Suzuki S-Cross
  ('Suzuki',     'S-Cross',    'S-Cross I',  2013, 2021, 'JY'),
  ('Suzuki',     'S-Cross',    'S-Cross II', 2021, NULL, 'KL')

)
INSERT INTO generations (model_id, name, year_start, year_end, platform)
SELECT ml.id, gd.name, gd.year_start, gd.year_end, gd.platform
FROM gen_data gd
JOIN (
    SELECT vm.id, b.name AS brand, vm.name AS model
    FROM vehicle_models vm
    JOIN brands b ON b.id = vm.brand_id
) ml ON LOWER(translate(ml.brand, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝàáâãäåèéêëìíîïòóôõöùúûüý',
                                  'AAAAAAEEEEIIIIOOOOOUUUUYaaaaaaeeeeiiiioooooouuuuy'))
       = LOWER(translate(gd.brand, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝàáâãäåèéêëìíîïòóôõöùúûüý',
                                   'AAAAAAEEEEIIIIOOOOOUUUUYaaaaaaeeeeiiiioooooouuuuy'))
   AND LOWER(translate(ml.model, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝàáâãäåèéêëìíîïòóôõöùúûüý',
                                 'AAAAAAEEEEIIIIOOOOOUUUUYaaaaaaeeeeiiiioooooouuuuy'))
       = LOWER(translate(gd.model, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝàáâãäåèéêëìíîïòóôõöùúûüý',
                                   'AAAAAAEEEEIIIIOOOOOUUUUYaaaaaaeeeeiiiioooooouuuuy'));

-- Verify
SELECT b.name AS brand, vm.name AS model, g.name AS generation, g.year_start, g.year_end, g.platform
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
ORDER BY b.name, vm.name, g.year_start;
