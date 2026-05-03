import streamlit as st
import requests
import random
import time
import os

FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")

def send_otp_fast2sms(phone: str, otp: str) -> bool:
    """Send OTP via Fast2SMS using the correct OTP route."""
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    # GET method with query params — this is what Fast2SMS OTP route requires
    params = {
        "authorization": FAST2SMS_API_KEY,
        "variables_values": otp,   # just the OTP number
        "route": "otp",            # Fast2SMS sends: "Your OTP: 123456"
        "numbers": phone,
    }
    headers = {
        "cache-control": "no-cache"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        return data.get("return", False)
    except Exception as e:
        st.error(f"SMS error: {e}")
        return False


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def init_auth_state():
    defaults = {
        "auth_verified": False,
        "auth_phone": "",
        "auth_otp": "",
        "auth_otp_sent": False,
        "auth_otp_time": 0,
        "auth_attempts": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def otp_login_page():
    """Render the OTP login gate. Returns True if user is verified."""
    init_auth_state()

    if st.session_state["auth_verified"]:
        return True

    # ── Page styling ──────────────────────────────────────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body { margin: 0; padding: 0; }

.stApp {
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
    background:
        radial-gradient(ellipse 120% 80% at 0% 0%,   #0f3460 0%, transparent 55%),
        radial-gradient(ellipse 100% 70% at 100% 10%, #1a1a4e 0%, transparent 50%),
        radial-gradient(ellipse 80%  60% at 30% 80%,  #0d2137 0%, transparent 55%),
        linear-gradient(160deg, #071929 0%, #0a1628 40%, #0c1f3a 70%, #071525 100%) !important;
    color: #e2e8f0 !important;
}

.auth-card {
    max-width: 440px;
    margin: 6vh auto 0;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(56,189,248,0.18);
    border-radius: 24px;
    padding: 44px 40px 40px;
    backdrop-filter: blur(20px) saturate(160%);
    box-shadow: 0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07);
}

.auth-logo {
    font-family: 'Sora', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #bae6fd 50%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 6px;
}

.auth-sub {
    text-align: center;
    font-size: 0.82rem;
    color: #475569;
    margin-bottom: 32px;
    font-weight: 500;
    line-height: 1.5;
}

.auth-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 8px;
    font-family: 'Inter', sans-serif;
}

.auth-disclaimer {
    margin-top: 28px;
    padding: 12px 16px;
    background: rgba(245,158,11,0.06);
    border: 1px solid rgba(245,158,11,0.12);
    border-radius: 10px;
    font-size: 0.72rem;
    color: #78716c;
    line-height: 1.6;
    text-align: center;
}

.stTextInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
    transition: all 0.2s !important;
}
.stTextInput input:focus {
    border-color: rgba(56,189,248,0.5) !important;
    background: rgba(56,189,248,0.04) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.1) !important;
}
.stTextInput label {
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
}

.stButton > button {
    width: 100% !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: 10px !important;
    padding: 13px 22px !important;
    border: none !important;
    background: linear-gradient(135deg, #0284c7 0%, #7c3aed 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 20px rgba(2,132,199,0.4) !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(2,132,199,0.55) !important;
}

[data-testid="stSuccess"] {
    background: rgba(16,185,129,0.08) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-left: 3px solid #10b981 !important;
    border-radius: 10px !important;
}
[data-testid="stError"] {
    background: rgba(239,68,68,0.08) !important;
    border: 1px solid rgba(239,68,68,0.2) !important;
    border-left: 3px solid #ef4444 !important;
    border-radius: 10px !important;
}
[data-testid="stInfo"] {
    background: rgba(14,165,233,0.08) !important;
    border: 1px solid rgba(14,165,233,0.2) !important;
    border-left: 3px solid #0ea5e9 !important;
    border-radius: 10px !important;
}

/* hide streamlit chrome on login page */
header[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 2rem 1rem !important; }
</style>
""", unsafe_allow_html=True)

    # ── Auth card ─────────────────────────────────────────────────────────────
    st.markdown("""
<div class="auth-card">
  <div class="auth-logo">🩺 EXiCare AI</div>
  <div class="auth-sub">Clinical Decision Support System<br>
    <span style="color:#334155;">Verify your phone number to continue</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # centre-column layout
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # ── STEP 1: Enter phone ───────────────────────────────────────────────
        if not st.session_state["auth_otp_sent"]:
            phone = st.text_input(
                "Mobile Number",
                placeholder="Enter 10-digit Indian mobile number",
                max_chars=10,
            )

            if st.button("📲 Send OTP"):
                if not FAST2SMS_API_KEY:
                    st.error("❌ FAST2SMS_API_KEY not configured. Add it to Streamlit secrets.")
                elif len(phone) != 10 or not phone.isdigit():
                    st.error("❌ Please enter a valid 10-digit mobile number.")
                else:
                    otp = generate_otp()
                    with st.spinner("Sending OTP..."):
                        success = send_otp_fast2sms(phone, otp)

                    if success:
                        st.session_state["auth_phone"]    = phone
                        st.session_state["auth_otp"]      = otp
                        st.session_state["auth_otp_sent"] = True
                        st.session_state["auth_otp_time"] = time.time()
                        st.session_state["auth_attempts"] = 0
                        st.success(f"✅ OTP sent to +91-XXXXXX{phone[-4:]}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to send OTP. Check your Fast2SMS API key & balance.")

        # ── STEP 2: Verify OTP ────────────────────────────────────────────────
        else:
            elapsed = time.time() - st.session_state["auth_otp_time"]
            remaining = max(0, int(300 - elapsed))   # 5-min window

            st.info(f"📱 OTP sent to +91-XXXXXX{st.session_state['auth_phone'][-4:]}  —  expires in {remaining//60}m {remaining%60}s")

            otp_input = st.text_input(
                "Enter OTP",
                placeholder="6-digit OTP",
                max_chars=6,
                type="password",
            )

            if st.button("✅ Verify & Enter"):
                if remaining == 0:
                    st.error("⏰ OTP expired. Please request a new one.")
                    st.session_state["auth_otp_sent"] = False
                    st.rerun()
                elif st.session_state["auth_attempts"] >= 5:
                    st.error("🔒 Too many attempts. Please request a new OTP.")
                    st.session_state["auth_otp_sent"] = False
                    st.rerun()
                elif otp_input == st.session_state["auth_otp"]:
                    st.session_state["auth_verified"] = True
                    st.session_state["auth_otp"]      = ""   # clear OTP from state
                    st.success("🎉 Verified! Loading EXiCare AI...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state["auth_attempts"] += 1
                    left = 5 - st.session_state["auth_attempts"]
                    st.error(f"❌ Wrong OTP. {left} attempt(s) remaining.")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Resend OTP"):
                st.session_state["auth_otp_sent"] = False
                st.rerun()

        st.markdown("""
<div class="auth-disclaimer">
  ⚠️ For clinical decision support only.<br>
  Not a substitute for professional medical judgment.
</div>
""", unsafe_allow_html=True)

    return False