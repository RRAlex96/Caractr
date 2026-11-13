-- Migration v5.8 — give each changeover year to one generation
--
-- Consecutive generations of a model shared their boundary year (Clio IV
-- 2012–2019, Clio V 2019–now). _get_generation_window returns the newest row
-- containing the car's year, so every car registered in a changeover year was
-- treated as the newer generation and priced against it, even when the older
-- one was still the car on sale for most of that year.
--
-- Rule (same as v5.6 and v5.7): the changeover year goes to the generation on
-- sale for most of it. New generation with customers in the first half of the
-- year -> the older row ends a year earlier. Second half, or later -> the
-- newer row starts a year later. A few rows were off by more than a year
-- (Honda Civic and Subaru Outback had US dates) and get explicit values.
--
-- Only year_start / year_end change. No row is inserted or deleted, and nothing
-- that references generations.id is touched.
--
-- Each launch date and its source is in migration_v58_changeover_years.md.
--
-- Idempotent: every update names the generation and the old value of the one
-- column it changes, and does nothing when that value is already different.

BEGIN;

DROP TABLE IF EXISTS _v58_gens;
CREATE TEMP TABLE _v58_gens AS
SELECT g.id AS generation_id,
       translate(b.name,  'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜàáâãäåèéêëìíîïòóôõöùúûü',
                          'AAAAAAEEEEIIIIOOOOOUUUUaaaaaaeeeeiiiiooooouuuu') AS brand,
       translate(vm.name, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜàáâãäåèéêëìíîïòóôõöùúûü',
                          'AAAAAAEEEEIIIIOOOOOUUUUaaaaaaeeeeiiiiooooouuuu') AS model,
       translate(g.name,  'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜàáâãäåèéêëìíîïòóôõöùúûü',
                          'AAAAAAEEEEIIIIOOOOOUUUUaaaaaaeeeeiiiiooooouuuu') AS generation
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id;

-- (brand, model, generation, column, old value, new value); names without accents
DROP TABLE IF EXISTS _v58_ops;
CREATE TEMP TABLE _v58_ops (
    brand TEXT, model TEXT, generation TEXT, col TEXT, old_value INT, new_value INT
);

