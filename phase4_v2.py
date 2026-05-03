import streamlit as st
import asyncio
import speech_recognition as sr

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from phase3_v2 import get_diagnosis_v2, SymptomRequest

st.set_page_config(page_title="EXiCare AI — Clinical Decision Support", layout="wide", page_icon="🩺")

# ══════════════════════════════════════════════════════
#  GLOBAL STYLES  (only shown after login)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sora:wght@400;600;700;800&display=swap');

html, body { margin: 0; padding: 0; }

.stApp {
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
    background:
        radial-gradient(ellipse 120% 80% at 0% 0%,   #0f3460 0%, transparent 55%),
        radial-gradient(ellipse 100% 70% at 100% 10%, #1a1a4e 0%, transparent 50%),
        radial-gradient(ellipse 80%  60% at 30% 80%,  #0d2137 0%, transparent 55%),
        radial-gradient(ellipse 90%  90% at 80% 90%,  #0a192f 0%, transparent 60%),
        linear-gradient(160deg, #071929 0%, #0a1628 40%, #0c1f3a 70%, #071525 100%) !important;
    color: #e2e8f0 !important;
}

.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
        radial-gradient(circle at 25% 25%, rgba(56,189,248,0.035) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(99,102,241,0.03)  0%, transparent 50%),
        radial-gradient(circle at 50% 10%, rgba(20,184,166,0.025) 0%, transparent 40%);
    pointer-events: none; z-index: 0;
}

.stApp::after {
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none; z-index: 0;
}

header[data-testid="stHeader"] {
    background: rgba(7, 25, 41, 0.85) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.1) !important;
}

.block-container {
    background: transparent !important;
    padding: 2rem 3rem 5rem !important;
    max-width: 1300px !important;
    position: relative; z-index: 1;
}

section[data-testid="stSidebar"] {
    background: rgba(10, 22, 40, 0.92) !important;
    backdrop-filter: blur(24px) saturate(160%) !important;
    border-right: 1px solid rgba(56, 189, 248, 0.1) !important;
    box-shadow: 4px 0 32px rgba(0,0,0,0.3) !important;
}
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] .block-container { padding: 2rem 1.5rem !important; }

section[data-testid="stSidebar"] h2 {
    font-family: 'Sora', sans-serif !important;
    font-size: 0.62rem !important; font-weight: 700 !important;
    letter-spacing: 0.16em !important; text-transform: uppercase !important;
    color: #38bdf8 !important;
    margin-bottom: 1.75rem !important; padding-bottom: 0.75rem !important;
    border-bottom: 1px solid rgba(56,189,248,0.15) !important;
}

section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stSelectbox label {
    font-size: 0.62rem !important; font-weight: 600 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    color: #64748b !important;
}

section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(56,189,248,0.06) !important;
    border: 1px solid rgba(56,189,248,0.28) !important;
    border-radius: 8px !important;
    color: #7dd3fc !important; font-weight: 700 !important;
    font-size: 1rem !important; font-family: 'Courier New', monospace !important;
    letter-spacing: 0.08em !important;
    box-shadow: 0 0 12px rgba(56,189,248,0.08), inset 0 1px 0 rgba(255,255,255,0.04) !important;
}

section[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important; color: #e2e8f0 !important; font-weight: 500 !important;
}

section[data-testid="stSidebar"] [data-testid="stNumberInput"] button {
    background: rgba(56,189,248,0.1) !important;
    border: 1px solid rgba(56,189,248,0.2) !important;
    color: #38bdf8 !important; border-radius: 6px !important; font-weight: 700 !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
}

h1 {
    font-family: 'Sora', sans-serif !important;
    font-size: 2.5rem !important; font-weight: 800 !important;
    letter-spacing: -0.03em !important; line-height: 1.1 !important;
    background: linear-gradient(135deg, #ffffff 0%, #bae6fd 50%, #a5b4fc 100%) !important;
    -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
    background-clip: text !important; margin-bottom: 0 !important;
}
h2 { font-family: 'Sora', sans-serif !important; font-size: 1.25rem !important; font-weight: 700 !important; color: #f1f5f9 !important; }
h3 { font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; font-weight: 700 !important; color: #cbd5e1 !important; margin: 1rem 0 0.5rem !important; }
p, span, div, li { font-family: 'Inter', sans-serif !important; }

hr {
    border: none !important; height: 1px !important; margin: 1.5rem 0 !important;
    background: linear-gradient(90deg, transparent 0%, rgba(56,189,248,0.25) 30%, rgba(99,102,241,0.25) 70%, transparent 100%) !important;
}

.stTextArea label { font-size: 0.62rem !important; font-weight: 700 !important; letter-spacing: 0.14em !important; text-transform: uppercase !important; color: #475569 !important; }
.stTextArea textarea {
    background: rgba(255,255,255,0.03) !important; color: #e2e8f0 !important;
    border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; line-height: 1.7 !important;
    padding: 16px 18px !important; backdrop-filter: blur(8px) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    transition: all 0.25s ease !important;
}
.stTextArea textarea:focus {
    border-color: rgba(56,189,248,0.5) !important;
    background: rgba(56,189,248,0.04) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2), 0 0 0 3px rgba(56,189,248,0.1), inset 0 1px 0 rgba(255,255,255,0.05) !important;
}
.stTextArea textarea::placeholder { color: #334155 !important; font-style: italic !important; }

.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 0.85rem !important; border-radius: 10px !important;
    padding: 11px 22px !important; cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important; border: none !important;
}
.stButton > button:first-child {
    background: linear-gradient(135deg, #0284c7 0%, #7c3aed 100%) !important;
    color: #fff !important;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.1) inset, 0 4px 20px rgba(2,132,199,0.4), 0 1px 3px rgba(0,0,0,0.3) !important;
}
.stButton > button:first-child:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.15) inset, 0 8px 32px rgba(2,132,199,0.55), 0 2px 8px rgba(0,0,0,0.3) !important;
}

.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 0.85rem !important;
    background: rgba(255,255,255,0.05) !important; color: #94a3b8 !important;
    border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important;
    padding: 10px 22px !important; backdrop-filter: blur(8px) !important; transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: rgba(56,189,248,0.1) !important; border-color: rgba(56,189,248,0.35) !important;
    color: #38bdf8 !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(56,189,248,0.15) !important;
}

[data-testid="stProgressBar"] > div { background: rgba(255,255,255,0.06) !important; border-radius: 99px !important; height: 6px !important; border: none !important; }
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #0ea5e9, #8b5cf6) !important; border-radius: 99px !important; box-shadow: 0 0 12px rgba(14,165,233,0.6) !important; }

[data-testid="stInfo"] { background: rgba(14,165,233,0.08) !important; border: 1px solid rgba(14,165,233,0.2) !important; border-left: 3px solid #0ea5e9 !important; border-radius: 12px !important; }
[data-testid="stSuccess"] { background: rgba(16,185,129,0.08) !important; border: 1px solid rgba(16,185,129,0.2) !important; border-left: 3px solid #10b981 !important; border-radius: 12px !important; }
[data-testid="stWarning"] { background: rgba(245,158,11,0.08) !important; border: 1px solid rgba(245,158,11,0.2) !important; border-left: 3px solid #f59e0b !important; border-radius: 12px !important; }
[data-testid="stError"] { background: rgba(239,68,68,0.08) !important; border: 1px solid rgba(239,68,68,0.2) !important; border-left: 3px solid #ef4444 !important; border-radius: 12px !important; }

[data-testid="column"] {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 20px !important; padding: 24px 20px !important;
    backdrop-filter: blur(16px) saturate(160%) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.07) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important; overflow: hidden !important;
}
[data-testid="column"]:hover {
    background: rgba(255,255,255,0.06) !important; border-color: rgba(56,189,248,0.25) !important;
    box-shadow: 0 16px 48px rgba(0,0,0,0.3), 0 0 0 1px rgba(56,189,248,0.15), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    transform: translateY(-3px) !important;
}

.exp-chk { display: none !important; }
.exp-label {
    display: flex !important; align-items: center !important; justify-content: space-between !important;
    padding: 10px 14px !important; border-radius: 10px !important; cursor: pointer !important;
    background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.09) !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; font-weight: 600 !important;
    color: #64748b !important; letter-spacing: 0.02em !important; transition: all 0.15s !important;
    user-select: none !important; margin-bottom: 0 !important;
}
.exp-label:hover { background: rgba(56,189,248,0.07) !important; border-color: rgba(56,189,248,0.25) !important; color: #38bdf8 !important; }
.exp-arrow { display: inline-block !important; transition: transform 0.2s ease !important; font-size: 1.2rem !important; line-height: 1 !important; color: #475569 !important; }
.exp-body { display: none !important; padding: 14px 16px !important; background: rgba(0,0,0,0.15) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-top: none !important; border-bottom-left-radius: 10px !important; border-bottom-right-radius: 10px !important; }

.stSpinner > div { border-top-color: #38bdf8 !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: #475569 !important; font-size: 0.75rem !important; font-weight: 500 !important; }
strong, b { color: #7dd3fc !important; font-weight: 600 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.2); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(56,189,248,0.4); }

[data-baseweb="select"] > div { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
[data-baseweb="select"] span { color: #e2e8f0 !important; }
[data-baseweb="popover"] ul { background: #0d1f35 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; }
[data-baseweb="popover"] li { color: #e2e8f0 !important; }
[data-baseweb="popover"] li:hover { background: rgba(56,189,248,0.1) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════════════════
st.title("🩺 EXiCare AI: Clinical Decision Support System")

st.markdown("""
<p style="font-family:'Inter',sans-serif;font-size:0.9rem;color:#475569;
    margin-top:6px;margin-bottom:0;line-height:1.6;">
  Symptom-based AI diagnostics &nbsp;·&nbsp;
  Probability-weighted differential &nbsp;·&nbsp;
  Clinical reasoning engine
</p>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("---")


# ══════════════════════════════════════════════════════
#  VOICE INPUT
# ══════════════════════════════════════════════════════
def get_voice_input():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak your symptoms")
            audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio)
        st.success(f"🗣️ You said: {text}")
        return text
    except:
        st.error("❌ Could not understand audio")
        return ""


# ══════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.header("👤 Patient Context")

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(14,165,233,0.12) 0%,rgba(99,102,241,0.12) 100%);
    border:1px solid rgba(56,189,248,0.2);border-radius:14px;padding:16px;margin-bottom:20px;">
  <div style="font-family:'Sora',sans-serif;font-size:0.6rem;font-weight:700;
      letter-spacing:0.14em;text-transform:uppercase;color:#64748b;margin-bottom:8px;">
    Patient Record
  </div>
  <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#94a3b8;line-height:1.7;">
    Fill in patient details below.<br>Data is used for AI enrichment only.
  </div>
</div>
""", unsafe_allow_html=True)

    patient_id = st.text_input("Patient Number", "P-001")
    age        = st.number_input("Age", 0, 120, 25)
    gender     = st.selectbox("Gender", ["Male", "Female", "Other"])
    weight     = st.number_input("Weight (kg)", 1, 200, 60)

    st.markdown("---")

    st.markdown("""
<div style="font-family:'Inter',sans-serif;font-size:0.72rem;color:#334155;line-height:1.6;padding:0 2px;">
  ⚠️ For clinical support only.<br>Always verify with clinical expertise.
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  SYMPTOM INPUT SECTION
# ══════════════════════════════════════════════════════
st.subheader("📝 Enter Symptoms")

user_input = st.text_area(
    "Describe symptoms (e.g., fever, headache, abdominal pain)",
    value=st.session_state.get("voice_input", ""),
    height=120
)

if st.button("🎤 Use Voice Input"):
    voice_text = get_voice_input()
    if voice_text:
        st.session_state["voice_input"] = voice_text
        st.rerun()

col1, col2 = st.columns([3, 1])
with col1:
    generate = st.button("⚡ Generate Diagnosis")
with col2:
    refresh = st.button("🔄 Refresh")

if refresh:
    # preserve auth state across refresh
    auth_verified = st.session_state.get("auth_verified", False)
    auth_phone    = st.session_state.get("auth_phone", "")
    st.session_state.clear()
    st.session_state["auth_verified"] = auth_verified
    st.session_state["auth_phone"]    = auth_phone
    st.rerun()

if generate:
    if user_input.strip():
        with st.spinner("Analyzing symptoms with AI..."):
            enriched_input = f"{user_input}, Age: {age}, Gender: {gender}"
            response = asyncio.run(
                get_diagnosis_v2(SymptomRequest(symptoms=enriched_input, weight=weight))
            )
            st.session_state['result'] = response
    else:
        st.warning("⚠️ Please enter symptoms before generating diagnosis")


# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════
def safe_display(value):
    if isinstance(value, str) and value.strip() and value.lower() != "nan":
        return value
    return None


def dblock(label, value):
    return f"""<div style="margin-bottom:14px;">
  <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;
      text-transform:uppercase;color:#475569;margin-bottom:4px;
      font-family:'Inter',sans-serif;">{label}</div>
  <div style="font-size:0.85rem;color:#94a3b8;line-height:1.65;
      font-family:'Inter',sans-serif;">{value}</div>
</div>"""


def generate_pdf(result, patient_id, age, gender, weight):
    import os
    doc    = SimpleDocTemplate("report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    title_style    = ParagraphStyle('title',    parent=styles['Heading1'], alignment=1, spaceAfter=12)
    subtitle_style = ParagraphStyle('subtitle', parent=styles['Normal'],  alignment=1, textColor=colors.grey, spaceAfter=15)
    section_style  = ParagraphStyle('section',  parent=styles['Heading3'], textColor=colors.darkblue, spaceAfter=8)
    content = []

    try:
        BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
        banner_path = os.path.join(BASE_DIR, "banner1.png")
        if os.path.exists(banner_path):
            content.append(Image(banner_path, width=7*inch, height=1.2*inch))
            content.append(Spacer(1, 10))
        else:
            content.append(Paragraph("EXiCare AI", title_style))
    except:
        content.append(Paragraph("EXiCare AI", title_style))

    content.append(Paragraph("Clinical Decision Support Report", subtitle_style))
    content.append(Spacer(1, 10))

    table_data = [
        ["Patient ID", patient_id, "Age", str(age)],
        ["Gender", gender, "Weight", f"{weight} kg"]
    ]
    table = Table(table_data, colWidths=[80,150,80,100])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey)
    ]))
    content.append(table)
    content.append(Spacer(1, 15))

    content.append(Paragraph("Diagnosis", section_style))
    content.append(Paragraph(f"{result['diagnosis']} (Confidence: {int(result['confidence']*100)}%)", styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("Clinical Summary", section_style))
    for line in result['clinical_summary'].split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 5))
    content.append(Spacer(1, 10))

    content.append(Paragraph("Suggested Clinical Management", section_style))
    for line in result.get("treatment", "").split("\n"):
        if line.strip():
            content.append(Paragraph(f"• {line}", styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("⚠️ This report is generated by EXiCare AI for clinical decision support only.", styles['Normal']))
    doc.build(content)

    with open("report.pdf", "rb") as f:
        return f.read()


# ══════════════════════════════════════════════════════
#  DEFAULT STATE
# ══════════════════════════════════════════════════════
if 'result' not in st.session_state:
    st.markdown("""
<div style="background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.14);
    border-left:3px solid #0ea5e9;border-radius:12px;padding:16px 20px;
    backdrop-filter:blur(8px);margin-top:8px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:18px;">👆</span>
    <span style="font-family:'Inter',sans-serif;font-size:0.88rem;color:#bae6fd;font-weight:500;">
      Enter symptoms above and click <strong style="color:#38bdf8;">Generate Diagnosis</strong> to begin analysis.
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  RESULTS
# ══════════════════════════════════════════════════════
if 'result' in st.session_state:
    result     = st.session_state['result']
    confidence = result['confidence']
    is_llm     = result.get("source") == "llm"

    pdf_data = generate_pdf(result, patient_id, age, gender, weight)
    st.download_button(
        label="📄 Download Report", data=pdf_data,
        file_name="diagnosis_report.pdf", mime="application/pdf"
    )

    if is_llm:
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin:1.5rem 0 6px;">
  <div style="width:3px;height:18px;background:linear-gradient(180deg,#a78bfa,#38bdf8);border-radius:99px;"></div>
  <span style="font-family:'Inter',sans-serif;font-size:0.62rem;font-weight:700;
      letter-spacing:0.14em;text-transform:uppercase;color:#64748b;">AI Reasoning</span>
</div>
""", unsafe_allow_html=True)
        st.subheader("🧠 AI Clinical Reasoning")
        st.success(f"Primary Diagnosis: {result['diagnosis']} (AI inferred)")
        st.caption("⚠️ Advanced reasoning used")
        st.markdown("### 📋 Clinical Summary")
        st.info(result['clinical_summary'])

    else:
        top_matches = result.get('top_matches', [])
        if not top_matches:
            st.warning("No matching diseases found.")
        else:
            st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin:1.5rem 0 6px;">
  <div style="width:3px;height:18px;background:linear-gradient(180deg,#38bdf8,#8b5cf6);border-radius:99px;"></div>
  <span style="font-family:'Inter',sans-serif;font-size:0.62rem;font-weight:700;
      letter-spacing:0.14em;text-transform:uppercase;color:#64748b;">Differential Diagnosis</span>
</div>
""", unsafe_allow_html=True)
            st.subheader("🔍 Top Possible Diagnoses")

            cols        = st.columns(len(top_matches))
            card_accent = ["#0ea5e9", "#8b5cf6", "#14b8a6"]

            for i, disease in enumerate(top_matches):
                with cols[i]:
                    score    = disease['Match_Score']
                    severity = disease.get("Severity", 0)
                    accent   = card_accent[i % len(card_accent)]

                    st.markdown(f"""
<div style="height:3px;background:linear-gradient(90deg,{accent},transparent);
    border-radius:99px;margin-bottom:16px;margin-top:-4px;"></div>
<div style="display:flex;align-items:baseline;gap:6px;margin-bottom:2px;">
  <span style="font-family:'Sora',sans-serif;font-size:2rem;font-weight:800;
      line-height:1;color:{accent};text-shadow:0 0 20px {accent}55;">#{i+1}</span>
  <span style="font-size:0.68rem;color:#475569;font-weight:500;font-family:'Inter',sans-serif;letter-spacing:0.04em;">rank</span>
</div>
<div style="font-family:'Sora',sans-serif;font-size:1rem;font-weight:700;
    color:#f1f5f9;text-transform:capitalize;letter-spacing:-0.01em;margin-bottom:14px;line-height:1.3;">
  {disease['Disease']}
</div>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
  <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;
      text-transform:uppercase;color:#475569;font-family:'Inter',sans-serif;">Confidence</span>
  <span style="font-size:0.82rem;font-weight:700;color:{accent};font-family:'Sora',sans-serif;">{int(score * 100)}%</span>
</div>
""", unsafe_allow_html=True)

                    st.progress(score)

                    if severity < 30:
                        chip_bg, chip_color, chip_dot, chip_label = "rgba(52,211,153,0.12)", "#6ee7b7", "#34d399", "Low Severity"
                    elif severity < 60:
                        chip_bg, chip_color, chip_dot, chip_label = "rgba(251,191,36,0.12)", "#fde68a", "#fbbf24", "Moderate Severity"
                    else:
                        chip_bg, chip_color, chip_dot, chip_label = "rgba(248,113,113,0.12)", "#fca5a5", "#f87171", "High Severity"

                    st.markdown(f"""
<div style="margin:12px 0 16px;">
  <span style="display:inline-flex;align-items:center;gap:6px;padding:5px 13px;border-radius:99px;
      font-size:0.7rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;
      font-family:'Inter',sans-serif;background:{chip_bg};color:{chip_color};border:1px solid {chip_dot}44;">
    <span style="width:6px;height:6px;border-radius:50%;background:{chip_dot};
        box-shadow:0 0 6px {chip_dot};display:inline-block;"></span>
    {chip_label}
  </span>
</div>
""", unsafe_allow_html=True)

                    st.markdown("---")

                    desc  = safe_display(disease.get('Description'))        or "Not available"
                    syms  = safe_display(disease.get('Symptoms'))           or "Not available"
                    exam  = safe_display(disease.get('Physical_Exam'))      or "Not available"
                    path  = safe_display(disease.get('Pathognomonic_Sign')) or "Not available"
                    treat = disease.get("Treatment", "Not available")
                    precs = disease.get('Precautions', [])

                    prec_html = "".join([
                        f'<div style="display:flex;gap:8px;align-items:flex-start;padding:3px 0;">'
                        f'<div style="width:4px;height:4px;background:#38bdf8;border-radius:50%;'
                        f'margin-top:7px;flex-shrink:0;"></div>'
                        f'<span style="font-size:0.85rem;color:#94a3b8;font-family:\'Inter\',sans-serif;line-height:1.5;">{p}</span></div>'
                        for p in precs
                    ]) if precs else '<div style="font-size:0.85rem;color:#94a3b8;">Not available</div>'

                    exp_id = f"exp_{i}"
                    st.markdown(f"""
<style>
  #{exp_id}-chk {{ display: none; }}
  #{exp_id}-chk:checked + label {{ color: #7dd3fc !important; border-color: rgba(56,189,248,0.2) !important; background: rgba(56,189,248,0.05) !important; border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important; }}
  #{exp_id}-chk:checked + label .exp-arrow {{ transform: rotate(90deg); color: #7dd3fc !important; }}
  #{exp_id}-chk:checked ~ .{exp_id}-body {{ display: block !important; }}
</style>
<input type="checkbox" id="{exp_id}-chk" class="exp-chk">
<label for="{exp_id}-chk" class="exp-label">
  📋 Clinical Details
  <span class="exp-arrow">›</span>
</label>
<div class="{exp_id}-body exp-body">
  {dblock("🧾 Description", desc)}
  {dblock("🤒 Symptoms", syms)}
  {dblock("🩺 Physical Exam", exam)}
  {dblock("🔬 Pathognomonic Sign", path)}
  <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
      color:#475569;margin-bottom:6px;font-family:'Inter',sans-serif;">💊 Precautions</div>
  {prec_html}
  {dblock("💊 Medicine & Dose", treat)}
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-top:0.5rem;">
  <div style="width:3px;height:18px;background:linear-gradient(180deg,#a78bfa,#38bdf8);border-radius:99px;"></div>
  <span style="font-family:'Inter',sans-serif;font-size:0.62rem;font-weight:700;
      letter-spacing:0.14em;text-transform:uppercase;color:#64748b;">AI Reasoning</span>
</div>
""", unsafe_allow_html=True)
        st.subheader("🧠 AI Clinical Reasoning")
        st.success(f"Primary Diagnosis: {result['diagnosis']}")
        st.progress(min(confidence, 1.0))
        st.caption(f"Confidence Score: {int(confidence * 100)}%")
        st.markdown("### 📋 Clinical Summary")
        st.info(result['clinical_summary'])


# ══════════════════════════════════════════════════════
#  DISCLAIMER
# ══════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="display:flex;align-items:flex-start;gap:12px;padding:14px 20px;margin-top:6px;
    background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.12);
    border-radius:12px;backdrop-filter:blur(8px);">
  <span style="font-size:16px;flex-shrink:0;margin-top:1px;">⚠️</span>
  <span style="font-family:'Inter',sans-serif;font-size:0.76rem;color:#57534e;font-weight:500;line-height:1.6;">
    <strong style="color:#78716c;">Clinical Decision Support Only.</strong>
    This system is not a substitute for professional medical judgment.
    Always verify AI-generated suggestions with appropriate clinical expertise
    and patient-specific context before making treatment decisions.
  </span>
</div>
""", unsafe_allow_html=True)
