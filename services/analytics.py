import streamlit as st
from supabase import create_client


def get_supabase_client():
    """
    Create and return the Supabase client using Streamlit secrets.
    """

    try:
        supabase_url = st.secrets["SUPABASE_URL"]

        # Support either secret name.
        # SUPABASE_SECRET_KEY is preferred for server-side analytics.
        if "SUPABASE_SECRET_KEY" in st.secrets:
            supabase_key = st.secrets["SUPABASE_SECRET_KEY"]
        elif "SUPABASE_SERVICE_ROLE_KEY" in st.secrets:
            supabase_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        elif "SUPABASE_KEY" in st.secrets:
            supabase_key = st.secrets["SUPABASE_KEY"]
        else:
            raise Exception(
                "No Supabase key found in .streamlit/secrets.toml"
            )

        return create_client(
            supabase_url,
            supabase_key
        )

    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None


def log_analysis_event(
    word_count=0,
    ats_score=None,
    status="success",
    error_message=None
):
    """
    Store anonymous ResumeIQ usage analytics.

    We DO NOT store:
    - Resume PDF
    - Resume text
    - Job description
    - Name
    - Email
    """

    try:
        supabase = get_supabase_client()

        if supabase is None:
            return False

        # Make sure ATS score is a valid integer or None
        if ats_score is not None:
            try:
                ats_score = int(ats_score)
            except (ValueError, TypeError):
                ats_score = None

        data = {
            "word_count": int(word_count or 0),
            "ats_score": ats_score,
            "status": status,
            "error_message": error_message
        }

        response = (
            supabase
            .table("analysis_events")
            .insert(data)
            .execute()
        )

        print("Analytics event saved:", response.data)

        return True

    except Exception as e:
        print(f"Supabase analytics error: {e}")
        return False


def get_analytics_data():
    """
    Get analysis events for internal analytics.
    """

    try:
        supabase = get_supabase_client()

        if supabase is None:
            return []

        response = (
            supabase
            .table("analysis_events")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return response.data or []

    except Exception as e:
        print(f"Analytics retrieval error: {e}")
        return []


def get_analytics_summary():
    """
    Return basic analytics summary.
    """

    data = get_analytics_data()

    if not data:
        return {
            "total_analyses": 0,
            "successful": 0,
            "failed": 0,
            "average_ats_score": 0
        }

    successful = [
        row
        for row in data
        if row.get("status") == "success"
    ]

    failed = [
        row
        for row in data
        if row.get("status") != "success"
    ]

    scores = []

    for row in successful:
        score = row.get("ats_score")

        if score is not None:
            try:
                scores.append(float(score))
            except (ValueError, TypeError):
                pass

    average_score = (
        round(sum(scores) / len(scores), 1)
        if scores
        else 0
    )

    return {
        "total_analyses": len(data),
        "successful": len(successful),
        "failed": len(failed),
        "average_ats_score": average_score
    }


def get_daily_usage():
    """
    Return analysis count grouped by date.
    """

    data = get_analytics_data()

    if not data:
        return []

    daily = {}

    for row in data:

        created_at = row.get("created_at")

        if not created_at:
            continue

        date = str(created_at)[:10]

        if date not in daily:
            daily[date] = 0

        daily[date] += 1

    return [
        {
            "date": date,
            "analyses": count
        }
        for date, count in sorted(daily.items())
    ]