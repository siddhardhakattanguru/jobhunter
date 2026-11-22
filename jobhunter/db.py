"""SQLite tracker: dedupes jobs across runs and records your application status."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("jobs.db")
STATUSES = ("new", "shortlisted", "applied", "interview", "offer", "rejected", "skipped")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source TEXT, title TEXT, company TEXT, location TEXT, url TEXT,
            score INTEGER, reason TEXT,
            status TEXT DEFAULT 'new',
            notes_file TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def is_known(conn: sqlite3.Connection, job_id: str) -> bool:
    return conn.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone() is not None


def save(conn, job, score: int, reason: str, notes_file: str | None = None) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO jobs
        (id, source, title, company, location, url, score, reason, notes_file)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (job.id, job.source, job.title, job.company, job.location, job.url,
         score, reason, notes_file),
    )
    conn.commit()


def set_status(conn, job_id: str, status: str) -> bool:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    cur = conn.execute(
        "UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, job_id),
    )
    conn.commit()
    return cur.rowcount > 0


def list_jobs(conn, min_score: int = 0, status: str | None = None):
    q = "SELECT * FROM jobs WHERE score >= ?"
    args: list = [min_score]
    if status:
        q += " AND status = ?"
        args.append(status)
    q += " ORDER BY score DESC, created_at DESC"
    return conn.execute(q, args).fetchall()
