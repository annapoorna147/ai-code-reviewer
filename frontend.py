import json
import os
from datetime import datetime, timezone

import requests
import streamlit as st


API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_TIMEOUT = 30

st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    .hero {
        padding: 1.5rem;
        border: 1px solid #30363d;
        border-radius: 14px;
        background: linear-gradient(120deg, #172554, #111827);
        margin-bottom: 1.5rem;
    }
    .hero h1 { margin-bottom: 0.3rem; }
    .muted { color: #9ca3af; }
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "review_result" not in st.session_state:
    st.session_state.review_result = None


def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state.access_token}"
    }


# ---------------- API FUNCTIONS ----------------

def check_backend():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def authenticate(endpoint, email, password, username=None):
    payload = {
        "email": email,
        "password": password,
    }

    if username is not None:
        payload["username"] = username

    try:
        response = requests.post(
            f"{API_URL}/auth/{endpoint}",
            json=payload,
            timeout=API_TIMEOUT,
        )

        if response.status_code >= 400:
            try:
                message = response.json().get("detail", "Authentication failed.")
            except ValueError:
                message = "Authentication failed."
            return None, str(message)

        return response.json(), None

    except requests.RequestException:
        return None, "Could not connect to the backend."


def submit_review(code):
    try:
        response = requests.post(
            f"{API_URL}/review",
            json={"code": code, "language": "python"},
            headers=auth_headers(),
            timeout=90,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 401:
            return None, "Your session may have expired. Please log in again."
        return None, "The backend could not complete the review."

    except requests.Timeout:
        return None, "The review request timed out. Please try again."

    except requests.RequestException:
        return None, "Could not connect to the backend."


def fetch_review_history():
    try:
        response = requests.get(
            f"{API_URL}/history",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("reviews", []), None

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 401:
            return [], "Your session may have expired. Please log in again."
        return [], "Could not retrieve review history."

    except requests.RequestException:
        return [], "Could not retrieve review history. Check the backend."


def fetch_review_detail(review_id):
    try:
        response = requests.get(
            f"{API_URL}/history/{review_id}",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.RequestException:
        return None, "Could not retrieve this review."


def fetch_analytics():
    try:
        response = requests.get(
            f"{API_URL}/analytics",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 401:
            return None, "Your session may have expired. Please log in again."
        return None, "Could not retrieve analytics."

    except requests.RequestException:
        return None, "Could not connect to the analytics service."


# ---------------- AUTHENTICATION SCREEN ----------------

if not st.session_state.access_token:

    st.markdown("""
    <div class="hero">
        <h1>🔍 AI Code Reviewer</h1>
        <p class="muted">
            Securely analyze code, identify bugs and track software quality.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Welcome")

    if check_backend():
        st.success("Backend connected")
    else:
        st.error("Backend offline. Start the FastAPI server first.")

    login_tab, register_tab = st.tabs(["Login", "Create account"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email address")
            login_password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True,
            )

        if login_clicked:
            if not login_email.strip() or not login_password:
                st.warning("Enter your email and password.")
            else:
                with st.spinner("Signing you in..."):
                    result, error = authenticate(
                        "login",
                        login_email.strip(),
                        login_password,
                    )

                if error:
                    st.error(error)
                else:
                    st.session_state.access_token = result["access_token"]
                    st.session_state.username = login_email.split("@")[0]
                    st.session_state.review_result = None
                    st.rerun()

    with register_tab:
        with st.form("register_form"):
            register_username = st.text_input(
                "Username",
                max_chars=30,
            )
            register_email = st.text_input("Email address")
            register_password = st.text_input(
                "Password",
                type="password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
            )

            register_clicked = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )

        if register_clicked:
            if not all([
                register_username.strip(),
                register_email.strip(),
                register_password,
                confirm_password,
            ]):
                st.warning("Please complete all fields.")

            elif register_password != confirm_password:
                st.error("Passwords do not match.")

            elif len(register_password) < 8:
                st.error("Password must contain at least 8 characters.")

            else:
                with st.spinner("Creating your account..."):
                    result, error = authenticate(
                        "register",
                        register_email.strip(),
                        register_password,
                        register_username.strip(),
                    )

                if error:
                    st.error(error)
                else:
                    st.success(
                        "Account created successfully! "
                        "Please switch to the Login tab."
                    )

    st.stop()


# ---------------- AUTHENTICATED DASHBOARD ----------------

with st.sidebar:
    st.title("🔍 Code Reviewer")
    st.caption("AI-powered Python code analysis")

    st.success(f"Logged in as {st.session_state.username}")

    if st.button("Logout", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.review_result = None
        st.rerun()

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


# ---------------- PERSONAL ANALYTICS ----------------

st.subheader("📊 Your Analytics")

analytics, analytics_error = fetch_analytics()

if analytics_error:
    st.warning(analytics_error)
else:
    metric1, metric2, metric3 = st.columns(3)

    metric1.metric("Total Reviews", analytics["total_reviews"])
    metric2.metric(
        "Average Quality Score",
        f'{analytics["average_quality_score"]}/100',
    )
    metric3.metric("Total Issues Found", analytics["total_issues"])

    severity = analytics["severity_distribution"]

    st.markdown("**Your issue distribution**")
    chart_data = {
        "Severity": ["Critical", "High", "Medium", "Low"],
        "Issues": [
            severity["critical"],
            severity["high"],
            severity["medium"],
            severity["low"],
        ],
    }

    st.bar_chart(
        chart_data,
        x="Severity",
        y="Issues",
        color="#3B82F6",
    )


st.divider()


# ---------------- CODE REVIEW WORKSPACE ----------------

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
            st.session_state.review_result = result


# ---------------- REVIEW RESULTS ----------------

result = st.session_state.review_result

if result:
    st.divider()
    st.subheader("Review Dashboard")

    score = result["quality_score"]
    issues = result["total_issues"]
    summary = result["severity_summary"]

    score_col, issues_col, status_col = st.columns(3)

    score_col.metric("Code Quality Score", f"{score}/100")
    issues_col.metric("Total Issues", issues)
    status_col.metric(
        "Review Status",
        result["status"].replace("_", " ").title(),
    )

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
        column.metric(f"{emoji} {name}", count)

    st.divider()
    st.subheader("Detailed Findings")

    findings = result["findings"]

    if not findings:
        st.success("No issues detected in this code!")
    else:
        for index, finding in enumerate(findings, start=1):
            severity_name = finding["severity"].upper()

            with st.expander(
                f'{index}. {finding["title"]} — {severity_name} '
                f'(Line {finding["line"]})',
                expanded=index == 1,
            ):
                st.markdown(f"**Severity:** {severity_name}")
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

    st.download_button(
        label="⬇️ Download JSON Report",
        data=json.dumps(report, indent=4),
        file_name=(
            "code_review_"
            f'{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.json'
        ),
        mime="application/json",
        use_container_width=True,
    )


# ---------------- REVIEW HISTORY ----------------

st.divider()
st.subheader("📚 Your Review History")
st.write("Only your account's saved reviews are shown here.")

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
            next(
                item for item in history_items
                if item["id"] == review_id
            )
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


st.divider()
st.caption(
    "AI Code Reviewer | Python · FastAPI · Streamlit · SQLite · JWT"
)
