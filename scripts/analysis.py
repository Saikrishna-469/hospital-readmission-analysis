"""
Statistical analysis for the hospital readmission project.

Runs on the cleaned cohort in data/hospital_readmission.duckdb
(table `encounters`, one row per patient, n = 69,985).

Produces:
- results/results.json : every number quoted in the README / dashboard
- images/*.png         : charts for the README and the HTML dashboard

Tests:
- Chi-square tests of independence for categorical factors vs readmitted_30d
- Mann-Whitney U tests for numeric factors (readmitted vs not readmitted)
- Logistic regression (statsmodels Logit) with odds ratios and 95% CIs

All findings are associations in this 1999-2008 diabetes dataset, not
causal claims and not medical advice.
"""
import json
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

PROJECT = Path(__file__).resolve().parents[1]
DB = PROJECT / "data" / "hospital_readmission.duckdb"
IMG = PROJECT / "images"
RESULTS = PROJECT / "results"
IMG.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.labelsize": 11, "figure.dpi": 150,
})
BLUE, TEAL, ORANGE, GREY = "#1f77b4", "#2ca02c", "#ff7f0e", "#7f7f7f"

con = duckdb.connect(str(DB), read_only=True)
df = con.execute("SELECT * FROM encounters").fetchdf()
con.close()

N = len(df)
N_READM = int(df["readmitted_30d"].sum())
RATE = round(100 * df["readmitted_30d"].mean(), 2)
print(f"Cohort: {N} patients, {N_READM} readmitted within 30 days ({RATE}%)")

res = {"cohort_n": N, "n_readmitted_30d": N_READM, "readmit_rate_pct": RATE}

# ---------------------------------------------------------------- helpers
def rate_table(col, order=None):
    t = (df.groupby(col)["readmitted_30d"]
           .agg(["count", "sum", "mean"])
           .rename(columns={"count": "n", "sum": "n_readmitted", "mean": "rate"})
           .reset_index())
    t["rate_pct"] = (t["rate"] * 100).round(2)
    if order:
        t[col] = pd.Categorical(t[col], categories=order, ordered=True)
        t = t.sort_values(col)
    return t

def chi2(col):
    ct = pd.crosstab(df[col], df["readmitted_30d"])
    chi2_stat, p, dof, _ = stats.chi2_contingency(ct)
    return {"chi2": round(float(chi2_stat), 2), "dof": int(dof), "p": float(p)}

def mannwhitney(col):
    a = df.loc[df["readmitted_30d"] == 1, col]
    b = df.loc[df["readmitted_30d"] == 0, col]
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"U": float(u), "p": float(p),
            "median_readmitted": float(a.median()), "median_not": float(b.median()),
            "mean_readmitted": round(float(a.mean()), 2), "mean_not": round(float(b.mean()), 2)}

# ---------------------------------------------------------------- chi-square
cat_factors = {
    "age_group": ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
                  "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"],
    "race": None, "gender": None, "admission_type": None,
    "discharge_group": None, "diag_1_category": None,
    "prior_inpatient_group": ["0", "1", "2", "3+"],
    "los_group": ["1-2 days", "3-4 days", "5-7 days", "8+ days"],
    "meds_group": ["1-10", "11-20", "21+"],
}
chi_results = {}
for col, order in cat_factors.items():
    t = rate_table(col, order)
    res[f"by_{col}"] = t.to_dict("records")
    chi_results[col] = chi2(col)
    print(f"\n{col}: chi2={chi_results[col]['chi2']}, p={chi_results[col]['p']:.2e}")
    print(t.to_string(index=False))
res["chi_square"] = chi_results

