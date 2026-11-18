"""
Load the UCI Diabetes 130-US Hospitals dataset into DuckDB and build the
cleaned analysis cohort.

Source: Strack et al. (2014), "Impact of HbA1c Measurement on Hospital
Readmission Rates", BioMed Research International.
UCI ML Repository: https://archive.ics.uci.edu/dataset/296/diabetes-130-us-hospitals-for-years-1999-2008
Raw file: diabetic_data.csv (101,766 encounters, 1999-2008)

Cleaning decisions (each is documented here and in the notebook):
1. '?' placeholders are treated as NULL.
2. `weight` is dropped: 96.9% missing, unusable.
3. `payer_code` is dropped: 39.6% missing, and payer is not part of the
   business question.
4. `medical_specialty` is dropped: 49.1% missing, and specialty is not part
   of the business question.
5. Gender 'Unknown/Invalid' (3 rows) is dropped.
6. Encounters ending in death or hospice (discharge_disposition_id in
   11, 13, 14, 19, 20, 21) are excluded: those patients cannot be readmitted,
   so including them would bias the readmission rate down.
7. Encounters where the patient was still in hospital (discharge 12, "Still
   patient") are excluded: the 30-day outcome is not yet observed.
8. Repeat patients: only the FIRST encounter per patient is kept (lowest
   encounter_id). 16,773 patients have more than one encounter (max 40).
   Keeping one row per patient avoids double-counting the same person and
   keeps the chi-square tests' independence assumption valid.
9. Diagnosis codes (ICD-9) are grouped into broad categories following
   Strack et al. (2014): Circulatory, Respiratory, Digestive, Diabetes,
   Injury, Musculoskeletal, Genitourinary, Neoplasms, Other.
10. Target: readmitted_30d = 1 when readmitted = '<30', else 0.
    (NO and '>30' both count as "not readmitted within 30 days".)

Outputs:
- data/hospital_readmission.duckdb with tables encounters_raw and encounters
- prints the cohort flow (row counts at each step)
"""
import shutil
from pathlib import Path
import duckdb

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"
RAW_SRC = Path("/tmp/diabetes_uci/dataset_diabetes/diabetic_data.csv")
RAW = DATA / "diabetic_data.csv"
DB = DATA / "hospital_readmission.duckdb"

DATA.mkdir(parents=True, exist_ok=True)
if not RAW.exists():
    shutil.copy(RAW_SRC, RAW)
    print(f"Copied raw data to {RAW}")
else:
    print(f"Raw data already at {RAW}")

if DB.exists():
    DB.unlink()
con = duckdb.connect(str(DB))

con.execute(f"""
    CREATE TABLE encounters_raw AS
    SELECT * FROM read_csv_auto('{RAW}', header=True, all_varchar=True)
""")
n_raw = con.execute("SELECT COUNT(*) FROM encounters_raw").fetchone()[0]
print(f"Raw rows loaded: {n_raw}")

