# AI Code Reviewer

An AI-powered code review platform built with Python and FastAPI.

## Features

- FastAPI backend
- Health check endpoint
- Automated API testing
- AI-powered code analysis (under development)

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Pytest
- Google Gemini API

## Run Locally

Activate the virtual environment:

    source .venv/bin/activate

Start the backend:

    uvicorn app.main:app --reload

## API Endpoints

| Endpoint | Description |
|---|---|
| / | Application home |
| /health | Health check |
| /docs | API documentation |

## Run Tests

    python -m pytest -v