# A1C tested vs not, medication change, diabetes med (binary factors)
df["a1c_tested"] = np.where(df["A1Cresult"] == "None", "Not tested", "Tested")
df["med_change"] = np.where(df["change"] == "Ch", "Changed", "No change")
df["diab_med"] = np.where(df["diabetesMed"] == "Yes", "Yes", "No")
for col in ["a1c_tested", "med_change", "diab_med", "A1Cresult"]:
    t = rate_table(col)
    res[f"by_{col}"] = t.to_dict("records")
    chi_results[col] = chi2(col)
    print(f"\n{col}: chi2={chi_results[col]['chi2']}, p={chi_results[col]['p']:.2e}")
    print(t.to_string(index=False))
res["chi_square"].update({k: v for k, v in chi_results.items() if k in
                          ["a1c_tested", "med_change", "diab_med", "A1Cresult"]})

# ---------------------------------------------------------------- Mann-Whitney
num_cols = ["time_in_hospital", "num_medications", "num_lab_procedures",
            "number_inpatient", "number_emergency", "number_diagnoses",
            "num_procedures", "number_outpatient"]
mw = {}
for col in num_cols:
    mw[col] = mannwhitney(col)
    print(f"{col}: median readm {mw[col]['median_readmitted']} vs not "
          f"{mw[col]['median_not']}, p={mw[col]['p']:.2e}")
res["mann_whitney"] = mw

# ---------------------------------------------------------------- discharge x prior inpatient
cross = (df.groupby(["discharge_group", "prior_inpatient_group"])["readmitted_30d"]
           .agg(["count", "mean"]).reset_index())
cross["rate_pct"] = (cross["mean"] * 100).round(2)
res["discharge_x_prior_inpatient"] = cross.to_dict("records")

# high-risk profile: 3+ prior inpatient visits
for label, mask in {
    "prior_inpatient_3plus": df["number_inpatient"] >= 3,
    "prior_inpatient_3plus_and_snf": (df["number_inpatient"] >= 3)
        & (df["discharge_group"] == "SNF / rehab / nursing facility"),
    "prior_inpatient_3plus_and_home": (df["number_inpatient"] >= 3)
        & (df["discharge_group"] == "Home"),
    "age_80plus_emergency": (df["age_group"].isin(["[80-90)", "[90-100)"]))
        & (df["admission_type"] == "Emergency"),
    "los_8plus": df["time_in_hospital"] >= 8,
}.items():
    sub = df[mask]
    res[label] = {"n": int(len(sub)), "n_readmitted": int(sub["readmitted_30d"].sum()),
                  "rate_pct": round(100 * sub["readmitted_30d"].mean(), 2)}
    print(label, res[label])

# ---------------------------------------------------------------- logistic regression
# Reference categories chosen as the largest / lowest-risk group for readability.
model_df = df.copy()
model_df["race"] = model_df["race"].fillna("Missing")
dummies = pd.get_dummies(
    model_df[["age_group", "race", "gender", "admission_type", "discharge_group",
              "diag_1_category", "prior_inpatient_group", "los_group",
              "meds_group", "a1c_tested", "med_change", "diab_med"]],
    drop_first=False, dtype=float)
# drop reference columns
refs = ["age_group_[50-60)", "race_Caucasian", "gender_Male",
        "admission_type_Elective", "discharge_group_Home",
        "diag_1_category_Other", "prior_inpatient_group_0",
        "los_group_1-2 days", "meds_group_1-10",
        "a1c_tested_Not tested", "med_change_No change", "diab_med_No"]
X = dummies.drop(columns=[c for c in refs if c in dummies.columns])
X = sm.add_constant(X)
y = model_df["readmitted_30d"].astype(float)
logit = sm.Logit(y, X).fit(disp=0, maxiter=200)
print(logit.summary())
params = logit.params
conf = logit.conf_int()
or_table = pd.DataFrame({
    "odds_ratio": np.exp(params),
    "ci_low": np.exp(conf[0]),
    "ci_high": np.exp(conf[1]),
    "p": logit.pvalues,
}).drop(index="const").sort_values("odds_ratio", ascending=False)
or_table.index.name = "variable"
res["logistic_regression"] = {
    "n_obs": int(logit.nobs),
    "pseudo_r2": round(float(logit.prsquared), 4),
    "odds_ratios": or_table.reset_index().to_dict("records"),
}
print(or_table.round(3).to_string())
or_table.to_csv(RESULTS / "odds_ratios.csv")

