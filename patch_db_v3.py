import MySQLdb
from db_config import get_db_connection

def patch():
    print("Connecting to database...")
    try:
        db = get_db_connection()
        db.autocommit(True)
        cur = db.cursor()

        print("Creating 'dht11_readings' table...")
        try:
            cur.execute("""
                CREATE TABLE dht11_readings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(100) NOT NULL,
                    temperature FLOAT,
                    humidity FLOAT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
                )
            """)
            print(" -> 'dht11_readings' table created successfully")
        except MySQLdb.OperationalError as e:
            if "already exists" in str(e):
                print(" -> 'dht11_readings' table already exists")
            else:
                print(f" -> Error creating 'dht11_readings' table: {e}")

        db.close()
        print("Patch v3 complete.")

    except Exception as e:
        print(f"Critical connection error: {e}")

if __name__ == "__main__":
    patch()
