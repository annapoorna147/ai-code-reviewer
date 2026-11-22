# AI Code Reviewer

An AI-powered Python code review platform built with FastAPI, Streamlit, and Google Gemini.

## Features

### Code Review
- Static Python code analysis using AST.
- Detection of potentially unsafe code such as eval() and exec().
- AI-powered code review using Gemini.
- Static-analysis fallback when AI is unavailable.
- Code quality score out of 100.
- Severity breakdown: Critical, High, Medium, Low.
- Detailed findings with line numbers and suggestions.
- Downloadable JSON review reports.

### Advanced Code Quality Analytics
- Cyclomatic complexity calculation.
- Function-level complexity analysis.
- Maintainability Index estimation.
- Duplicate code block detection.
- Technical debt estimation based on finding severity.
- Lines-of-code measurement.
- Syntax-error-aware metrics reporting.

Note: Maintainability Index and technical debt are approximate estimates, not guarantees of actual maintenance effort.

### Security Vulnerability Analysis
- Potential SQL injection detection.
- Unsafe pickle deserialization detection.
- Unsafe YAML loading detection.
- Subprocess command execution with shell=True detection.
- Weak MD5 and SHA1 hash detection.
- Insecure random number generation detection.
- Separate security score out of 100.
- Security findings with severity, affected line numbers, explanations, and suggested fixes.

Note: Security analysis uses heuristic static analysis and may produce false positives or miss vulnerabilities. It is not a substitute for a professional security audit.

### Advanced AI Code Intelligence
- Context-aware AI explanations for detected code issues.
- Root-cause analysis explaining why an issue occurs.
- Potential impact descriptions highlighting practical consequences.
- AI confidence levels: Low, Medium, and High.
- Actionable recommendations for improving code.
- Backward-compatible handling of findings without advanced intelligence fields.

Note: AI-generated explanations and confidence levels are estimates. Review findings before making code changes.

### Intelligent Finding Prioritization
- Individual priority scores from 0 to 100.
- Severity-based priority ranking: Critical, High, Medium, Low.
- Confidence-based score adjustments.
- Automatic sorting from highest to lowest priority.
- Priority score visualization in the Streamlit frontend.
- Priority scores preserved in saved review records.
- Separate priority, quality, and security scoring systems.

Priority scoring:
- Critical: 100 base points.
- High: 80 base points.
- Medium: 60 base points.
- Low: 40 base points.
- High confidence: no adjustment.
- Medium or unspecified confidence: -10 points.
- Low confidence: -20 points.

Final scores are bounded between 0 and 100. Priority scores are heuristic guidance, not a substitute for engineering judgment.

### Review Intelligence and Recommendations
- Overall code health assessment.
- Identification of the three highest-priority risks.
- Actionable improvement recommendations.
- Automatically generated fixing order based on finding priority.
- Duplicate recommendation removal.
- Review summaries available through the API and Streamlit dashboard.
- Graceful summary generation when Gemini AI is unavailable.
- Review summaries preserved in saved review history.

Note: Review summaries are generated from detected findings and heuristic scores. They are decision-support guidance, not a substitute for manual code review.

### User Management and Security
- User registration and login.
- Secure password hashing using Argon2.
- JWT-based authentication.
- Protected API endpoints.
- User-specific review history.
- Personal analytics dashboard.

### Project Management
- Create, view, edit, and delete projects.
- User-specific project ownership.
- Associate code reviews with projects.
- Retrieve project-specific review history.
- Filter review history by project.

### Dashboard
- Interactive Streamlit interface.
- Advanced code quality metrics.
- Review history and analytics.
- Downloadable JSON reports.

## Technology Stack

- Python 3.13
- FastAPI
- Streamlit
- Google Gemini API
- Pydantic
- Python AST
- SQLite
- JWT / PyJWT
- Argon2 password hashing
- Requests
- Pytest
- Uvicorn

## Installation

    git clone https://github.com/annapoorna147/ai-code-reviewer.git
    cd ai-code-reviewer
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Environment Configuration

Create a `.env` file in the project root:

    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=your_supported_gemini_model
    JWT_SECRET_KEY=your_secure_random_secret

Generate a secure JWT secret using:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Never upload your `.env` file, API keys, JWT secrets, or passwords to GitHub.

