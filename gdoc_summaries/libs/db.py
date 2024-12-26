"""SQLite DB Tools"""
import sqlite3

from gdoc_summaries.libs import constants


def _table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists in the database"""
    cursor.execute("""
        SELECT count(name) 
        FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone()[0] == 1

def _run_migration_1_add_summary_type():
    """First migration: Add summary_type column and set existing records to 'TDD'"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    # Check if summary_type column exists
    cursor.execute("PRAGMA table_info(summaries)")
    columns = cursor.fetchall()
    has_summary_type = any(column[1] == 'summary_type' for column in columns)
    
    if not has_summary_type:
        print("Running migration 1: Adding summary_type column")
        cursor.execute("ALTER TABLE summaries ADD COLUMN summary_type TEXT DEFAULT 'TDD'")
        cursor.execute("UPDATE summaries SET summary_type = 'TDD'")
        conn.commit()
    
    conn.close()

def _run_migration_2_add_sections_table():
    """Second migration: Add sections table for biweekly updates"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    if not _table_exists(cursor, "summary_sections"):
        print("Running migration 2: Adding sections table")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT,
                section_date TEXT,
                section_content TEXT,
                section_summary TEXT,
                processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent INTEGER DEFAULT 0,
                FOREIGN KEY(document_id) REFERENCES summaries(document_id)
            )
        """)
        conn.commit()
    
    conn.close()

def run_migrations():
    """Run all database migrations in order"""
    migrations = [
        _run_migration_1_add_summary_type,
        _run_migration_2_add_sections_table,
    ]
    
    for migration in migrations:
        migration()

def setup_database():
    """Initialize database and run migrations"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    # Create initial table structure
    if not _table_exists(cursor, "summaries"):
        print("Creating summaries table")
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
    
    # Run any pending migrations
    run_migrations()


def get_summary_from_db(document_id: str) -> constants.Summary | None:
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, summary, date_published, summary_type 
        FROM summaries 
        WHERE document_id = ?
    """, (document_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return constants.Summary(
            document_id=document_id,
            title=result[0],
            content=result[1],
            date_published=result[2],
            summary_type=result[3]
        )
    return None

def save_summary_to_db(summary: constants.Summary):
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summaries (document_id, title, summary, date_published, sent, summary_type) 
        VALUES (?, ?, ?, ?, 0, ?) 
        ON CONFLICT(document_id) DO UPDATE SET 
            title=excluded.title, 
            summary=excluded.summary, 
            date_published=excluded.date_published,
            summary_type=excluded.summary_type,
            sent=0
    """, (
        summary.document_id, 
        summary.title, 
        summary.content, 
        summary.date_published, 
        summary.summary_type.value
    ))
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

def get_latest_section_date(document_id: str) -> str | None:
    """Get the most recent section date for a document"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT section_date 
        FROM summary_sections 
        WHERE document_id = ? 
        ORDER BY section_date DESC 
        LIMIT 1
    """, (document_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_section_to_db(
    document_id: str,
    section_date: str,
    section_content: str,
    section_summary: str
) -> None:
    """Save a new document section"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summary_sections 
        (document_id, section_date, section_content, section_summary) 
        VALUES (?, ?, ?, ?)
    """, (document_id, section_date, section_content, section_summary))
    conn.commit()
    conn.close()

def get_unsent_sections(document_id: str) -> list[tuple]:
    """Get all unsent sections for a document"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT section_date, section_summary 
        FROM summary_sections 
        WHERE document_id = ? AND sent = 0 
        ORDER BY section_date DESC
    """, (document_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def mark_sections_as_sent(document_id: str) -> None:
    """Mark all sections for a document as sent"""
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE summary_sections 
        SET sent = 1 
        WHERE document_id = ? AND sent = 0
    """, (document_id,))
    conn.commit()
    conn.close()