INSERT INTO _v58_ops VALUES
    ('Audi', 'A1', 'A1 GB', 'year_start', 2018, 2019),
    ('Audi', 'A3', 'A3 8V', 'year_start', 2012, 2013),
    ('Audi', 'A3', 'A3 8V', 'year_end', 2020, 2019),
    ('Audi', 'A4', 'B9', 'year_start', 2015, 2016),
    ('Audi', 'A5', 'A5 F5', 'year_start', 2016, 2017),
    ('Audi', 'A6', 'C7', 'year_end', 2018, 2017),
    ('Audi', 'Q3', 'Q3 F3', 'year_start', 2018, 2019),
    ('Audi', 'Q5', 'Q5 FY', 'year_start', 2016, 2017),
    ('Audi', 'Q7', 'Q7 4L', 'year_end', 2015, 2014),
    ('Audi', 'TT', 'TT 8S', 'year_start', 2014, 2015),
    ('BMW', 'Serie 1', 'F20', 'year_start', 2011, 2012),
    ('BMW', 'Serie 1', 'F40', 'year_start', 2019, 2020),
    ('BMW', 'Serie 2 Active Tourer', 'U06', 'year_start', 2021, 2022),
    ('BMW', 'Serie 4', 'G22', 'year_start', 2020, 2021),
    ('BMW', 'X1', 'X1 F48', 'year_start', 2015, 2016),
    ('BMW', 'X1', 'X1 U11', 'year_start', 2022, 2023),
    ('BMW', 'X3', 'X3 F25', 'year_start', 2010, 2011),
    ('BMW', 'X3', 'X3 G01', 'year_start', 2017, 2018),
    ('BMW', 'X5', 'X5 F15', 'year_start', 2013, 2014),
    ('BMW', 'X5', 'X5 G05', 'year_start', 2018, 2019),
    ('BMW', 'X6', 'X6 F16', 'year_start', 2014, 2015),
    ('BMW', 'X6', 'X6 G06', 'year_start', 2019, 2020),
    ('Citroen', 'Berlingo', 'Berlingo III', 'year_start', 2018, 2019),
    ('Citroen', 'C1', 'C1 II', 'year_start', 2014, 2015),
    ('Citroen', 'C3', 'C3 III', 'year_start', 2016, 2017),
    ('Cupra', 'Leon', 'Leon II', 'year_start', 2020, 2021),
    ('Dacia', 'Duster', 'Duster II', 'year_start', 2017, 2018),
    ('Dacia', 'Sandero', 'Sandero II', 'year_start', 2012, 2013),
    ('Ford', 'Fiesta', 'Fiesta VII', 'year_start', 2017, 2018),
    ('Ford', 'Focus', 'Focus IV', 'year_start', 2018, 2019),
    ('Ford', 'Kuga', 'Kuga III', 'year_start', 2019, 2020),
    ('Ford', 'Mustang', 'Mustang VII', 'year_start', 2023, 2024),
    ('Honda', 'CR-V', 'CR-V V', 'year_start', 2018, 2019),
    ('Honda', 'CR-V', 'CR-V VI', 'year_start', 2023, 2024),
    ('Honda', 'Civic', 'Civic IX', 'year_end', 2015, 2016),
    ('Honda', 'Civic', 'Civic X', 'year_start', 2015, 2017),
    ('Honda', 'Civic', 'Civic X', 'year_end', 2021, 2022),
    ('Honda', 'Civic', 'Civic XI', 'year_start', 2021, 2023),
    ('Honda', 'HR-V', 'HR-V II', 'year_start', 2021, 2022),
    ('Honda', 'Jazz', 'Jazz III', 'year_end', 2020, 2019),
    ('Hyundai', 'Tucson', 'Tucson IV', 'year_start', 2020, 2021),
    ('Hyundai', 'i10', 'i10 II', 'year_start', 2013, 2014),
    ('Hyundai', 'i10', 'i10 III', 'year_start', 2019, 2020),
    ('Hyundai', 'i20', 'i20 II', 'year_start', 2014, 2015),
    ('Hyundai', 'i20', 'i20 III', 'year_start', 2020, 2021),
    ('Hyundai', 'i30', 'i30 II', 'year_end', 2017, 2016),
    ('Kia', 'Ceed', 'Ceed II', 'year_end', 2018, 2017),
    ('Kia', 'Niro', 'Niro I', 'year_end', 2022, 2021),
    ('Kia', 'Picanto', 'Picanto II', 'year_end', 2017, 2016),
    ('Kia', 'Rio', 'Rio III', 'year_end', 2017, 2016),
    ('Kia', 'Sportage', 'Sportage IV', 'year_start', 2015, 2016),
    ('Kia', 'Sportage', 'Sportage V', 'year_start', 2021, 2022),
    ('Land Rover', 'Range Rover Sport', 'Sport II', 'year_start', 2013, 2014),
    ('Land Rover', 'Range Rover Sport', 'Sport III', 'year_start', 2022, 2023),
    ('Lexus', 'NX', 'NX II', 'year_start', 2021, 2022),
    ('Lexus', 'RX', 'RX V', 'year_start', 2022, 2023),
    ('MINI', 'Clubman', 'F54', 'year_start', 2015, 2016),
    ('MINI', 'Cooper', 'F56', 'year_start', 2013, 2014),
    ('MINI', 'Countryman', 'F60', 'year_start', 2016, 2017),
    ('MINI', 'Countryman', 'U25', 'year_start', 2023, 2024),
    ('Mazda', '3', 'Mazda 3 IV', 'year_start', 2018, 2019),
    ('Mazda', 'CX-5', 'CX-5 I', 'year_end', 2017, 2016),
    ('Mazda', 'MX-5', 'MX-5 ND', 'year_start', 2015, 2016),
    ('Mercedes-Benz', 'CLA', 'C117', 'year_end', 2019, 2018),
    ('Mercedes-Benz', 'Classe A', 'W169', 'year_start', 2004, 2005),
    ('Mercedes-Benz', 'Classe A', 'W176', 'year_start', 2012, 2013),
    ('Mercedes-Benz', 'Classe A', 'W176', 'year_end', 2018, 2017),
    ('Mercedes-Benz', 'Classe B', 'W246', 'year_start', 2011, 2012),
    ('Mercedes-Benz', 'Classe B', 'W247', 'year_start', 2018, 2019),
    ('Mercedes-Benz', 'Classe C', 'W203', 'year_end', 2007, 2006),
    ('Mercedes-Benz', 'Classe C', 'W204', 'year_end', 2014, 2013),
    ('Mercedes-Benz', 'Classe C', 'W205', 'year_end', 2021, 2020),
    ('Mercedes-Benz', 'Classe E', 'W211', 'year_end', 2009, 2008),
    ('Mercedes-Benz', 'Classe E', 'W212', 'year_end', 2016, 2015),
    ('Mercedes-Benz', 'Classe E', 'W214', 'year_start', 2023, 2024),
    ('Mercedes-Benz', 'E Coupe', 'C207', 'year_end', 2017, 2016),
    ('Mercedes-Benz', 'GLC', 'GLC X254', 'year_start', 2022, 2023),
    ('Mercedes-Benz', 'GLE', 'GLE W166', 'year_end', 2019, 2018),
    ('Mercedes-Benz', 'GLS', 'GLS X167', 'year_start', 2019, 2020),
    ('Nissan', 'Juke', 'Juke II', 'year_start', 2019, 2020),
    ('Nissan', 'Micra', 'Micra K13', 'year_end', 2017, 2016),
    ('Nissan', 'Qashqai', 'Qashqai II', 'year_start', 2013, 2014),
    ('Nissan', 'Qashqai', 'Qashqai III', 'year_start', 2021, 2022),
    ('Opel', 'Astra', 'Astra K', 'year_start', 2015, 2016),
    ('Opel', 'Astra', 'Astra L', 'year_start', 2021, 2022),
    ('Opel', 'Corsa', 'Corsa E', 'year_start', 2014, 2015),
    ('Opel', 'Corsa', 'Corsa F', 'year_start', 2019, 2020),
    ('Opel', 'Grandland', 'Grandland (facelift)', 'year_start', 2021, 2022),
    ('Peugeot', '2008', '2008 II', 'year_start', 2019, 2020),
    ('Peugeot', '208', '208 II', 'year_start', 2019, 2020),
    ('Peugeot', '3008', '3008 II', 'year_start', 2016, 2017),
    ('Peugeot', '3008', '3008 III', 'year_start', 2023, 2024),
    ('Peugeot', '308', '308 II', 'year_start', 2013, 2014),
    ('Peugeot', '308', '308 III', 'year_start', 2021, 2022),
    ('Peugeot', '5008', '5008 II', 'year_start', 2016, 2017),
    ('Peugeot', '508', '508 II', 'year_start', 2018, 2019),
    ('Porsche', 'Cayenne', 'Cayenne III', 'year_start', 2017, 2018),
    ('Porsche', 'Panamera', 'Panamera II', 'year_start', 2016, 2017),
    ('Renault', 'Captur', 'Captur II', 'year_start', 2019, 2020),
    ('Renault', 'Clio', 'Clio IV', 'year_start', 2012, 2013),
    ('Renault', 'Clio', 'Clio V', 'year_start', 2019, 2020),
    ('Renault', 'Megane', 'Megane IV', 'year_start', 2015, 2016),
    ('Renault', 'Scenic', 'Scenic E-Tech', 'year_start', 2023, 2024),
    ('Renault', 'Twingo', 'Twingo III', 'year_start', 2014, 2015),
    ('SEAT', 'Ibiza', 'Ibiza IV', 'year_end', 2017, 2016),
    ('SEAT', 'Leon', 'Leon III', 'year_end', 2020, 2019),
    ('Skoda', 'Fabia', 'Fabia III', 'year_start', 2014, 2015),
    ('Skoda', 'Fabia', 'Fabia IV', 'year_start', 2021, 2022),
    ('Skoda', 'Kodiaq', 'Kodiaq I', 'year_end', 2024, 2023),
    ('Skoda', 'Superb', 'Superb II', 'year_end', 2015, 2014),
    ('Skoda', 'Superb Combi', 'Superb Combi III', 'year_start', 2015, 2016),
    ('Subaru', 'BRZ', 'BRZ II', 'year_start', 2021, 2023),
    ('Subaru', 'Forester', 'Forester V', 'year_start', 2018, 2019),
    ('Subaru', 'Outback', 'Outback V', 'year_end', 2019, 2020),
    ('Subaru', 'Outback', 'Outback VI', 'year_start', 2019, 2021),
    ('Suzuki', 'S-Cross', 'S-Cross II', 'year_start', 2021, 2022),
    ('Suzuki', 'Swift', 'Swift IV', 'year_end', 2017, 2016),
    ('Tesla', 'Model 3', 'Model 3 Highland', 'year_start', 2023, 2024),
    ('Toyota', 'C-HR', 'C-HR II', 'year_start', 2023, 2024),
    ('Toyota', 'Corolla', 'E210', 'year_start', 2018, 2019),
    ('Toyota', 'Prius', 'Prius V', 'year_start', 2022, 2023),
    ('Toyota', 'RAV4', 'RAV4 V', 'year_start', 2018, 2019),
    ('Toyota', 'Yaris', 'Yaris IV', 'year_start', 2020, 2021),
    ('Volkswagen', 'Golf', 'Mk7', 'year_start', 2012, 2013),
    ('Volkswagen', 'Passat', 'B8', 'year_start', 2014, 2015),
    ('Volkswagen', 'Passat', 'B9', 'year_start', 2023, 2024),
    ('Volkswagen', 'Polo', 'Polo VI', 'year_start', 2017, 2018),
    ('Volkswagen', 'Tiguan', 'Tiguan I', 'year_end', 2016, 2015),
    ('Volvo', 'S60', 'S60 III', 'year_start', 2018, 2019),
    ('Volvo', 'V60', 'V60 II', 'year_start', 2018, 2019),
    ('Volvo', 'XC60', 'XC60 II', 'year_start', 2017, 2018),
    ('Volvo', 'XC90', 'XC90 II', 'year_start', 2014, 2015);

