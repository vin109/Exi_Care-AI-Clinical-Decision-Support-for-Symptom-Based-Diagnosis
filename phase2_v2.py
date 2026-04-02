from sentence_transformers import SentenceTransformer, util
import torch
import pandas as pd

# 🔥 IMPORTANT: use upgraded phase1_v2
from phase1_v2 import clinical_kb

# ===================== LOAD MODEL =====================
model = SentenceTransformer('all-MiniLM-L6-v2')

# ===================== PREPARE DATA =====================

descriptions = clinical_kb["Full_Text"].fillna("").tolist()
disease_names = clinical_kb["Disease"].tolist()

disease_lookup = clinical_kb.set_index("Disease")

# ===================== PRECOMPUTE EMBEDDINGS =====================
description_embeddings = model.encode(
    descriptions,
    convert_to_tensor=True,
    normalize_embeddings=True
)

# ===================== 🔥 SEVERITY ENGINE =====================

def rule_based_severity(symptoms_text):
    text = str(symptoms_text).lower()

    # 🔴 HIGH
    high_keywords = [
        "chest pain", "shortness of breath", "breathlessness",
        "confusion", "unconscious", "seizure",
        "bleeding", "low blood pressure", "fainting"
    ]

    # 🟡 MEDIUM
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
        from groq import Groq
        import os

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


# ===================== MAIN FUNCTION =====================
def semantic_diagnostic_engine_v2(user_input_text, top_k=5):
    """
    Enhanced semantic search using structured clinical knowledge.
    """

    user_input_text = str(user_input_text).lower().strip()

    # 🔥 GET SEVERITY ONCE
    severity = get_severity(user_input_text)

    # Convert user input → embedding
    user_embedding = model.encode(
        user_input_text,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    cosine_scores = util.cos_sim(user_embedding, description_embeddings)[0]

    top_results = torch.topk(cosine_scores, k=top_k)

    predictions = []

    for score, idx in zip(top_results.values, top_results.indices):
        disease = disease_names[idx]

        row = disease_lookup.loc[disease]

        precautions = [
            row.get('Precaution_1', ''),
            row.get('Precaution_2', ''),
            row.get('Precaution_3', ''),
            row.get('Precaution_4', '')
        ]

        precautions = [p for p in precautions if isinstance(p, str) and p.strip()]

        predictions.append({
            "Disease": disease,
            "Match_Score": round(float(score), 4),
            "Description": row.get('Description', ''),
            "Symptoms": row.get('Symptoms', ''),
            "Physical_Exam": row.get('Physical_Exam', ''),
            "Pathognomonic_Sign": row.get('Pathognomonic_Sign', ''),
            "Precautions": precautions,
            "Severity": severity   # 🔥 DYNAMIC NOW
        })

    return predictions


# ===================== TEST =====================
if __name__ == "__main__":
    test_input = "chest pain and breathlessness"
    results = semantic_diagnostic_engine_v2(test_input)

    print("\nTop Predictions:\n")
    for r in results:
        print(r)