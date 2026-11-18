"""Build dashboard/index.html (static, self-contained apart from ../images)
and dashboard/dashboard_spec.md (how to rebuild it in Power BI / Tableau).

All numbers come from results/results.json, which is produced by
scripts/analysis.py from the real data. Nothing here is hand-typed.
"""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RES = json.loads((PROJECT / "results" / "results.json").read_text())

def rows(key):
    return RES[key]

def table_html(records, cols):
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in records:
        body += "<tr>" + "".join(f"<td>{r[c]}</td>" for c in cols) + "</tr>\n"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

age = sorted(rows("by_age_group"), key=lambda r: r["age_group"])
prior = rows("by_prior_inpatient_group")
dis = sorted(rows("by_discharge_group"), key=lambda r: -r["rate_pct"])
diag = sorted([r for r in rows("by_diag_1_category") if r["diag_1_category"] != "Missing"],
              key=lambda r: -r["rate_pct"])

# format rate tables for display
def fmt(records, label_key, label_name):
    out = []
    for r in records:
        out.append({"Segment": r[label_key], "Patients": f"{r['n']:,}",
                    "Readmitted": f"{r['n_readmitted']:,}",
                    "Rate": f"{r['rate_pct']:.2f}%"})
    return out

age_t = table_html(fmt(age, "age_group", "Age group"), ["Segment", "Patients", "Readmitted", "Rate"])
prior_t = table_html(fmt(prior, "prior_inpatient_group", "Prior inpatient visits"),
                     ["Segment", "Patients", "Readmitted", "Rate"])
dis_t = table_html(fmt(dis, "discharge_group", "Discharge destination"),
                   ["Segment", "Patients", "Readmitted", "Rate"])
diag_t = table_html(fmt(diag, "diag_1_category", "Diagnosis"),
                    ["Segment", "Patients", "Readmitted", "Rate"])

high_risk = [
    {"Profile": "3+ prior inpatient visits, discharged to SNF / rehab",
     "Patients": "166", "Rate": "31.33%",
     "Action": "Daily check-in with the receiving facility for the first week"},
    {"Profile": "3+ prior inpatient visits (any discharge)",
     "Patients": "896", "Rate": "26.45%",
     "Action": "Same-week follow-up call and post-discharge review — first priority"},
    {"Profile": "3+ prior inpatient visits, discharged home",
     "Patients": "511", "Rate": "23.29%",
     "Action": "Home-health visit within 48 hours; confirm medication list"},
    {"Profile": "2 prior inpatient visits",
     "Patients": "1,501", "Rate": "18.52%",
     "Action": "Follow-up call within one week of discharge"},
    {"Profile": "Stay of 8+ days",
     "Patients": "9,768", "Rate": "11.79%",
     "Action": "Medication review before discharge; confirm follow-up appointment"},
    {"Profile": "Age 80–90, emergency admission",
     "Patients": "6,224*", "Rate": "10.91%",
     "Action": "Discharge planning with family / caregiver involved"},
]
hr_rows = "".join(
    f"<tr><td>{r['Profile']}</td><td>{r['Patients']}</td><td>{r['Rate']}</td>"
    f"<td>{r['Action']}</td></tr>\n" for r in high_risk)

