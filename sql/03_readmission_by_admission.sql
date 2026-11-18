-- 03_readmission_by_admission.sql
-- 30-day readmission rate by admission type and admission source.

-- By admission type
SELECT
    admission_type,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY admission_type
ORDER BY readmit_rate_pct DESC;

-- By admission source (top sources; labels from IDs_mapping.csv)
SELECT
    CASE admission_source_id
        WHEN 7 THEN 'Emergency Room'
        WHEN 1 THEN 'Physician Referral'
        WHEN 17 THEN 'NULL (not mapped)'
        WHEN 4 THEN 'Transfer from a hospital'
        WHEN 6 THEN 'Transfer from another health care facility'
        WHEN 2 THEN 'Clinic Referral'
        WHEN 5 THEN 'Transfer from SNF'
        ELSE 'Other'
    END AS admission_source,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY admission_source
ORDER BY n DESC;
