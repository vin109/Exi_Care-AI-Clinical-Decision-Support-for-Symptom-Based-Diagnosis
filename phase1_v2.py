import pandas as pd
import numpy as np

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

desc_df = pd.read_csv(os.path.join(BASE_DIR, "DATASETS/symptom_Description.csv"))
prec_df = pd.read_csv(os.path.join(BASE_DIR, "DATASETS/symptom_precaution.csv"))
severity_df = pd.read_csv(os.path.join(BASE_DIR, "DATASETS/Symptom-severity.csv"))

new_df = pd.read_csv(os.path.join(BASE_DIR, "DATASETS/clinical_dataset.csv"))
# ===================== CLEAN SEVERITY =====================
severity_df["Symptom"] = (
    severity_df["Symptom"]
    .astype(str)
    .str.replace("_", " ")
    .str.strip()
    .str.lower()
)

# ===================== CREATE SEVERITY DICTIONARY =====================
severity_dict = dict(zip(severity_df["Symptom"], severity_df["weight"]))

# ===================== LOAD NEW DATASET =====================
new_df = pd.read_csv("DATASETS/clinical_dataset.csv")
new_df = new_df.fillna("")

# ===================== CLEAN TEXT FUNCTION =====================
def clean_text(text):
    if pd.isna(text):
        return ""
    return (
        str(text)
        .lower()
        .replace("_", " ")
        .strip()
    )

# ===================== APPLY CLEANING =====================
for col in desc_df.columns:
    desc_df[col] = desc_df[col].apply(clean_text)

for col in prec_df.columns:
    prec_df[col] = prec_df[col].apply(clean_text)

for col in new_df.columns:
    new_df[col] = new_df[col].apply(clean_text)

# ===================== MERGE OLD DATA =====================
clinical_kb_old = pd.merge(desc_df, prec_df, on="Disease", how="inner")

# ===================== MERGE OLD + NEW =====================
clinical_kb = pd.merge(
    clinical_kb_old,
    new_df,
    on="Disease",
    how="left"
)

# ===================== FIX DESCRIPTION =====================
clinical_kb['Description'] = (
    clinical_kb['Description_x'].fillna('').str.strip() + ". " +
    clinical_kb['Description_y'].fillna('').str.strip()
).str.strip()

# Drop duplicate columns
clinical_kb.drop(['Description_x', 'Description_y'], axis=1, inplace=True)

# ===================== CLEAN IMPORTANT FIELDS =====================
for col in ["Symptoms", "Physical_Exam", "Pathognomonic_Sign", "Description"]:
    if col in clinical_kb.columns:
        clinical_kb[col] = clinical_kb[col].apply(clean_text)

# ===================== 🔥 CREATE STRUCTURED TEXT (IMPORTANT) =====================
clinical_kb["Full_Text"] = (
    "description: " + clinical_kb["Description"].fillna("") + ". " +
    "symptoms: " + clinical_kb.get("Symptoms", "").fillna("") + ". " +
    "physical exam: " + clinical_kb.get("Physical_Exam", "").fillna("") + ". " +
    "pathognomonic sign: " + clinical_kb.get("Pathognomonic_Sign", "").fillna("")
)

# Remove extra spaces
clinical_kb["Full_Text"] = clinical_kb["Full_Text"].str.replace(r"\s+", " ", regex=True)

# ===================== 🔥 COMPUTE DISEASE SEVERITY =====================
def compute_disease_severity(symptoms_text):
    total = 0
    count = 0

    for s in str(symptoms_text).split(","):
        s = s.strip().lower()

        if s in severity_dict:
            total += severity_dict[s]
            count += 1

    return int(total / count) if count else 0

if "Symptoms" in clinical_kb.columns:
    clinical_kb["Severity"] = clinical_kb["Symptoms"].apply(compute_disease_severity)
else:
    clinical_kb["Severity"] = 0

# ===================== REMOVE DUPLICATES =====================
clinical_kb = clinical_kb.drop_duplicates(subset="Disease")

# ===================== AVAILABLE SYMPTOMS =====================
available_symptoms = severity_df["Symptom"].unique().tolist()

# ===================== DEBUG =====================
print("✅ Phase1_v2 UPGRADED Successfully")
print(f"Total Diseases: {len(clinical_kb)}")
print(f"Total Symptoms: {len(available_symptoms)}")

print("\nColumns in clinical_kb:")
print(clinical_kb.columns.tolist())

print("\nSample Full_Text:")
print(clinical_kb["Full_Text"].iloc[0][:300])