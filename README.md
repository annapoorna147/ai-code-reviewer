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
- Automated tests.

## Technology Stack

- Python 3.13
- FastAPI
- Streamlit
- Google Gemini API
- Pydantic
- Python AST
- Requests
- Pytest
- Uvicorn

## Installation

    git clone https://github.com/annapoorna147/ai-code-reviewer.git
    cd ai-code-reviewer
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Gemini Configuration

Create a .env file:

    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=gemini-3.8-flash

Never upload your API key to GitHub.

## Run Backend

    uvicorn app.main:app --reload

## Run Frontend

Open another Terminal window:

    cd ~/ai-code-reviewer
    source .venv/bin/activate
    streamlit run frontend.py

Frontend: http://localhost:8501

API documentation: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Application home |
| GET | /health | Health check |
| POST | /review | Review Python code |

## Quality Scoring

| Severity | Deduction |
|---|---:|
| Critical | 25 |
| High | 15 |
| Medium | 8 |
| Low | 3 |

Starting score: 100. Minimum score: 0.

## Run Tests

    python -m pytest -v --ignore=ai-code-reviewer

## Development Progress

- Day 1: FastAPI foundation and automated tests.
- Day 2: Static code analyzer and review API.
- Day 3: Gemini AI integration and fallback handling.
- Day 4: Quality scoring and structured review reports.
- Day 5: Streamlit frontend and downloadable JSON reports.

## Author

Annapoorna S U

GitHub: https://github.com/annapoorna147
