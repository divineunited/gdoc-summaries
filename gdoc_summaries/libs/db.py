"""SQLite DB Tools"""
import sqlite3


def setup_database():
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            document_id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_summary_from_db(document_id: str):
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM summaries WHERE document_id = ?", (document_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None


def save_summary_to_db(document_id: str, title: str, summary: str):
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summaries (document_id, title, summary, sent) 
        VALUES (?, ?, ?, 0) 
        ON CONFLICT(document_id) DO UPDATE SET title=excluded.title, summary=excluded.summary, sent=0
    """, (document_id, title, summary))
    conn.commit()
    conn.close()

def get_summary_sent_status(document_id: str):
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