# ---------------------------------------------------------------- cost illustration
# AHRQ HCUP Statistical Brief #278 (Weiss & Jiang, 2021): average 30-day
# readmission cost $15,200 (2018 USD). Used only as an illustrative
# national average, not a diabetes-specific cost.
COST_PER_READMISSION = 15200
res["cost"] = {
    "source": "AHRQ HCUP Statistical Brief #278 (Weiss & Jiang, 2021): "
              "average 30-day readmission cost $15,200 (2018 USD)",
    "cost_per_readmission_usd": COST_PER_READMISSION,
    "cohort_readmissions_cost_usd": N_READM * COST_PER_READMISSION,
    "high_risk_3plus_readmissions": res["prior_inpatient_3plus"]["n_readmitted"],
    "high_risk_3plus_cost_usd": res["prior_inpatient_3plus"]["n_readmitted"] * COST_PER_READMISSION,
    "high_risk_20pct_reduction_avoided": round(res["prior_inpatient_3plus"]["n_readmitted"] * 0.20),
    "high_risk_20pct_reduction_savings_usd": round(res["prior_inpatient_3plus"]["n_readmitted"] * 0.20) * COST_PER_READMISSION,
}
print("\nCost illustration:", json.dumps(res["cost"], indent=2))

with open(RESULTS / "results.json", "w") as f:
    json.dump(res, f, indent=2, default=str)
print("\nSaved results/results.json")

# ---------------------------------------------------------------- charts
def bar_chart(data, x, y, title, xlabel, ylabel, fname, horizontal=False,
              color=BLUE, annotate=True):
    fig, ax = plt.subplots(figsize=(9, 5))
    if horizontal:
        ax.barh(data[x], data[y], color=color)
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.invert_yaxis()
        if annotate:
            for i, v in enumerate(data[y]):
                ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=10)
        ax.set_xlim(0, max(data[y]) * 1.25)
    else:
        ax.bar(data[x], data[y], color=color)
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        if annotate:
            for i, v in enumerate(data[y]):
                ax.text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=10)
        ax.set_ylim(0, max(data[y]) * 1.2)
        plt.xticks(rotation=30, ha="right")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / fname, bbox_inches="tight")
    plt.close(fig)

age = pd.DataFrame(res["by_age_group"])
bar_chart(age, "age_group", "rate_pct", "30-day readmission rate rises with age",
          "Age group", "Readmitted within 30 days (%)", "readmission_by_age.png")

prior = pd.DataFrame(res["by_prior_inpatient_group"])
bar_chart(prior, "prior_inpatient_group", "rate_pct",
          "Prior inpatient visits are the strongest single signal",
          "Inpatient visits in the year before", "Readmitted within 30 days (%)",
          "readmission_by_prior_inpatient.png", color=ORANGE)

dis = pd.DataFrame(res["by_discharge_group"]).sort_values("rate_pct")
bar_chart(dis, "discharge_group", "rate_pct",
          "Patients discharged to a facility readmit far more often",
          "Readmitted within 30 days (%)", "Discharge destination",
          "readmission_by_discharge.png", horizontal=True, color=TEAL)

los = pd.DataFrame(res["by_los_group"])
bar_chart(los, "los_group", "rate_pct",
          "Longer stays are associated with higher readmission",
          "Length of stay", "Readmitted within 30 days (%)",
          "readmission_by_los.png")

