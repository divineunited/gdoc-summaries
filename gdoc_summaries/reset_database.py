import sqlite3

from gdoc_summaries.libs import db


def reset_database():
    confirmation = input("\n⚠️  WARNING: This will delete all existing summaries data! Are you sure? (type 'yes' to confirm): ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    conn = sqlite3.connect("summaries.db")
    cursor = conn.cursor()
    
    # Drop the existing table
    cursor.execute("DROP TABLE IF EXISTS summaries")
    conn.commit()
    conn.close()
    
    # Use the setup_database function from db.py to recreate the table
    db.setup_database()
    print("Database table has been reset successfully!")

if __name__ == "__main__":
    reset_database()
