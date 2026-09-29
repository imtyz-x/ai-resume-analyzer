import re

import streamlit as st
from pypdf import PdfReader
from groq import Groq
from supabase import create_client


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Resume Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #080c14;
    color: #e2e8f0;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
}

.main-header {
    background: linear-gradient(
        135deg,
        rgba(15, 23, 42, 0.95) 0%,
        rgba(30, 27, 75, 0.95) 50%,
        rgba(49, 27, 146, 0.95) 100%
    );
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

.stButton > button {
    width: 100%;
    background: linear-gradient(
        90deg,
        #2563eb 0%,
        #4f46e5 100%
    ) !important;
    color: white !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    padding: 0.85rem 1.5rem !important;
    border-radius: 12px !important;
    border: none !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5) !important;
}

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


# ============================================================
# 3. SUPABASE ANALYTICS
# ============================================================

def save_analytics(
    word_count=0,
    ats_score=None,
    status="success",
    error_message=None
):
    """
    Save anonymous ResumeIQ analytics.

    We DO NOT store:
    - Resume PDF
    - Resume text
    - Job description
    - Name
    - Email
    """

    try:

        supabase_url = st.secrets.get("SUPABASE_URL")

        supabase_key = (
            st.secrets.get("SUPABASE_SECRET_KEY")
            or st.secrets.get("SUPABASE_KEY")
        )

        if not supabase_url:
            return False, "Missing SUPABASE_URL in Streamlit Secrets."

        if not supabase_key:
            return False, "Missing SUPABASE_SECRET_KEY in Streamlit Secrets."

        supabase = create_client(
            supabase_url,
            supabase_key
        )

        response = (
            supabase
            .table("analysis_events")
            .insert({
                "word_count": int(word_count),
                "ats_score": ats_score,
                "status": status,
                "error_message": error_message
            })
            .select(
                "id, created_at, word_count, ats_score, status"
            )
            .execute()
        )

        return True, response.data

    except Exception as e:

        return False, str(e)


# ============================================================
# 4. GROQ API
# ============================================================

with st.sidebar:

    st.title("⚙️ Engine Hub")

    st.info(
        "💡 Upload your PDF resume and paste the target "
        "job description to run an instant ATS analysis."
    )

    st.markdown("---")

    custom_groq_key = st.text_input(
        "Groq API Key (Optional Override)",
        type="password"
    )

    groq_api_key = (
        custom_groq_key
        if custom_groq_key
        else st.secrets.get("GROQ_API_KEY")
    )

    st.markdown("### 🛠️ Developer Console")

    st.caption(
        "Internal telemetry for system monitoring."
    )


# ============================================================
# 5. CHECK GROQ KEY
# ============================================================

if not groq_api_key:

    st.error(
        "🔑 Groq API key missing. "
        "Add GROQ_API_KEY to Streamlit Secrets."
    )

    st.stop()


client = Groq(
    api_key=groq_api_key
)


# ============================================================
# 6. PDF EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text


# ============================================================
# 7. FIND WORKING GROQ MODEL
# ============================================================

def get_working_model():

    preferred_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]

    try:

        available_models = [
            model.id
            for model in client.models.list().data
        ]

        for preferred in preferred_models:

            if preferred in available_models:
                return preferred

        valid_models = [
            model
            for model in available_models
            if "whisper" not in model.lower()
            and "vision" not in model.lower()
        ]

        if valid_models:
            return valid_models[0]

    except Exception as e:

        print(
            f"Model detection error: {e}"
        )

    return "llama-3.3-70b-versatile"


active_model = get_working_model()


# ============================================================
# 8. SIDEBAR MODEL STATUS
# ============================================================

with st.sidebar:

    st.code(
        f"Active Model: {active_model}\n"
        f"Engine Status: Ready",
        language="text"
    )


# ============================================================
# 9. HEADER
# ============================================================

st.markdown(
    '<div class="main-header"><h1>⚡ AI Resume Intelligence Platform</h1><p>Real-time ATS Score Diagnostic, Keyword Gap Analysis & Impact Rewrites</p></div>',
    unsafe_allow_html=True
)


# ============================================================
# 10. INPUT AREA
# ============================================================

col_left, col_right = st.columns(
    [1, 1],
    gap="large"
)


with col_left:

    st.subheader(
        "1. Upload Candidate Resume"
    )

    uploaded_resume = st.file_uploader(
        "Upload PDF Resume",
        type=["pdf"]
    )


with col_right:

    st.subheader(
        "2. Target Job Description"
    )

    job_description = st.text_area(
        "Paste Target Job Requirements & Description",
        height=180,
        placeholder="Paste the job description here..."
    )


st.markdown(
    "<br>",
    unsafe_allow_html=True
)


# ============================================================
# 11. RUN ANALYSIS
# ============================================================

