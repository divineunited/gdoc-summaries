import sqlite3

from gdoc_summaries.libs import db


def reset_database():
    confirmation = input("\n⚠️  WARNING: This will delete all existing summaries data! Are you sure? (type 'yes' to confirm): ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    # Drop all existing tables
    cursor.execute("DROP TABLE IF EXISTS summary_sections")  # Drop sections first due to foreign key
    cursor.execute("DROP TABLE IF EXISTS summaries")
    conn.commit()
    conn.close()
    
    # Use the setup_database function from db.py to recreate the tables
    db.setup_database()
    print("Database tables have been reset successfully!")

if __name__ == "__main__":
    reset_database()
    