import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.models.review import ReviewResponse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "reviews.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                code TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
        """)


def save_review(code: str, result: ReviewResponse) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    result_json = result.model_dump_json()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reviews (created_at, code, result_json)
            VALUES (?, ?, ?)
            """,
            (created_at, code, result_json),
        )

        return cursor.lastrowid


def get_history(limit: int = 20) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, result_json
            FROM reviews
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    history = []

    for row in rows:
        result = json.loads(row["result_json"])

        history.append({
            "id": row["id"],
            "created_at": row["created_at"],
            "quality_score": result["quality_score"],
            "total_issues": result["total_issues"],
            "status": result["status"],
            "ai_status": result["ai_status"],
        })

    return history


def get_review(review_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, created_at, code, result_json
            FROM reviews
            WHERE id = ?
            """,
            (review_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "code": row["code"],
        "result": json.loads(row["result_json"]),
    }
