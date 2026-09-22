import os
import streamlit as st
from pypdf import PdfReader
from groq import Groq

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Resume Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED SAAS UI STYLING ---
st.markdown("""
    <style>
    /* Dark Theme Core */
    .stApp {
        background-color: #080c14;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Modern Glassmorphic Header */
    .main-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.9) 50%, rgba(49, 27, 146, 0.9) 100%);
        padding: 2.2rem;
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.8);
    }
    .main-header h1 {
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #94a3b8 !important;
        font-size: 1.05rem;
        margin-top: 0.6rem;
    }

    /* Clean User Metric Cards */
    .user-metric-card {
        background: #0f172a;
        padding: 1.25rem;
        border-radius: 14px;
        border: 1px solid #1e293b;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .user-metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .user-metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 4px;
    }

    /* Primary Action Button */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 0.85rem 1.5rem !important;
        border-radius: 12px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5) !important;
    }

    /* Footer */
    .custom-footer {
        text-align: center;
        padding: 2.5rem 0 1rem 0;
        color: #64748b;
        font-size: 0.85rem;
        border-top: 1px solid #1e293b;
        margin-top: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR & DEV CONSOLE ---
with st.sidebar:
    st.title("⚙️ Engine Hub")
    st.info("💡 Upload your PDF resume and paste the target job description to run an instant ATS analysis.")
    st.markdown("---")
    
    custom_groq_key = st.text_input("Groq API Key (Optional Override)", type="password")
    groq_api_key = custom_groq_key if custom_groq_key else st.secrets.get("GROQ_API_KEY")
    
    st.markdown("### 🛠️ Developer Console")
    st.caption("Internal telemetry for system monitoring.")

if not groq_api_key:
    st.error("🔑 Groq API key missing. Configure GROQ_API_KEY inside .streamlit/secrets.toml")
    st.stop()

client = Groq(api_key=groq_api_key)

# PDF Extraction Function
def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

# Dynamic Fallback Mechanism
def get_working_model():
    preferred = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]
    try:
        available = [m.id for m in client.models.list().data]
        for pref in preferred:
            if pref in available:
                return pref
        valid_models = [m for m in available if "whisper" not in m and "vision" not in m]
        if valid_models:
            return valid_models[0]
    except Exception:
        pass
    return "llama3-8b-8192"

active_model = get_working_model()

# Developer Console telemetry
with st.sidebar:
    st.code(f"Active Model: {active_model}\nEngine Status: Ready", language="text")

# --- 4. HEADER ---
st.markdown("""
    <div class="main-header">
        <h1>⚡ AI Resume Intelligence Platform</h1>
        <p>Real-time ATS Score Diagnostic, Keyword Gap Analysis & Impact Rewrites</p>
    </div>
""", unsafe_allow_html=True)

# --- 5. USER INPUTS ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Upload Candidate Resume")
    uploaded_resume = st.file_uploader("Upload PDF Resume", type=["pdf"])

with col_right:
    st.subheader("2. Target Job Description")
    job_description = st.text_area("Paste Target Job Requirements & Description", height=180, placeholder="Paste the job description here...")

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. EXECUTION ENGINE ---
if st.button("🚀 Run Instant ATS Diagnostic", type="primary"):
    if not uploaded_resume or not job_description.strip():
        st.error("Please upload a PDF resume and enter a target job description.")
    else:
        with st.spinner("Processing document and running ATS evaluation..."):
            try:
                raw_resume_text = extract_pdf_text(uploaded_resume)
                word_count = len(raw_resume_text.split())
                est_read_time = max(1, round(word_count / 200))

                prompt = f"""
                You are an HR ATS Specialist. Analyze this Resume against the Job Description. Be concise.

                JOB DESCRIPTION:
                {job_description[:2000]}

                RESUME:
                {raw_resume_text[:3000]}

                Provide output in exact Markdown structure below:
                ## Overall ATS Match Score: [Insert Score]%

                ### 🌟 Key Candidate Strengths
                - [Strength 1]
                - [Strength 2]

                ### 🚨 Critical Missing Keywords & Skills
                - [Missing Skill/Keyword 1]
                - [Missing Skill/Keyword 2]

                ### ✍️ Impact Bullet Rewrites
                - **Original**: [Original Bullet Point from Resume]
                - **Optimized**: [Action-Oriented ATS Rewritten Bullet]
                """

                completion = client.chat.completions.create(
                    model=active_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )

                if completion and completion.choices:
                    result_text = completion.choices[0].message.content

                    st.success("Diagnostic Analysis Complete!")
                    st.markdown("---")

                    # CLEAN USER-FACING METRICS
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f'<div class="user-metric-card"><div class="user-metric-value">{word_count}</div><div class="user-metric-label">Resume Word Count</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown(f'<div class="user-metric-card"><div class="user-metric-value">~{est_read_time} min</div><div class="user-metric-label">Recruiter Read Time</div></div>', unsafe_allow_html=True)
                    with m3:
                        st.markdown('<div class="user-metric-card"><div class="user-metric-value">PDF Parsed</div><div class="user-metric-label">Document Health</div></div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # OUTPUT TABS
                    t1, t2 = st.tabs(["📊 Diagnostic Report", "💡 Recommended Action Items"])
                    with t1:
                        st.markdown(result_text)
                    with t2:
                        st.info("Incorporate the highlighted missing keywords directly into your work experience bullet points to improve your ATS parsing score.")
                else:
                    st.error("No response received from the engine.")

            except Exception as e:
                st.error(f"Error processing document: {e}")

# --- 7. FOOTER BRANDING ---
st.markdown("""
    <div class="custom-footer">
        Designed & Developed with ❤️ by <b>Inthiyaz</b>
    </div>
""", unsafe_allow_html=True)