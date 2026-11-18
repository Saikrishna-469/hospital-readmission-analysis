# Data dictionary

Source file: `diabetic_data.csv` (UCI Diabetes 130-US Hospitals, 1999–2008).
The raw file is **not** committed to this repo (see `.gitignore`); download it
from the UCI Machine Learning Repository and place it in `data/`.
`IDs_mapping.csv` from the same download maps the ID columns to labels.

## Encounter identifiers
| Column | Type | Description |
|---|---|---|
| encounter_id | int | Unique encounter identifier |
| patient_nbr | int | Unique patient identifier (patients can have multiple encounters) |

## Demographics
| Column | Type | Description |
|---|---|---|
| race | string | Caucasian, AfricanAmerican, Hispanic, Asian, Other, or `?` (missing, 2.2%) |
| gender | string | Female, Male, or Unknown/Invalid (3 rows, dropped) |
| age | string | 10-year band, e.g. `[70-80)` |
| weight | string | **Dropped**: 96.9% missing |

## Admission and discharge
| Column | Type | Description |
|---|---|---|
| admission_type_id | int | 1 Emergency, 2 Urgent, 3 Elective, 4 Newborn, 5 Not Available, 6 NULL, 7 Trauma Center, 8 Not Mapped |
| discharge_disposition_id | int | 1 Home, 2 Other short-term hospital, 3 SNF, 4 ICF, 5 Other inpatient institution, 6 Home with home health, 7 Left AMA, 11 Expired, 13/14 Hospice, 19–21 Expired (Medicaid hospice), 22 Rehab, 23 Long-term care hospital, and others (see `IDs_mapping.csv`) |
| admission_source_id | int | 1 Physician referral, 2 Clinic referral, 7 Emergency Room, and others |
| time_in_hospital | int | Length of stay in days (1–14) |
| payer_code | string | **Dropped**: 39.6% missing |
| medical_specialty | string | **Dropped**: 49.1% missing |

## Utilization (year before the encounter)
| Column | Type | Description |
|---|---|---|
| number_outpatient | int | Outpatient visits in the prior year |
| number_emergency | int | Emergency visits in the prior year |
| number_inpatient | int | Inpatient visits in the prior year |
| number_diagnoses | int | Number of diagnoses recorded (1–16) |

## Clinical
| Column | Type | Description |
|---|---|---|
| num_lab_procedures | int | Number of lab procedures during the encounter |
| num_procedures | int | Number of procedures (non-lab) during the encounter |
| num_medications | int | Number of medications administered |
| diag_1 / diag_2 / diag_3 | string | Primary / secondary / tertiary ICD-9 diagnosis code (`?` = missing) |
| max_glu_serum | string | Glucose serum test result: None, Norm, >200, >300 |
| A1Cresult | string | HbA1c test result: None (not tested, 83%), Norm, >7, >8 |
| metformin … insulin, glyburide-metformin, etc. | string | Medication status: No, Down, Steady, Up |
| change | string | Ch = diabetes medication changed during the encounter, No = unchanged |
| diabetesMed | string | Yes = diabetes medication prescribed, No = not prescribed |

## Target
| Column | Type | Description |
|---|---|---|
| readmitted | string | `<30` = readmitted within 30 days, `>30` = readmitted after 30 days, `NO` = not readmitted |
| readmitted_30d | int | Derived target: 1 if `readmitted` = `<30`, else 0 |

## Derived columns in the cleaned `encounters` table
| Column | Description |
|---|---|
| diag_1_category | ICD-9 group of the primary diagnosis: Circulatory (390–459, 785), Respiratory (460–519, 786), Digestive (520–579, 787), Diabetes (250), Injury (800–999), Musculoskeletal (710–739), Genitourinary (580–629, 788), Neoplasms (140–239), Other, Missing |
| admission_type | Emergency / Urgent / Elective / Other-Unknown |
| discharge_group | Home / Home with home health / SNF-rehab-nursing facility / Other hospital-inpatient facility / Left AMA / Other-Unknown |
| prior_inpatient_group | 0 / 1 / 2 / 3+ inpatient visits in the prior year |
| los_group | 1–2 / 3–4 / 5–7 / 8+ days |
| meds_group | 1–10 / 11–20 / 21+ medications |
