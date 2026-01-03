import MySQLdb
from db_config import get_db_connection

def patch_database():
    print("Starting database patch...")
    try:
        db = get_db_connection()
        cur = db.cursor()
        
        # Check if 'verified' column exists
        cur.execute("SHOW COLUMNS FROM ai_suggestions LIKE 'verified'")
        result = cur.fetchone()
        
        if not result:
            print("Column 'verified' not found. Adding it now...")
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN verified BOOLEAN DEFAULT FALSE")
            db.commit()
            print("Column 'verified' added successfully.")
        else:
            print("Column 'verified' already exists.")

        # Also check for other potential missing columns from database.sql
        # doctor_feedback
        cur.execute("SHOW COLUMNS FROM ai_suggestions LIKE 'doctor_feedback'")
        if not cur.fetchone():
            print("Adding 'doctor_feedback'...")
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN doctor_feedback TEXT NULL")
            db.commit()

        # doctor_status
        cur.execute("SHOW COLUMNS FROM ai_suggestions LIKE 'doctor_status'")
        if not cur.fetchone():
            print("Adding 'doctor_status'...")
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN doctor_status ENUM('Approved', 'Rejected', 'Pending') DEFAULT 'Pending'")
            db.commit()

        db.close()
        print("Database patch completed successfully.")
        
    except MySQLdb.Error as e:
        print(f"Error patching database: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    patch_database()