con.execute("""
CREATE TABLE encounters AS
WITH typed AS (
    SELECT
        CAST(encounter_id AS BIGINT) AS encounter_id,
        CAST(patient_nbr AS BIGINT) AS patient_nbr,
        NULLIF(race, '?') AS race,
        gender,
        age AS age_group,
        CAST(admission_type_id AS INTEGER) AS admission_type_id,
        CAST(discharge_disposition_id AS INTEGER) AS discharge_disposition_id,
        CAST(admission_source_id AS INTEGER) AS admission_source_id,
        CAST(time_in_hospital AS INTEGER) AS time_in_hospital,
        CAST(num_lab_procedures AS INTEGER) AS num_lab_procedures,
        CAST(num_procedures AS INTEGER) AS num_procedures,
        CAST(num_medications AS INTEGER) AS num_medications,
        CAST(number_outpatient AS INTEGER) AS number_outpatient,
        CAST(number_emergency AS INTEGER) AS number_emergency,
        CAST(number_inpatient AS INTEGER) AS number_inpatient,
        NULLIF(diag_1, '?') AS diag_1,
        NULLIF(diag_2, '?') AS diag_2,
        NULLIF(diag_3, '?') AS diag_3,
        CAST(number_diagnoses AS INTEGER) AS number_diagnoses,
        max_glu_serum,
        A1Cresult,
        change,
        diabetesMed,
        readmitted
    FROM encounters_raw
),
first_encounter AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY patient_nbr ORDER BY encounter_id) AS rn
    FROM typed
    WHERE gender <> 'Unknown/Invalid'
      AND discharge_disposition_id NOT IN (11, 13, 14, 19, 20, 21, 12)
),
diag_cat AS (
    SELECT *,
        CASE
            WHEN diag_1 ~ '^(250|251)' THEN 'Diabetes'
            WHEN diag_1 ~ '^(39[0-9]|4[0-5][0-9]|785)' THEN 'Circulatory'
            WHEN diag_1 ~ '^(46[0-9]|47[0-9]|48[0-9]|49[0-9]|5[0-1][0-9]|786)' THEN 'Respiratory'
            WHEN diag_1 ~ '^(52[0-9]|53[0-9]|54[0-9]|55[0-9]|56[0-9]|57[0-9]|787)' THEN 'Digestive'
            WHEN diag_1 ~ '^(80[0-9]|81[0-9]|82[0-9]|83[0-9]|84[0-9]|85[0-9]|86[0-9]|87[0-9]|88[0-9]|89[0-9]|9[0-9][0-9])' THEN 'Injury'
            WHEN diag_1 ~ '^(71[0-9]|72[0-9]|73[0-9])' THEN 'Musculoskeletal'
            WHEN diag_1 ~ '^(58[0-9]|59[0-9]|6[0-2][0-9]|788)' THEN 'Genitourinary'
            WHEN diag_1 ~ '^(14[0-9]|15[0-9]|16[0-9]|17[0-9]|18[0-9]|19[0-9]|2[0-3][0-9])' THEN 'Neoplasms'
            WHEN diag_1 IS NULL THEN 'Missing'
            ELSE 'Other'
        END AS diag_1_category,
        CASE
            WHEN admission_type_id = 1 THEN 'Emergency'
            WHEN admission_type_id = 2 THEN 'Urgent'
            WHEN admission_type_id = 3 THEN 'Elective'
            ELSE 'Other/Unknown'
        END AS admission_type,
        CASE
            WHEN discharge_disposition_id = 1 THEN 'Home'
            WHEN discharge_disposition_id IN (6, 8) THEN 'Home with home health'
            WHEN discharge_disposition_id IN (3, 4, 15, 22, 23, 24, 27) THEN 'SNF / rehab / nursing facility'
            WHEN discharge_disposition_id IN (2, 5, 9, 29, 30) THEN 'Other hospital / inpatient facility'
            WHEN discharge_disposition_id = 7 THEN 'Left AMA'
            ELSE 'Other/Unknown'
        END AS discharge_group,
        CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END AS readmitted_30d,
        CASE
            WHEN number_inpatient = 0 THEN '0'
            WHEN number_inpatient = 1 THEN '1'
            WHEN number_inpatient = 2 THEN '2'
            ELSE '3+'
        END AS prior_inpatient_group,
        CASE
            WHEN time_in_hospital <= 2 THEN '1-2 days'
            WHEN time_in_hospital <= 4 THEN '3-4 days'
            WHEN time_in_hospital <= 7 THEN '5-7 days'
            ELSE '8+ days'
        END AS los_group,
        CASE
            WHEN num_medications <= 10 THEN '1-10'
            WHEN num_medications <= 20 THEN '11-20'
            ELSE '21+'
        END AS meds_group
    FROM first_encounter
    WHERE rn = 1
)
SELECT * EXCLUDE (rn) FROM diag_cat
""")

n_clean = con.execute("SELECT COUNT(*) FROM encounters").fetchone()[0]
n_readm = con.execute("SELECT SUM(readmitted_30d) FROM encounters").fetchone()[0]
rate = con.execute("SELECT ROUND(100.0 * AVG(readmitted_30d), 2) FROM encounters").fetchone()[0]
print(f"Analysis cohort rows (one per patient): {n_clean}")
print(f"Readmitted within 30 days: {n_readm} ({rate}%)")
print(f"Distinct patients in cohort: {con.execute('SELECT COUNT(DISTINCT patient_nbr) FROM encounters').fetchone()[0]}")
print("Cohort flow:")
print(f"  raw encounters: {n_raw}")
print(f"  after exclusions + first encounter per patient: {n_clean}")

# sanity: verify no duplicates remain and target has no nulls
print("Null readmitted_30d:", con.execute("SELECT COUNT(*) FROM encounters WHERE readmitted_30d IS NULL").fetchone()[0])
print("Done. DuckDB file:", DB)
con.close()
