import MySQLdb
from db_config import get_db_connection
import sys

def patch():
    print("Connecting to database...")
    try:
        db = get_db_connection()
        db.autocommit(True) # Ensure immediate commit
        cur = db.cursor()
        
        print("Checking 'verified' column...")
        try:
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN verified BOOLEAN DEFAULT FALSE")
            print(" -> Added 'verified'")
        except MySQLdb.OperationalError as e:
            if "Duplicate column" in str(e):
                print(" -> 'verified' already exists")
            else:
                print(f" -> Error adding 'verified': {e}")

        print("Checking 'doctor_feedback' column...")
        try:
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN doctor_feedback TEXT NULL")
            print(" -> Added 'doctor_feedback'")
        except MySQLdb.OperationalError as e:
            if "Duplicate column" in str(e):
                print(" -> 'doctor_feedback' already exists")
            else:
                print(f" -> Error adding 'doctor_feedback': {e}")

        print("Checking 'doctor_status' column...")
        try:
            cur.execute("ALTER TABLE ai_suggestions ADD COLUMN doctor_status ENUM('Approved', 'Rejected', 'Pending') DEFAULT 'Pending'")
            print(" -> Added 'doctor_status'")
        except MySQLdb.OperationalError as e:
            if "Duplicate column" in str(e):
                print(" -> 'doctor_status' already exists")
            else:
                print(f" -> Error adding 'doctor_status': {e}")

        db.close()
        print("Patch complete.")

    except Exception as e:
        print(f"Critical connection error: {e}")

if __name__ == "__main__":
    patch()
