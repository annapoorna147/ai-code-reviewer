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

if "proposed_fix" not in st.session_state:
    st.session_state.proposed_fix = None


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


def submit_review(code, project_id=None):
    try:
        payload = {"code": code, "language": "python"}

        if project_id is not None:
            payload["project_id"] = project_id

        response = requests.post(
            f"{API_URL}/review",
            json=payload,
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



def submit_fix(code, finding):
    try:
        payload = {
            "code": code,
            "title": finding["title"],
            "explanation": finding["explanation"],
            "suggestion": finding["suggestion"],
        }

        response = requests.post(
            f"{API_URL}/fix",
            json=payload,
            headers=auth_headers(),
            timeout=90,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 401:
            return None, "Your session may have expired. Please log in again."
        try:
            message = error.response.json().get("detail", "Fix generation failed.")
        except (ValueError, AttributeError):
            message = "Fix generation failed."
        return None, str(message)

    except requests.Timeout:
        return None, "Fix generation timed out. Please try again."

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


def fetch_project_history(project_id):
    try:
        response = requests.get(
            f"{API_URL}/projects/{project_id}/history",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("reviews", []), None

    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 401:
            return [], "Your session may have expired. Please log in again."
        return [], "Could not retrieve project review history."

    except requests.RequestException:
        return [], "Could not retrieve project review history. Check the backend."


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


def fetch_projects():
    try:
        response = requests.get(
            f"{API_URL}/projects/",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException:
        return [], "Could not retrieve your projects."


def create_project(name, description):
    try:
        response = requests.post(
            f"{API_URL}/projects/",
            json={"name": name, "description": description},
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException:
        return None, "Could not create the project."


def update_project(project_id, name, description):
    try:
        response = requests.put(
            f"{API_URL}/projects/{project_id}",
            json={"name": name, "description": description},
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException:
        return None, "Could not update the project."


def delete_project(project_id):
    try:
        response = requests.delete(
            f"{API_URL}/projects/{project_id}",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return True, None
    except requests.RequestException:
        return False, "Could not delete the project."


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


def apply_proposed_fix():
    proposed = st.session_state.get("proposed_fix")

    if proposed:
        st.session_state.original_code_before_fix = proposed["original_code"]
        st.session_state.code_editor = proposed["fixed_code"]
        st.session_state.proposed_fix = None
        st.session_state.review_result = None


def discard_proposed_fix():
    st.session_state.proposed_fix = None


# ---------------- CODE REVIEW WORKSPACE ----------------

st.subheader("Code Analysis Workspace")
st.write("Paste your Python source code below to begin.")

review_projects, review_projects_error = fetch_projects()

if review_projects_error:
    st.warning("Could not load projects. This review will be saved without a project.")

selected_project = st.selectbox(
    "Associate this review with a project",
    options=[None, *review_projects],
    format_func=lambda project: (
        "No project" if project is None else project["name"]
    ),
    key="review_project_selector",
)

default_code = """def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


values = [10, 20, 30, 40]
result = calculate_average(values)
print(result)
"""

if "code_editor" not in st.session_state:
    st.session_state.code_editor = default_code

code = st.text_area(
    "Python source code",
    height=320,
    placeholder="Paste your Python code here...",
    help="Maximum accepted code length: 50,000 characters.",
    key="code_editor",
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
            result, error = submit_review(
                code,
                selected_project["id"] if selected_project else None,
            )

        if error:
            st.error(error)
        else:
            st.session_state.reviewed_code = code
            st.session_state.proposed_fix = None
            st.session_state.review_result = result


# ---------------- REVIEW RESULTS ----------------

result = st.session_state.review_result

if result:
    st.divider()
    st.subheader("Review Dashboard")

    score = result["quality_score"]
    security_score = result.get("security_score", 100)
    issues = result["total_issues"]
    summary = result["severity_summary"]

    score_col, security_col, issues_col, status_col = st.columns(4)

    score_col.metric("Code Quality Score", f"{score}/100")
    security_col.metric("Security Score", f"{security_score}/100")
    issues_col.metric("Total Issues", issues)
    status_col.metric(
        "Review Status",
        result["status"].replace("_", " ").title(),
    )

    st.progress(score / 100)

    st.caption(
        "AI service: " + result["ai_status"].replace("_", " ").title()
    )

    # ---------------- ADVANCED CODE METRICS ----------------

    metrics = result.get("code_metrics")

    if metrics:
        st.divider()
        st.subheader("Advanced Code Quality Metrics")

        if metrics["analysis_status"] == "success":
            complexity = metrics["total_complexity"]
            maintainability = metrics["maintainability_index"]
            debt = metrics["technical_debt"]

            metric_cols = st.columns(4)

            metric_cols[0].metric(
                "Lines of Code",
                metrics["lines_of_code"],
            )
            metric_cols[1].metric(
                "Cyclomatic Complexity",
                complexity,
            )
            metric_cols[2].metric(
                "Maintainability Index",
                f'{maintainability}/100',
            )
            metric_cols[3].metric(
                "Estimated Technical Debt",
                f'{debt["estimated_hours"]} hrs',
            )

            st.caption(
                "Technical debt is a heuristic estimate based on finding severity."
            )

            function_metrics = metrics["function_complexities"]

            if function_metrics:
                st.markdown("**Function Complexity**")
                st.dataframe(
                    function_metrics,
                    use_container_width=True,
                    hide_index=True,
                )

            duplicate_blocks = metrics["duplicate_blocks"]

            st.markdown("**Duplicate Code Detection**")

            if duplicate_blocks:
                for index, block in enumerate(duplicate_blocks, start=1):
                    with st.expander(
                        f'Duplicate Block {index} — '
                        f'{block["lines"]} lines, '
                        f'{block["occurrences"]} occurrences'
                    ):
                        st.code("\\n".join(block["code"]), language="python")
            else:
                st.success("No duplicate code blocks detected.")

        else:
            st.warning(
                "Advanced metrics could not be calculated because "
                "the submitted code contains a syntax error."
            )
    else:
        st.info("Advanced metrics are unavailable for this review.")

    if result["ai_status"] == "unavailable":
        st.warning(
            "Gemini AI is currently unavailable. "
            "This report may contain static-analysis findings only."
        )

    # ---------------- SECURITY ANALYSIS ----------------

    st.divider()
    st.subheader("Security Analysis")

    security_titles = {
        "Potential SQL injection",
        "Unsafe pickle deserialization",
        "Potentially unsafe YAML loading",
        "Subprocess shell execution",
        "Weak cryptographic hash",
        "Potentially insecure random generation",
    }

    security_findings = [
        finding
        for finding in result["findings"]
        if finding["title"] in security_titles
    ]

    if not security_findings:
        st.success("No security vulnerabilities detected by the analyzer.")
    else:
        st.warning(
            f"{len(security_findings)} potential security issue(s) detected."
        )

        for index, finding in enumerate(security_findings, start=1):
            severity = finding["severity"].upper()

            with st.expander(
                f'{index}. {finding["title"]} — {severity} '
                f'(Line {finding["line"]})'
            ):
                st.markdown(f"**Severity:** {severity}")
                st.markdown(f'**Affected line:** {finding["line"]}')
                st.write(finding["explanation"])
                st.markdown("**Recommended fix**")
                st.info(finding["suggestion"])

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

                priority_score = finding.get("priority_score")
                if priority_score is not None:
                    st.progress(priority_score / 100)
                    st.caption(f"Priority Score: {priority_score}/100")

                st.markdown(f'**Line:** {finding["line"]}')
                st.write(finding["explanation"])

                if finding.get("root_cause"):
                    st.markdown("**Root cause**")
                    st.write(finding["root_cause"])

                if finding.get("impact"):
                    st.markdown("**Potential impact**")
                    st.warning(finding["impact"])

                if finding.get("confidence"):
                    st.caption(
                        f'AI confidence: {finding["confidence"].title()}'
                    )

                st.markdown("**Suggested improvement**")
                st.info(finding["suggestion"])

    # ---------------- AUTOMATED FIX GENERATOR ----------------

    st.divider()
    st.subheader("🛠️ Automated Fix Generator")
    st.caption(
        "Generate a suggested correction for a detected issue. "
        "Review the proposal before applying it."
    )

    if findings:
        selected_finding_index = st.selectbox(
            "Choose an issue to fix",
            options=range(len(findings)),
            format_func=lambda index: (
                f'{findings[index]["title"]} '
                f'— {findings[index]["severity"].upper()} '
                f'(Line {findings[index]["line"]})'
            ),
            key="fix_finding_selector",
        )

        if st.button(
            "✨ Generate Fix",
            key="generate_fix_button",
            use_container_width=True,
        ):
            reviewed_code = st.session_state.get("reviewed_code", "")

            with st.spinner("Generating a proposed correction..."):
                proposal, fix_error = submit_fix(
                    reviewed_code,
                    findings[selected_finding_index],
                )

            if fix_error:
                st.error(fix_error)
            else:
                st.session_state.proposed_fix = proposal
                st.rerun()

    else:
        st.info("No detected issues are available to fix.")

    proposed = st.session_state.get("proposed_fix")

    if proposed:
        st.markdown("### Before and After")

        original_column, fixed_column = st.columns(2)

        with original_column:
            st.markdown("**Original code**")
            st.code(proposed["original_code"], language="python")

        with fixed_column:
            st.markdown("**Proposed corrected code**")
            st.code(proposed["fixed_code"], language="python")

        st.warning(
            "Review generated code carefully before applying it. "
            "Generated code is syntax-checked but not executed."
        )

        apply_column, discard_column = st.columns(2)

        with apply_column:
            st.button(
                "✅ Apply Fix",
                key="apply_proposed_fix_button",
                type="primary",
                use_container_width=True,
                on_click=apply_proposed_fix,
            )

        with discard_column:
            st.button(
                "Discard Fix",
                key="discard_proposed_fix_button",
                use_container_width=True,
                on_click=discard_proposed_fix,
            )

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

if selected_project:
    st.write(f'Reviews associated with "{selected_project["name"]}".')
    history_items, history_error = fetch_project_history(
        selected_project["id"]
    )
else:
    st.write("All your account's saved reviews are shown here.")
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


# ---------------- PROJECT MANAGEMENT ----------------

st.divider()
st.header("📁 Project Management")
st.write("Organize and manage your code review projects.")

with st.expander("➕ Create a new project", expanded=False):
    with st.form("create_project_form"):
        new_project_name = st.text_input(
            "Project name",
            max_chars=100,
            placeholder="e.g. AI Code Reviewer",
        )
        new_project_description = st.text_area(
            "Project description",
            max_chars=1000,
            placeholder="Describe what this project does...",
        )

        create_clicked = st.form_submit_button(
            "Create Project",
            type="primary",
            use_container_width=True,
        )

    if create_clicked:
        if len(new_project_name.strip()) < 3:
            st.warning("Project name must contain at least 3 characters.")
        else:
            with st.spinner("Creating project..."):
                created, error = create_project(
                    new_project_name.strip(),
                    new_project_description.strip(),
                )

            if error:
                st.error(error)
            else:
                st.success(f'Project "{created["name"]}" created!')
                st.rerun()


projects, projects_error = fetch_projects()

if projects_error:
    st.error(projects_error)

elif not projects:
    st.info("No projects yet. Create your first project above.")

else:
    st.metric("Total Projects", len(projects))

    for project in projects:
        with st.container(border=True):
            st.subheader(project["name"])
            st.write(
                project["description"]
                or "No description provided."
            )
            st.caption(
                f'Created: {project["created_at"][:10]}'
                f' | Last updated: {project["updated_at"][:10]}'
            )

            edit_column, delete_column = st.columns(2)

            with edit_column:
                with st.expander("✏️ Edit project"):
                    with st.form(f'edit_project_{project["id"]}'):
                        edited_name = st.text_input(
                            "Project name",
                            value=project["name"],
                            max_chars=100,
                        )
                        edited_description = st.text_area(
                            "Description",
                            value=project["description"],
                            max_chars=1000,
                        )

                        update_clicked = st.form_submit_button(
                            "Save Changes",
                            use_container_width=True,
                        )

                    if update_clicked:
                        if len(edited_name.strip()) < 3:
                            st.warning(
                                "Project name must contain at least 3 characters."
                            )
                        else:
                            updated, error = update_project(
                                project["id"],
                                edited_name.strip(),
                                edited_description.strip(),
                            )

                            if error:
                                st.error(error)
                            else:
                                st.success("Project updated successfully.")
                                st.rerun()

            with delete_column:
                with st.popover("🗑️ Delete project"):
                    st.warning(
                        "This will permanently delete this project."
                    )

                    if st.button(
                        "Confirm Delete",
                        key=f'delete_project_{project["id"]}',
                        type="primary",
                        use_container_width=True,
                    ):
                        deleted, error = delete_project(project["id"])

                        if error:
                            st.error(error)
                        else:
                            st.success("Project deleted.")
                            st.rerun()
