import MySQLdb
from db_config import get_db_connection

def check_columns():
    try:
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("DESCRIBE ai_suggestions")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Current columns in ai_suggestions: {columns}")
        
        missing = []
        if 'verified' not in columns: missing.append('verified')
        if 'doctor_feedback' not in columns: missing.append('doctor_feedback')
        if 'doctor_status' not in columns: missing.append('doctor_status')
        
        if missing:
            print(f"Missing columns: {missing}")
        else:
            print("All required columns are present.")
            
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
