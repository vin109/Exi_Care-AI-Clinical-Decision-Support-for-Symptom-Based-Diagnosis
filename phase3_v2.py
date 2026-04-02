from pydantic import BaseModel
from groq import Groq
import os
import pandas as pd

from phase2_v2 import semantic_diagnostic_engine_v2

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ===================== UPDATED REQUEST =====================
class SymptomRequest(BaseModel):
    symptoms: str
    weight: float = 60


# ===================== 🔥 SEVERITY ENGINE =====================

def rule_based_severity(symptoms_text):
    text = str(symptoms_text).lower()

    high_keywords = [
        "chest pain", "shortness of breath", "breathlessness",
        "confusion", "unconscious", "seizure",
        "bleeding", "low blood pressure", "fainting"
    ]

    medium_keywords = [
        "high fever", "persistent fever", "vomiting",
        "severe headache", "abdominal pain", "dehydration",
        "joint pain", "rash"
    ]

    for k in high_keywords:
        if k in text:
            return "High"

    for k in medium_keywords:
        if k in text:
            return "Medium"

    return None


def llm_severity(symptoms_text):
    try:
        prompt = f"""
        Symptoms: {symptoms_text}

        Classify severity:
        Low / Medium / High

        Return only one word.
        """

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )

        return response.choices[0].message.content.strip()
    except:
        return "Low"


def get_severity(symptoms_text):
    severity = rule_based_severity(symptoms_text)

    if severity:
        return severity

    return llm_severity(symptoms_text)


# ===================== GAP FILL =====================
def enrich_missing_fields(disease, client):

    missing_fields = []

    if not disease.get("Symptoms"):
        missing_fields.append("Symptoms")
    if not disease.get("Physical_Exam"):
        missing_fields.append("Physical Examination")
    if not disease.get("Pathognomonic_Sign"):
        missing_fields.append("Pathognomonic Sign")

    if not missing_fields:
        return disease

    prompt = f"""
    Provide the following clinical details for {disease['Disease']}:

    {", ".join(missing_fields)}

    Use format:
    Symptoms:
    Physical Examination:
    Pathognomonic Sign:
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    text = response.choices[0].message.content

    current = None
    symptoms_text = ""
    exam_text = ""
    sign_text = ""

    for line in text.split("\n"):
        l = line.lower().strip()

        if l.startswith("symptom"):
            current = "symptoms"
            continue
        elif l.startswith("physical"):
            current = "exam"
            continue
        elif l.startswith("pathognomonic"):
            current = "sign"
            continue

        if current == "symptoms":
            symptoms_text += line + "\n"
        elif current == "exam":
            exam_text += line + "\n"
        elif current == "sign":
            sign_text += line + "\n"

    if not disease.get("Symptoms"):
        disease["Symptoms"] = symptoms_text.strip()

    if not disease.get("Physical_Exam"):
        disease["Physical_Exam"] = exam_text.strip()

    if not disease.get("Pathognomonic_Sign"):
        disease["Pathognomonic_Sign"] = (
            sign_text.strip() or "No specific pathognomonic sign identified"
        )

    return disease


# ===================== TREATMENT =====================
def get_treatment_llm(disease, age, weight):

    prompt = f"""
    You are a clinical decision support assistant for doctors.

    Disease: {disease}
    Patient Age: {age}
    Patient Weight: {weight} kg

    Provide ONLY:
    - Medicines
    - Dosage (weight-based if needed)

    Keep it short and structured.
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    return response.choices[0].message.content


# ===================== MAIN =====================
async def get_diagnosis_v2(request: SymptomRequest):

    # 🔥 Get matches
    top_matches = semantic_diagnostic_engine_v2(request.symptoms, top_k=3)

    # ===================== 🔥 FIXED SEVERITY =====================
    severity_str = get_severity(request.symptoms)

    severity_map = {
        "Low": 20,
        "Medium": 50,
        "High": 90
    }

    severity = severity_map.get(severity_str, 20)

    for d in top_matches:
        d["Severity"] = severity

    # 🔥 Gap fill
    top_matches = [enrich_missing_fields(d, client) for d in top_matches]

    primary_match = top_matches[0]

    # ===================== AGE EXTRACTION =====================
    age = 25
    try:
        import re
        match = re.search(r'Age:\s*(\d+)', request.symptoms)
        if match:
            age = int(match.group(1))
    except:
        pass

    # ===================== ADD TREATMENT =====================
    for d in top_matches:
        try:
            d["Treatment"] = get_treatment_llm(
                d['Disease'],
                age,
                request.weight
            )
        except:
            d["Treatment"] = "Not available"

    # ===================== FALLBACK =====================
    if primary_match['Match_Score'] < 0.4:

        fallback_prompt = f"""
        You are an expert clinical decision support system.

        Patient symptoms:
        {request.symptoms}

        Task:
        - Identify the most likely diagnosis
        """

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": fallback_prompt}],
            model="llama-3.3-70b-versatile",
        )

        llm_text = response.choices[0].message.content

        return {
            "diagnosis": "AI Inferred Condition",
            "confidence": primary_match['Match_Score'],
            "clinical_summary": llm_text,
            "top_matches": [],
            "raw_data": {},
            "treatment": "Not available",
            "source": "llm"
        }

    # ===================== CONTEXT =====================
    disease_block = "\n".join([
        f"{m['Disease']} ({round(m['Match_Score']*100)}%)"
        for m in top_matches
    ])

    symptoms = primary_match.get('Symptoms', '')
    physical_exam = primary_match.get('Physical_Exam', '')
    path_sign = primary_match.get('Pathognomonic_Sign', '')

    clean_precautions = [
        str(p) for p in primary_match['Precautions']
        if isinstance(p, str) and p.strip()
    ]

    # ===================== SUMMARY =====================
    PROMPT = f"""
    You are a Clinical Decision Support Assistant.

    Patient Symptoms:
    {request.symptoms}

    Top Possible Diagnoses:
    {disease_block}

    Primary Diagnosis:
    {primary_match['Disease']} (confidence: {round(primary_match['Match_Score']*100)}%)

    Medical Description:
    {primary_match['Description']}

    Key Symptoms:
    {symptoms}

    Physical Examination:
    {physical_exam}

    Pathognomonic Sign:
    {path_sign}

    Precautions:
    {", ".join(clean_precautions)}

    Task:
    1. Explain why the primary diagnosis fits best
    2. Compare briefly with other possible diagnoses
    3. Provide urgency level (Low / Medium / High)
    4. Immediate Actions
    5. Further Diagnostics
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": PROMPT}],
        model="llama-3.3-70b-versatile",
    )

    return {
        "diagnosis": primary_match['Disease'],
        "confidence": primary_match['Match_Score'],
        "clinical_summary": response.choices[0].message.content,
        "top_matches": top_matches,
        "treatment": primary_match.get("Treatment", "Not available"),
        "raw_data": {
            "description": primary_match['Description'],
            "symptoms": symptoms,
            "physical_exam": physical_exam,
            "path_sign": path_sign,
            "precautions": clean_precautions
        }
    }