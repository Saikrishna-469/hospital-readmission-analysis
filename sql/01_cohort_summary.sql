-- 01_cohort_summary.sql
-- Cohort flow and overall 30-day readmission rate.
-- Run against data/hospital_readmission.duckdb (tables: encounters_raw, encounters).

-- Overall cohort size and 30-day readmission rate
SELECT
    COUNT(*) AS n_patients,
    SUM(readmitted_30d) AS n_readmitted_30d,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct,
    ROUND(AVG(time_in_hospital), 2) AS mean_los_days,
    ROUND(AVG(num_medications), 2) AS mean_num_medications
FROM encounters;

-- Cohort flow (raw -> exclusions -> first encounter per patient)
SELECT 'raw encounters' AS step, COUNT(*) AS n FROM encounters_raw
UNION ALL
SELECT 'after outcome exclusions (expired, hospice, still patient, unknown gender)',
       COUNT(*) FROM encounters_raw
WHERE gender <> 'Unknown/Invalid'
  AND CAST(discharge_disposition_id AS INTEGER) NOT IN (11, 13, 14, 19, 20, 21, 12)
UNION ALL
SELECT 'analysis cohort (first encounter per patient)', COUNT(*) FROM encounters;

-- Target distribution in the raw file, for reference
SELECT readmitted, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM encounters_raw
GROUP BY readmitted
ORDER BY n DESC;
