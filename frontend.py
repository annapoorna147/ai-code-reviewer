import json
import os
from datetime import datetime, timezone

import requests
import streamlit as st


API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero {
        padding: 1.5rem;
        border: 1px solid #30363d;
        border-radius: 14px;
        background: linear-gradient(120deg, #172554, #111827);
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        margin-bottom: 0.3rem;
    }
    .muted {
        color: #9ca3af;
    }
    .finding {
        padding: 1rem;
        border: 1px solid #30363d;
        border-radius: 10px;
        margin-bottom: 0.7rem;
    }
</style>
""", unsafe_allow_html=True)


def check_backend():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def submit_review(code):
    try:
        response = requests.post(
            f"{API_URL}/review",
            json={
                "code": code,
                "language": "python",
            },
            timeout=90,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.Timeout:
        return None, "The review request timed out. Please try again."

    except requests.HTTPError as error:
        return None, f"Backend returned an error: {error.response.status_code}"

    except requests.RequestException:
        return None, "Could not connect to the backend. Check whether FastAPI is running."


def fetch_review_history():
    try:
        response = requests.get(f"{API_URL}/history", timeout=10)
        response.raise_for_status()
        return response.json().get("reviews", []), None
    except requests.RequestException:
        return [], "Could not retrieve review history. Check the backend connection."


def fetch_review_detail(review_id):
    try:
        response = requests.get(
            f"{API_URL}/history/{review_id}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException:
        return None, "Could not retrieve this review."


with st.sidebar:
    st.title("🔍 Code Reviewer")
    st.caption("AI-powered Python code analysis")

    st.divider()

    if check_backend():
        st.success("Backend connected")
    else:
        st.error("Backend offline")

    st.caption(f"API: {API_URL}")

    st.divider()

    st.markdown("### About")
    st.write(
        "Analyze Python code using static analysis "
        "and AI-powered review."
    )

    st.markdown("### Severity levels")
    st.markdown("🔴 Critical")
    st.markdown("🟠 High")
    st.markdown("🟡 Medium")
    st.markdown("🔵 Low")


st.markdown("""
<div class="hero">
    <h1>AI Code Reviewer</h1>
    <p class="muted">
        Write better code. Find hidden bugs. Improve software quality.
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("Code Analysis Workspace")
st.write("Paste your Python source code below to begin.")

default_code = """def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


values = [10, 20, 30, 40]
result = calculate_average(values)
print(result)
"""

code = st.text_area(
    "Python source code",
    value=default_code,
    height=320,
    placeholder="Paste your Python code here...",
    help="Maximum accepted code length: 50,000 characters.",
)

left, right = st.columns([1, 4])

with left:
    review_clicked = st.button(
        "🔍 Review Code",
        type="primary",
        use_container_width=True,
    )

with right:
    st.caption("Supported language: Python")

if review_clicked:
    if not code.strip():
        st.warning("Please enter some Python code first.")

    elif len(code) > 50000:
        st.error("Code exceeds the 50,000-character limit.")

    else:
        with st.spinner("Analyzing your code..."):
            result, error = submit_review(code)

        if error:
            st.error(error)

        else:
            st.session_state["review_result"] = result

result = st.session_state.get("review_result")

if result:
    st.divider()
    st.subheader("Review Dashboard")

    score = result["quality_score"]
    issues = result["total_issues"]
    summary = result["severity_summary"]

    score_col, issues_col, status_col = st.columns(3)

    with score_col:
        st.metric("Code Quality Score", f"{score}/100")

    with issues_col:
        st.metric("Total Issues", issues)

    with status_col:
        st.metric("Review Status", result["status"].replace("_", " ").title())

    st.progress(score / 100)

    st.caption(
        "AI service: " + result["ai_status"].replace("_", " ").title()
    )

    if result["ai_status"] == "unavailable":
        st.warning(
            "Gemini AI is currently unavailable. "
            "This report may contain static-analysis findings only."
        )

    st.subheader("Severity Breakdown")

    severity_columns = st.columns(4)

    severity_data = [
        ("Critical", summary["critical"], "🔴"),
        ("High", summary["high"], "🟠"),
        ("Medium", summary["medium"], "🟡"),
        ("Low", summary["low"], "🔵"),
    ]

    for column, (name, count, emoji) in zip(
        severity_columns, severity_data
    ):
        with column:
            st.metric(f"{emoji} {name}", count)

    st.divider()
    st.subheader("Detailed Findings")

    findings = result["findings"]

    if not findings:
        st.success("No issues detected in this code!")
    else:
        for index, finding in enumerate(findings, start=1):
            severity = finding["severity"].upper()

            with st.expander(
                f'{index}. {finding["title"]} — {severity} '
                f'(Line {finding["line"]})',
                expanded=index == 1,
            ):
                st.markdown(f'**Severity:** {severity}')
                st.markdown(f'**Line:** {finding["line"]}')
                st.write(finding["explanation"])

                st.markdown("**Suggested improvement**")
                st.info(finding["suggestion"])

    st.divider()
    st.subheader("Download Review Report")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "submitted_code": code,
        "review": result,
    }

    report_json = json.dumps(report, indent=4)

    st.download_button(
        label="⬇️ Download JSON Report",
        data=report_json,
        file_name=f"code_review_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.caption("AI Code Reviewer | Built with Python, FastAPI and Streamlit")


# Review History
st.divider()
st.subheader("📚 Review History")
st.write("Revisit your previously analyzed Python code.")

history_items, history_error = fetch_review_history()

if history_error:
    st.warning(history_error)

elif not history_items:
    st.info("No saved reviews yet. Submit your first code review!")

else:
    def history_label(item):
        created = item["created_at"].replace("T", " ")[:19]
        return (
            f'#{item["id"]} | {created} | '
            f'Score: {item["quality_score"]}/100 | '
            f'Issues: {item["total_issues"]}'
        )

    selected_id = st.selectbox(
        "Select a previous review",
        options=[item["id"] for item in history_items],
        format_func=lambda review_id: history_label(
            next(item for item in history_items if item["id"] == review_id)
        ),
    )

    if selected_id is not None:
        detail, detail_error = fetch_review_detail(selected_id)

        if detail_error:
            st.error(detail_error)

        else:
            previous = detail["result"]

            history_score, history_issues, history_status = st.columns(3)

            history_score.metric(
                "Quality Score",
                f'{previous["quality_score"]}/100',
            )
            history_issues.metric(
                "Total Issues",
                previous["total_issues"],
            )
            history_status.metric(
                "Review Status",
                previous["status"].replace("_", " ").title(),
            )

            with st.expander("View submitted code"):
                st.code(detail["code"], language="python")

            with st.expander("View findings"):
                if not previous["findings"]:
                    st.success("No issues detected.")
                else:
                    for index, finding in enumerate(
                        previous["findings"], start=1
                    ):
                        st.markdown(
                            f'**{index}. {finding["title"]}** '
                            f'— {finding["severity"].upper()} '
                            f'(Line {finding["line"]})'
                        )
                        st.write(finding["explanation"])
                        st.info(finding["suggestion"])
