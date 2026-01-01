import sqlite3
import os


def migrate():
    db_path = "./vb.sqlite"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if cash column already exists
        cursor.execute("PRAGMA table_info(positions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "cash" not in columns:
            print("Adding 'cash' column to 'positions' table...")
            cursor.execute("ALTER TABLE positions ADD COLUMN cash FLOAT DEFAULT 0.0")
            conn.commit()
            print("Successfully added 'cash' column.")
        else:
            print("'cash' column already exists in 'positions' table.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