diag = pd.DataFrame(res["by_diag_1_category"])
diag = diag[diag["diag_1_category"] != "Missing"].sort_values("rate_pct")
bar_chart(diag, "diag_1_category", "rate_pct",
          "Readmission rate by primary diagnosis (ICD-9 group)",
          "Readmitted within 30 days (%)", "Primary diagnosis",
          "readmission_by_diagnosis.png", horizontal=True)

a1c = pd.DataFrame(res["by_A1Cresult"])
order = ["None", "Norm", ">7", ">8"]
a1c["A1Cresult"] = pd.Categorical(a1c["A1Cresult"], categories=order, ordered=True)
a1c = a1c.sort_values("A1Cresult")
bar_chart(a1c, "A1Cresult", "rate_pct",
          "HbA1c testing: tested patients readmit slightly less often",
          "HbA1c result (None = not tested)", "Readmitted within 30 days (%)",
          "readmission_by_a1c.png", color=TEAL)

# age x gender heatmap
heat = df.pivot_table(index="age_group", columns="gender",
                      values="readmitted_30d", aggfunc="mean") * 100
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(heat.values, cmap="Blues", vmin=0, vmax=12)
ax.set_xticks(range(len(heat.columns))); ax.set_xticklabels(heat.columns)
ax.set_yticks(range(len(heat.index))); ax.set_yticklabels(heat.index)
ax.set_title("30-day readmission rate (%) by age group and gender")
for i in range(len(heat.index)):
    for j in range(len(heat.columns)):
        ax.text(j, i, f"{heat.values[i, j]:.1f}", ha="center", va="center",
                fontsize=10, color="white" if heat.values[i, j] > 6 else "black")
fig.colorbar(im, ax=ax, label="% readmitted")
fig.tight_layout(); fig.savefig(IMG / "age_gender_heatmap.png", bbox_inches="tight")
plt.close(fig)

# forest plot of key odds ratios
key_vars = [
    "prior_inpatient_group_3+", "prior_inpatient_group_2", "prior_inpatient_group_1",
    "discharge_group_SNF / rehab / nursing facility",
    "discharge_group_Other hospital / inpatient facility",
    "los_group_8+ days", "los_group_5-7 days",
    "meds_group_21+", "age_group_[80-90)", "age_group_[70-80)",
    "diag_1_category_Injury", "diag_1_category_Circulatory",
    "a1c_tested_Tested", "med_change_Changed", "diab_med_Yes",
]
or_df = pd.DataFrame(res["logistic_regression"]["odds_ratios"]).set_index("variable")
plot_rows = or_df.loc[[v for v in key_vars if v in or_df.index]].iloc[::-1]
labels = [v.replace("prior_inpatient_group_", "Prior inpatient ")
          .replace("discharge_group_", "Discharge: ")
          .replace("los_group_", "Stay ")
          .replace("meds_group_", "Meds ")
          .replace("age_group_", "Age ")
          .replace("diag_1_category_", "Diagnosis: ")
          .replace("a1c_tested_", "HbA1c ")
          .replace("med_change_", "Med change: ")
          .replace("diab_med_", "Diabetes med: ") for v in plot_rows.index]
fig, ax = plt.subplots(figsize=(9, 6.5))
y_pos = np.arange(len(plot_rows))
ax.errorbar(plot_rows["odds_ratio"], y_pos,
            xerr=[plot_rows["odds_ratio"] - plot_rows["ci_low"],
                  plot_rows["ci_high"] - plot_rows["odds_ratio"]],
            fmt="o", color=BLUE, ecolor=BLUE, capsize=4)
ax.axvline(1.0, color="red", linestyle="--", linewidth=1)
ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel("Odds ratio for readmission within 30 days (vs. reference group)")
ax.set_title("Logistic regression: adjusted odds ratios (95% CI)")
ax.set_xlim(0, max(plot_rows["ci_high"]) * 1.15)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(IMG / "odds_ratios.png", bbox_inches="tight")
plt.close(fig)

print("Charts saved to images/:", sorted(p.name for p in IMG.glob("*.png")))
print("Done.")