DO $$
DECLARE
    n_end   INTEGER;
    n_start INTEGER;
    n_bad   INTEGER;
BEGIN
    UPDATE generations g
    SET year_end = o.new_value
    FROM _v58_ops o
    JOIN _v58_gens x ON x.brand = o.brand AND x.model = o.model AND x.generation = o.generation
    WHERE o.col = 'year_end' AND g.id = x.generation_id AND g.year_end = o.old_value;
    GET DIAGNOSTICS n_end = ROW_COUNT;

    UPDATE generations g
    SET year_start = o.new_value
    FROM _v58_ops o
    JOIN _v58_gens x ON x.brand = o.brand AND x.model = o.model AND x.generation = o.generation
    WHERE o.col = 'year_start' AND g.id = x.generation_id AND g.year_start = o.old_value;
    GET DIAGNOSTICS n_start = ROW_COUNT;

    -- Volvo S60 III: production for Europe ended in 2024; the row was still open-ended.
    UPDATE generations g
    SET year_end = 2024
    FROM _v58_gens x
    WHERE g.id = x.generation_id AND x.brand = 'Volvo' AND x.model = 'S60'
      AND x.generation = 'S60 III' AND g.year_end IS NULL;

    SELECT COUNT(*) INTO n_bad FROM generations WHERE year_end < year_start;
    IF n_bad > 0 THEN
        RAISE EXCEPTION 'v58 would leave % generation(s) ending before they start', n_bad;
    END IF;

    RAISE NOTICE 'v58: % end years and % start years changed (of % listed)',
        n_end, n_start, (SELECT COUNT(*) FROM _v58_ops);
END $$;

COMMIT;

-- Verify: every generation of the models touched.
SELECT b.name AS brand, vm.name AS model, g.id, g.name AS generation, g.year_start, g.year_end
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
JOIN _v58_gens x ON x.generation_id = g.id
WHERE (x.brand, x.model) IN (SELECT brand, model FROM _v58_ops)
ORDER BY b.name, vm.name, g.year_start;
