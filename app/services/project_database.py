import sqlite3
from datetime import datetime, timezone

from app.services.review_history import get_connection


def initialize_project_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_projects_user_id
            ON projects(user_id)
        """)


def create_project(name: str, description: str, user_id: int):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO projects
            (name, description, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, user_id, now, now),
        )
        project_id = cursor.lastrowid

    return get_project(project_id, user_id)


def get_projects(user_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, description, user_id, created_at, updated_at
            FROM projects
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_project(project_id: int, user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, description, user_id, created_at, updated_at
            FROM projects
            WHERE id = ? AND user_id = ?
            """,
            (project_id, user_id),
        ).fetchone()

        return dict(row) if row else None


def update_project(project_id: int, user_id: int, name: str, description: str):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (name, description, now, project_id, user_id),
        )

        if cursor.rowcount == 0:
            return None

    return get_project(project_id, user_id)


def delete_project(project_id: int, user_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM projects
            WHERE id = ? AND user_id = ?
            """,
            (project_id, user_id),
        )

        return cursor.rowcount > 0
