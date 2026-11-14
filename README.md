# AI Code Reviewer

An AI-powered Python code review platform built with FastAPI, Streamlit, and Google Gemini.

## Features

- Static Python code analysis using AST.
- Detection of potentially unsafe code such as eval() and exec().
- AI-powered code review using Gemini.
- Static-analysis fallback when AI is unavailable.
- Code quality score out of 100.
- Severity breakdown: Critical, High, Medium, Low.
- Detailed findings with line numbers and suggestions.
- Interactive Streamlit dashboard.
- Downloadable JSON review reports.
- User registration and login.
- Secure password hashing using Argon2.
- JWT-based authentication.
- Protected API endpoints.
- User-specific review history.
- Personal analytics dashboard.
- SQLite database for persistent storage.
- Automated tests.

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
    GEMINI_MODEL=gemini-3.8-flash
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
| POST | /review | Review Python code (authenticated) |
| GET | /history | Retrieve personal review history (authenticated) |
| GET | /history/{review_id} | Retrieve a saved personal review (authenticated) |
| GET | /analytics | Retrieve personal review analytics (authenticated) |

Protected endpoints require a valid JWT bearer token in the Authorization header.

## Authentication

- Users can create accounts with a username, email, and password.
- Passwords are securely hashed using Argon2.
- Successful login returns a JWT access token.
- Access tokens expire after 30 minutes.
- Review, history, and analytics endpoints require authentication.
- Users can access only their own authenticated review records.

## Quality Scoring

| Severity | Deduction |
|---|---:|
| Critical | 25 |
| High | 15 |
| Medium | 8 |
| Low | 3 |

Starting score: 100. Minimum score: 0.

## Review History and Database

Review results and user accounts are stored locally in a SQLite database at `data/reviews.db`.

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

## Run Tests

    python -m pytest -q tests/

## Development Progress

- Day 1: FastAPI foundation and automated tests.
- Day 2: Static code analyzer and review API.
- Day 3: Gemini AI integration and fallback handling.
- Day 4: Quality scoring and structured review reports.
- Day 5: Streamlit frontend and downloadable JSON reports.
- Day 6: SQLite review history, saved review details, and history dashboard.
- Day 7: User authentication, JWT security, password hashing, protected APIs, and personal analytics.

## Author

Annapoorna S U

GitHub: https://github.com/annapoorna147
