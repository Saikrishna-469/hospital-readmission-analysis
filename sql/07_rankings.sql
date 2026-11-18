-- 07_rankings.sql
-- Window-function rankings: which segments stand out once volume is
-- taken into account.

-- Rank primary diagnosis categories by readmission rate (min 1,000 patients)
WITH diag_rates AS (
    SELECT
        diag_1_category,
        COUNT(*) AS n,
        ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
    FROM encounters
    GROUP BY diag_1_category
    HAVING COUNT(*) >= 1000
)
SELECT
    diag_1_category,
    n,
    readmit_rate_pct,
    RANK() OVER (ORDER BY readmit_rate_pct DESC) AS rate_rank
FROM diag_rates
ORDER BY rate_rank;

-- Rank admission types within each age group (oldest three groups shown)
WITH age_adm AS (
    SELECT
        age_group,
        admission_type,
        COUNT(*) AS n,
        ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
    FROM encounters
    GROUP BY age_group, admission_type
)
SELECT
    age_group,
    admission_type,
    n,
    readmit_rate_pct,
    RANK() OVER (PARTITION BY age_group ORDER BY readmit_rate_pct DESC) AS rate_rank_within_age
FROM age_adm
WHERE age_group IN ('[60-70)', '[70-80)', '[80-90)')
ORDER BY age_group, rate_rank_within_age;

-- Rank discharge groups by readmission rate, with share of all readmissions
WITH d AS (
    SELECT
        discharge_group,
        COUNT(*) AS n,
        SUM(readmitted_30d) AS n_readmitted,
        ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
    FROM encounters
    GROUP BY discharge_group
)
SELECT
    discharge_group,
    n,
    n_readmitted,
    readmit_rate_pct,
    ROUND(100.0 * n_readmitted / SUM(n_readmitted) OVER (), 1) AS share_of_all_readmissions_pct,
    RANK() OVER (ORDER BY readmit_rate_pct DESC) AS rate_rank
FROM d
ORDER BY rate_rank;
