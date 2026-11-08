
from fastapi import FastAPI

app = FastAPI(
    title="AI Code Reviewer",
    description="An AI-powered code review platform",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to AI Code Reviewer!",
        "status": "Running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