## Run Backend

    uvicorn app.main:app --reload

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## Run Frontend

Open another Terminal window:

    cd ~/ai-code-reviewer
    source .venv/bin/activate
    streamlit run frontend.py

Frontend: http://localhost:8501

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Application home |
| GET | /health | Health check |
| POST | /auth/register | Register a new account |
| POST | /auth/login | Authenticate and receive a JWT |
| POST | /review | Review Python code |
| GET | /history | Retrieve personal review history |
| GET | /history/{review_id} | Retrieve a saved review |
| GET | /analytics | Retrieve personal review analytics |
| GET | /projects | List personal projects |
| POST | /projects | Create a project |
| GET | /projects/{project_id} | Retrieve project details |
| PUT | /projects/{project_id} | Update a project |
| DELETE | /projects/{project_id} | Delete a project |
| GET | /projects/{project_id}/history | Retrieve project-linked reviews |

Protected endpoints require a valid JWT bearer token in the Authorization header.

## Authentication

- Users can create accounts with a username, email, and password.
- Passwords are securely hashed using Argon2.
- Successful login returns a JWT access token.
- Access tokens expire after 30 minutes.
- Review, history, analytics, and project management endpoints require authentication.
- Users can access only their own authenticated review records.

## Quality Scoring

| Severity | Deduction |
|---|---:|
| Critical | 25 |
| High | 15 |
| Medium | 8 |
| Low | 3 |

Starting score: 100. Minimum score: 0.

## Advanced Code Quality Metrics

The advanced metrics engine provides:

| Metric | Description |
|---|---|
| Lines of Code | Number of non-empty source lines |
| Cyclomatic Complexity | Decision-path complexity |
| Function Complexity | Complexity calculated for individual functions |
| Maintainability Index | Approximate maintainability score from 0 to 100 |
| Duplicate Code Detection | Repeated normalized source-code blocks |
| Technical Debt | Estimated remediation time based on finding severity |

Advanced metrics are included in the `/review` API response and displayed in the Streamlit review dashboard.

## Review History and Database

Review results and user accounts are stored locally in SQLite databases under `data/`.

The database and required tables are initialized automatically when the backend starts.

The dashboard displays account-specific reviews, allows users to select previous reviews, and shows submitted code and findings.

The `data/` directory is excluded from Git.

## Analytics Dashboard

The personal analytics dashboard displays:

- Total reviews completed.
- Average code quality score.
- Total issues detected.
- Issue distribution by severity.

Analytics are calculated using the authenticated user's review records.

## Project Management

Users can create and manage their own projects through the dashboard and API.

Features:
- Create projects with a name and description.
- View a list of personal projects.
- Retrieve individual project details.
- Edit project information.
- Delete projects.
- Enforce project ownership.
- Associate reviews with projects.
- Retrieve project-specific review history.

Project data is stored in SQLite with creation and update timestamps.

## Database Structure

The application uses SQLite tables for:

- `users`: account information and password hashes.
- `reviews`: submitted code and review results.
- `projects`: user-owned project information.

## Run Tests

    python -m pytest -q --ignore=ai-code-reviewer

The nested `ai-code-reviewer/` directory is excluded because it contains duplicate test module names.

## Development Progress

- Day 1: FastAPI foundation and automated tests.
- Day 2: Static code analyzer and review API.
- Day 3: Gemini AI integration and fallback handling.
- Day 4: Quality scoring and structured review reports.
- Day 5: Streamlit frontend and downloadable JSON reports.
- Day 6: SQLite review history, saved review details, and history dashboard.
- Day 7: User authentication, JWT security, password hashing, protected APIs, and personal analytics.
- Day 8: Project management, project CRUD APIs, user-specific project ownership, and dashboard integration.
- Day 9: Project-linked code reviews and project-specific review history.
- Day 10: Advanced code quality analytics, cyclomatic complexity, maintainability index, duplicate code detection, technical debt estimation, and dashboard integration.
- Day 11: Security vulnerability detection, separate security scoring, security analysis dashboard, and automated security tests.

## Author

Annapoorna S U

GitHub: https://github.com/annapoorna147

Repository: https://github.com/annapoorna147/ai-code-reviewer
