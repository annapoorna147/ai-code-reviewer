import sqlite3

from app.services.review_history import get_connection


def initialize_user_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def create_user(username: str, email: str, password_hash: str):
    from datetime import datetime, timezone

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    email.lower(),
                    password_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_by_email(email: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()


def get_user_by_id(user_id: int):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
