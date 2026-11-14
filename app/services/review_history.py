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

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(reviews)"
            ).fetchall()
        }

        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE reviews ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )


def save_review(
    code: str,
    result: ReviewResponse,
    user_id: int | None = None,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    result_json = result.model_dump_json()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reviews (created_at, code, result_json, user_id)
            VALUES (?, ?, ?, ?)
            """,
            (created_at, code, result_json, user_id),
        )

        return cursor.lastrowid


def get_history(limit: int = 20, user_id: int | None = None) -> list[dict]:
    with get_connection() as connection:
        if user_id is None:
            rows = connection.execute(
                """
                SELECT id, created_at, result_json
                FROM reviews
                WHERE user_id IS NULL
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, created_at, result_json
                FROM reviews
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
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


def get_review(review_id: int, user_id: int | None = None) -> dict | None:
    with get_connection() as connection:
        if user_id is None:
            row = connection.execute(
                """
                SELECT id, created_at, code, result_json
                FROM reviews
                WHERE id = ? AND user_id IS NULL
                """,
                (review_id,),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT id, created_at, code, result_json
                FROM reviews
                WHERE id = ? AND user_id = ?
                """,
                (review_id, user_id),
            ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "code": row["code"],
        "result": json.loads(row["result_json"]),
    }


def get_analytics(user_id: int) -> dict:
    """Return review analytics for one authenticated user."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT result_json
            FROM reviews
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

    total_reviews = len(rows)
    total_issues = 0
    total_score = 0

    severity_distribution = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for row in rows:
        result = json.loads(row["result_json"])

        total_score += result["quality_score"]
        total_issues += result["total_issues"]

        summary = result["severity_summary"]

        for severity in severity_distribution:
            severity_distribution[severity] += summary.get(severity, 0)

    average_score = (
        round(total_score / total_reviews, 2)
        if total_reviews else 0
    )

    return {
        "total_reviews": total_reviews,
        "average_quality_score": average_score,
        "total_issues": total_issues,
        "severity_distribution": severity_distribution,
    }
