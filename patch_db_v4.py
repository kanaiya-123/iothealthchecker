# patch_db_v4.py
import MySQLdb
from db_config import get_db_connection

def patch():
    print("Connecting to database...")
    try:
        db = get_db_connection()
        db.autocommit(True)
        cur = db.cursor()

        print("Patching 'dht11_readings' table...")
        
        # Check for and drop the foreign key if it exists
        try:
            cur.execute("SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_NAME = 'dht11_readings' AND COLUMN_NAME = 'device_id' AND REFERENCED_TABLE_NAME = 'devices';")
            fk_name = cur.fetchone()
            if fk_name:
                cur.execute(f"ALTER TABLE dht11_readings DROP FOREIGN KEY {fk_name[0]}")
                print(f" -> Dropped foreign key '{fk_name[0]}'")
        except MySQLdb.OperationalError as e:
            print(f" -> Could not drop foreign key (might not exist): {e}")


        # Modify the column type
        try:
            cur.execute("ALTER TABLE dht11_readings MODIFY COLUMN device_id VARCHAR(100) NOT NULL")
            print(" -> Modified 'device_id' column to VARCHAR(100)")
        except MySQLdb.OperationalError as e:
            print(f" -> Error modifying column: {e}")

        # Add the correct foreign key
        try:
            cur.execute("ALTER TABLE dht11_readings ADD CONSTRAINT fk_dht11_device_id FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE")
            print(" -> Added correct foreign key constraint")
        except MySQLdb.OperationalError as e:
            if "already exists" in str(e):
                 print(" -> Foreign key already exists.")
            else:
                print(f" -> Error adding foreign key: {e}")

        db.close()
        print("Patch v4 complete.")

    except Exception as e:
        print(f"Critical connection error: {e}")

if __name__ == "__main__":
    patch()