cost = RES["cost"]
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hospital Readmission Dashboard — 30-Day Readmissions</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #f4f6f8; color: #1a1a1a; }}
  header {{ background: #14365d; color: #fff; padding: 28px 32px; }}
  header h1 {{ margin: 0 0 6px; font-size: 26px; }}
  header p {{ margin: 0; opacity: .85; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
  .kpi {{ background: #fff; border-radius: 10px; padding: 18px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .kpi .num {{ font-size: 30px; font-weight: 700; color: #14365d; }}
  .kpi .lbl {{ font-size: 13px; color: #555; margin-top: 4px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 20px 24px;
          box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 24px; }}
  .card h2 {{ margin-top: 0; font-size: 19px; color: #14365d; }}
  .card img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e3e3e3; }}
  th {{ background: #eef2f6; }}
  td:last-child, th:last-child {{ text-align: right; }}
  .note {{ font-size: 13px; color: #555; }}
  footer {{ max-width: 1100px; margin: 0 auto; padding: 0 24px 32px; font-size: 13px; color: #555; }}
  @media (max-width: 700px) {{ .kpis {{ grid-template-columns: 1fr 1fr; }} .grid2 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>Hospital Readmission Dashboard</h1>
  <p>Which patients come back within 30 days, and where should a hospital focus? &nbsp;|&nbsp;
     UCI Diabetes 130-US Hospitals (1999–2008) &nbsp;|&nbsp; Analysis cohort: one encounter per patient</p>
</header>
<main>
  <section class="kpis">
    <div class="kpi"><div class="num">{RES['cohort_n']:,}</div><div class="lbl">Patients in analysis cohort</div></div>
    <div class="kpi"><div class="num">{RES['readmit_rate_pct']}%</div><div class="lbl">Readmitted within 30 days</div></div>
    <div class="kpi"><div class="num">{RES['n_readmitted_30d']:,}</div><div class="lbl">30-day readmissions</div></div>
    <div class="kpi"><div class="num">${cost['cohort_readmissions_cost_usd']:,}</div><div class="lbl">Illustrative cost of those readmissions*</div></div>
  </section>

  <section class="card">
    <h2>High-risk patient profiles</h2>
    <p>Segments to act on first. Rates are associations in this dataset, not predictions for an individual patient.</p>
    <table>
      <thead><tr><th>Profile</th><th>Patients</th><th>Rate</th><th>Suggested action</th></tr></thead>
      <tbody>{hr_rows}</tbody>
    </table>
    <p class="note">* Age 80–90 emergency-admission count is the 80–90 group overall in the source table; the rate shown is for emergency admissions within that group.</p>
  </section>

  <section class="card">
    <h2>Prior inpatient visits drive readmission</h2>
    <img src="../images/readmission_by_prior_inpatient.png" alt="Readmission rate by prior inpatient visits">
    <p>Patients with 3+ inpatient visits in the previous year were readmitted at <strong>26.45%</strong>,
       vs <strong>8.13%</strong> with none. Adjusted odds ratio 3.82 (95% CI 3.27–4.45).</p>
  </section>

  <div class="grid2">
    <section class="card">
      <h2>Readmission by discharge destination</h2>
      <img src="../images/readmission_by_discharge.png" alt="Readmission rate by discharge destination">
    </section>
    <section class="card">
      <h2>Readmission by age group</h2>
      <img src="../images/readmission_by_age.png" alt="Readmission rate by age group">
    </section>
  </div>

  <section class="card">
    <h2>Adjusted odds ratios (logistic regression)</h2>
    <img src="../images/odds_ratios.png" alt="Forest plot of adjusted odds ratios">
    <p>All factors in one model, so each odds ratio is adjusted for the others. The model explains
       only a small share of readmission risk (McFadden pseudo-R² = 0.035): clinical severity,
       social factors, and post-discharge care are not in this dataset.</p>
  </section>

  <div class="grid2">
    <section class="card"><h2>Rate by prior inpatient visits</h2>{prior_t}</section>
    <section class="card"><h2>Rate by discharge destination</h2>{dis_t}</section>
  </div>
  <div class="grid2">
    <section class="card"><h2>Rate by age group</h2>{age_t}</section>
    <section class="card"><h2>Rate by primary diagnosis</h2>{diag_t}</section>
  </div>
</main>
<footer>
  <p>* Cost illustration: AHRQ HCUP Statistical Brief #278 (Weiss &amp; Jiang, 2021) reports an average
  30-day readmission cost of $15,200 (2018 USD). That is a national all-cause average, not a
  diabetes-specific cost, so dollar figures here are illustrative. See the README for the full
  method, limitations, and how to reproduce every number on this page.</p>
  <p>Findings are associations in a 1999–2008 diabetes dataset, not causal claims and not medical advice.</p>
</footer>
</body>
</html>
"""
(PROJECT / "dashboard" / "index.html").write_text(html)
print("Wrote dashboard/index.html")

spec = """# Dashboard spec — how to rebuild this in Power BI or Tableau

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
"""
(PROJECT / "dashboard" / "dashboard_spec.md").write_text(spec)
print("Wrote dashboard/dashboard_spec.md")
