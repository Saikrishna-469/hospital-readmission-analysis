-- 04_readmission_by_utilization.sql
-- Effect of length of stay, number of medications, and prior utilization
-- (outpatient, emergency, and inpatient visits in the year before) on
-- 30-day readmission.

-- Length of stay
SELECT
    los_group,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct,
    ROUND(AVG(time_in_hospital), 2) AS mean_los_days
FROM encounters
GROUP BY los_group
ORDER BY MIN(time_in_hospital);

-- Number of medications
SELECT
    meds_group,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY meds_group
ORDER BY MIN(num_medications);

-- Prior inpatient visits (strongest utilization signal in this dataset)
SELECT
    prior_inpatient_group AS prior_inpatient_visits,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY prior_inpatient_group
ORDER BY prior_inpatient_group;

-- Prior emergency visits
SELECT
    CASE
        WHEN number_emergency = 0 THEN '0'
        WHEN number_emergency = 1 THEN '1'
        ELSE '2+'
    END AS prior_emergency_visits,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY prior_emergency_visits
ORDER BY prior_emergency_visits;

-- Prior outpatient visits
SELECT
    CASE
        WHEN number_outpatient = 0 THEN '0'
        WHEN number_outpatient BETWEEN 1 AND 2 THEN '1-2'
        ELSE '3+'
    END AS prior_outpatient_visits,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY prior_outpatient_visits
ORDER BY prior_outpatient_visits;

-- Mean utilization by readmission status (for t-tests / Mann-Whitney in the notebook)
SELECT
    readmitted_30d,
    COUNT(*) AS n,
    ROUND(AVG(time_in_hospital), 2) AS mean_los,
    ROUND(AVG(num_medications), 2) AS mean_medications,
    ROUND(AVG(num_lab_procedures), 2) AS mean_lab_procedures,
    ROUND(AVG(number_inpatient), 2) AS mean_prior_inpatient,
    ROUND(AVG(number_emergency), 2) AS mean_prior_emergency,
    ROUND(AVG(number_diagnoses), 2) AS mean_num_diagnoses
FROM encounters
GROUP BY readmitted_30d;
