-- 05_readmission_by_clinical.sql
-- Impact of HbA1c testing, medication changes, diabetes medication, and
-- primary diagnosis category on 30-day readmission.

-- HbA1c test result (None = test not performed)
SELECT
    A1Cresult AS a1c_result,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY A1Cresult
ORDER BY n DESC;

-- HbA1c tested vs not tested
SELECT
    CASE WHEN A1Cresult = 'None' THEN 'Not tested' ELSE 'Tested' END AS a1c_tested,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY a1c_tested;

-- Medication change during the stay
SELECT
    CASE WHEN change = 'Ch' THEN 'Medication changed' ELSE 'No change' END AS medication_change,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY medication_change;

-- Diabetes medication prescribed
SELECT
    CASE WHEN diabetesMed = 'Yes' THEN 'Diabetes med prescribed' ELSE 'No diabetes med' END AS diabetes_med,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY diabetes_med;

-- Primary diagnosis category (ICD-9 groups, see scripts/load_clean.py)
SELECT
    diag_1_category,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY diag_1_category
ORDER BY readmit_rate_pct DESC;

-- Insulin use (Steady / Down / Up vs No)
SELECT
    insulin,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters_raw
WHERE CAST(encounter_id AS BIGINT) IN (SELECT encounter_id FROM encounters)
GROUP BY insulin
ORDER BY n DESC;