if st.button(
    "🚀 Run Instant ATS Diagnostic",
    type="primary"
):

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    if not uploaded_resume:

        st.error(
            "Please upload a PDF resume."
        )

        st.stop()


    if not job_description.strip():

        st.error(
            "Please enter a target job description."
        )

        st.stop()


    word_count = 0


    try:

        # ====================================================
        # PROCESSING
        # ====================================================

        with st.spinner(
            "Processing document and running ATS evaluation..."
        ):

            # ------------------------------------------------
            # Extract resume text
            # ------------------------------------------------

            raw_resume_text = extract_pdf_text(
                uploaded_resume
            )


            if not raw_resume_text.strip():

                raise ValueError(
                    "Could not extract readable text from the PDF."
                )


            word_count = len(
                raw_resume_text.split()
            )


            est_read_time = max(
                1,
                round(word_count / 200)
            )


            # ------------------------------------------------
            # AI PROMPT
            # ------------------------------------------------

            prompt = f"""
You are an HR ATS Specialist.

Analyze the candidate's resume against the target job description.

Be accurate, concise and practical.

JOB DESCRIPTION:
{job_description[:4000]}

RESUME:
{raw_resume_text[:6000]}

Return the result using EXACTLY this Markdown structure:

## Overall ATS Match Score: [number]%

### 🌟 Key Candidate Strengths
- [Strength 1]
- [Strength 2]
- [Strength 3]

### 🚨 Critical Missing Keywords & Skills
- [Missing Skill/Keyword 1]
- [Missing Skill/Keyword 2]
- [Missing Skill/Keyword 3]

### ✍️ Impact Bullet Rewrites

- **Original**: [Original resume bullet]
- **Optimized**: [ATS-friendly rewritten bullet]

- **Original**: [Original resume bullet]
- **Optimized**: [ATS-friendly rewritten bullet]

Give a realistic ATS match score based on the actual overlap between the resume and job description.
"""


            # ------------------------------------------------
            # GROQ REQUEST
            # ------------------------------------------------

            completion = client.chat.completions.create(

                model=active_model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2,

                max_tokens=1000
            )


            # ------------------------------------------------
            # VERIFY RESPONSE
            # ------------------------------------------------

            if not completion:

                raise ValueError(
                    "No response received from the AI engine."
                )


            if not completion.choices:

                raise ValueError(
                    "AI engine returned no choices."
                )


            result_text = (
                completion
                .choices[0]
                .message
                .content
            )


            if not result_text:

                raise ValueError(
                    "AI returned an empty result."
                )


           # =================================================
# EXTRACT ATS SCORE
# =================================================

score_patterns = [
    r"Overall ATS Match Score\s*:\s*\**\s*(\d{1,3})\s*%",
    r"ATS Match Score\s*:\s*\**\s*(\d{1,3})\s*%",
    r"ATS Score\s*:\s*\**\s*(\d{1,3})\s*%",
]

ats_score = None

for pattern in score_patterns:

    score_match = re.search(
        pattern,
        result_text,
        re.IGNORECASE
    )

    if score_match:
        ats_score = int(score_match.group(1))
        break


            # =================================================
            # SAVE TO SUPABASE
            # =================================================

            analytics_saved, analytics_result = save_analytics(
                word_count=word_count,
                ats_score=ats_score,
                status="success"
            )


            # =================================================
            # SUCCESS MESSAGE
            # =================================================

            st.success(
                "Diagnostic Analysis Complete!"
            )


            # ------------------------------------------------
            # Analytics connection status
            # ------------------------------------------------

            if analytics_saved:

                st.success(
                    "✓ Analytics saved successfully."
                )

            else:

                st.error(
                    f"Supabase analytics error: {analytics_result}"
                )


            st.markdown("---")


            # =================================================
            # METRICS
            # =================================================

            m1, m2, m3 = st.columns(3)


            with m1:

                st.markdown(
                    f'<div class="user-metric-card"><div class="user-metric-value">{word_count}</div><div class="user-metric-label">Resume Word Count</div></div>',
                    unsafe_allow_html=True
                )


            with m2:

                st.markdown(
                    f'<div class="user-metric-card"><div class="user-metric-value">~{est_read_time} min</div><div class="user-metric-label">Recruiter Read Time</div></div>',
                    unsafe_allow_html=True
                )


            with m3:

                score_display = (
                    f"{ats_score}%"
                    if ats_score is not None
                    else "Analyzed"
                )

                st.markdown(
                    f'<div class="user-metric-card"><div class="user-metric-value">{score_display}</div><div class="user-metric-label">ATS Match Score</div></div>',
                    unsafe_allow_html=True
                )


            st.markdown(
                "<br>",
                unsafe_allow_html=True
            )


            # =================================================
            # RESULTS
            # =================================================

            tab_report, tab_actions = st.tabs(
                [
                    "📊 Diagnostic Report",
                    "💡 Recommended Action Items"
                ]
            )


            with tab_report:

                st.markdown(
                    result_text
                )


            with tab_actions:

                st.info(
                    """
**Recommended next steps**

1. Add relevant missing keywords naturally.
2. Strengthen weak experience bullet points.
3. Use measurable achievements where available.
4. Keep formatting simple and ATS-friendly.
5. Re-run the analysis after improving the resume.
"""
                )


    except Exception as e:

        # ====================================================
        # SAVE FAILURE TO SUPABASE
        # ====================================================

        analytics_saved, analytics_result = save_analytics(
            word_count=word_count,
            ats_score=None,
            status="failed",
            error_message=str(e)[:500]
        )


        # ====================================================
        # SHOW ERROR
        # ====================================================

        st.error(
            f"Error processing document: {e}"
        )

        if not analytics_saved:

            st.error(
                f"Supabase analytics error: {analytics_result}"
            )


# ============================================================
# 12. FOOTER
# ============================================================

st.markdown(
    '<div class="custom-footer">Designed & Developed by <b>Inthiyaz</b></div>',
    unsafe_allow_html=True
)