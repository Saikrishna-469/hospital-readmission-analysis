-- 06_readmission_by_discharge.sql
-- Discharge disposition (home vs. facility) and 30-day readmission.

SELECT
    discharge_group,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY discharge_group
ORDER BY readmit_rate_pct DESC;

-- Discharge group x prior inpatient visits: does facility discharge help
-- the highest-risk patients?
SELECT
    discharge_group,
    prior_inpatient_group AS prior_inpatient_visits,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY discharge_group, prior_inpatient_group
ORDER BY discharge_group, prior_inpatient_group;
