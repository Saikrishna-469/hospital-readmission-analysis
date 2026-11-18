# Dashboard spec — how to rebuild this in Power BI or Tableau

The HTML dashboard in `index.html` is a static version of this analysis. To
rebuild it as an interactive dashboard, use the same data and measures below.
No Power BI (.pbix) or Tableau (.twbx) file is included in this repo.

## Data source
- DuckDB table `encounters` in `data/hospital_readmission.duckdb`
  (build it with `python scripts/load_clean.py`), or export it to CSV/Parquet
  with `COPY (SELECT * FROM encounters) TO 'encounters.csv' (HEADER)`.
- One row per patient (n = 69,985), target `readmitted_30d` (1 = readmitted
  within 30 days).

## Pages
1. **Overview (KPI cards):** Patients (COUNT), 30-day readmissions
   (SUM(readmitted_30d)), 30-day readmission rate (AVERAGE(readmitted_30d)),
   illustrative cost (SUM(readmitted_30d) × $15,200 — see README for the source).
2. **Risk segments:** bar charts of readmission rate by prior inpatient visits
   (`prior_inpatient_group`), discharge destination (`discharge_group`), and age
   group (`age_group`). Slicers: admission type, diagnosis category, HbA1c tested.
3. **High-risk profiles:** table with the segments in `index.html`
   (3+ prior inpatient visits, 3+ with SNF discharge, 3+ discharged home,
   2 prior visits, 8+ day stays, age 80–90 emergency). Add a drill-through to
   the patient list for each segment.
4. **Model:** forest plot of the adjusted odds ratios from
   `results/odds_ratios.csv` (or re-run the logistic regression in the notebook).

## Measures (DAX / Tableau calculated fields)
- `Readmission rate = DIVIDE(SUM([readmitted_30d]), COUNTROWS(encounters))`
- `Prior inpatient 3+ rate = CALCULATE([Readmission rate], encounters[prior_inpatient_group] = "3+")`

## Design notes
- Keep the KPI cards on top and the segment tables underneath, as in `index.html`.
- Use the same color meaning everywhere: one accent color for the rate bars,
  a second for the high-risk segments.
- Publish the finished dashboard to Tableau Public or Power BI Service and add
  the link to the README.
