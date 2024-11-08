"""SQLite DB Tools"""
import sqlite3


def setup_database():
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            document_id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT
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
        INSERT INTO summaries (document_id, title, summary) 
        VALUES (?, ?, ?) ON CONFLICT(document_id) DO UPDATE SET title=excluded.title, summary=excluded.summary
    """, (document_id, title, summary))
    conn.commit()
    conn.close()
