"""SQLite DB Tools"""
import sqlite3

from gdoc_summaries.libs import constants


def setup_database():
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            document_id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            date_published TEXT,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_summary_from_db(document_id: str) -> constants.Summary | None:
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, summary, date_published FROM summaries WHERE document_id = ?", (document_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return constants.Summary(
            document_id=document_id,
            title=result[0],
            content=result[1],
            date_published=result[2]
        )
    return None


def save_summary_to_db(summary: constants.Summary):
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summaries (document_id, title, summary, date_published, sent) 
        VALUES (?, ?, ?, ?, 0) 
        ON CONFLICT(document_id) DO UPDATE SET 
            title=excluded.title, 
            summary=excluded.summary, 
            date_published=excluded.date_published,
            sent=0
    """, (summary.document_id, summary.title, summary.content, summary.date_published))
    conn.commit()
    conn.close()

def get_summary_sent_status(document_id: str) -> 0|1:
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sent FROM summaries WHERE document_id = ?", (document_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def mark_summary_as_sent(document_id: str):
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE summaries SET sent = 1 WHERE document_id = ?", (document_id,))
    conn.commit()
    conn.close()
