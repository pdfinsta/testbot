"""
PostgreSQL persistence layer.

Replaces pending_state.json with a real database so state survives
restarts/redeploys on Render (whose filesystem is ephemeral).

Needs the DATABASE_URL environment variable, e.g.:
  postgres://user:password@host:5432/dbname

Render gives you this as the "Internal Database URL" on your
PostgreSQL instance's dashboard page.
"""

import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras


def _get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set the DATABASE_URL environment variable.")
    # Render's free Postgres requires SSL for external connections;
    # sslmode=require is harmless for internal connections too.
    return psycopg2.connect(database_url, sslmode="require")


@contextmanager
def get_cursor(commit: bool = False):
    conn = _get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist yet. Call once on startup."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS awaiting_screenshot (
                user_id BIGINT PRIMARY KEY,
                course_id TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_approvals (
                request_id TEXT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username TEXT,
                course_id TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )


# ---------------------------------------------------------------
# awaiting_screenshot table
# ---------------------------------------------------------------
def set_awaiting_screenshot(user_id: int, course_id: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO awaiting_screenshot (user_id, course_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET course_id = EXCLUDED.course_id;
            """,
            (user_id, course_id),
        )


def pop_awaiting_screenshot(user_id: int):
    """Returns the course_id the user was paying for, or None. Deletes the row."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM awaiting_screenshot WHERE user_id = %s RETURNING course_id;",
            (user_id,),
        )
        row = cur.fetchone()
        return row["course_id"] if row else None


# ---------------------------------------------------------------
# pending_approvals table
# ---------------------------------------------------------------
def add_pending_approval(request_id: str, user_id: int, username: str, course_id: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO pending_approvals (request_id, user_id, username, course_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (request_id) DO NOTHING;
            """,
            (request_id, user_id, username, course_id),
        )


def pop_pending_approval(request_id: str):
    """Returns dict with user_id/username/course_id, or None. Deletes the row."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            DELETE FROM pending_approvals WHERE request_id = %s
            RETURNING user_id, username, course_id;
            """,
            (request_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
