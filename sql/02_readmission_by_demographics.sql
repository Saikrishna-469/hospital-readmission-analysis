-- 02_readmission_by_demographics.sql
-- 30-day readmission rate by age group, race, and gender.

-- By age group
SELECT
    age_group,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY age_group
ORDER BY age_group;

-- By race (NULL race shown as Missing)
SELECT
    COALESCE(race, 'Missing') AS race,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY race
ORDER BY n DESC;

-- By gender
SELECT
    gender,
    COUNT(*) AS n,
    SUM(readmitted_30d) AS n_readmitted,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY gender
ORDER BY n DESC;

-- Age group x gender (for the heatmap in the notebook)
SELECT
    age_group,
    gender,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(readmitted_30d), 2) AS readmit_rate_pct
FROM encounters
GROUP BY age_group, gender
ORDER BY age_group, gender;
