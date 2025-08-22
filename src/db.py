import os
import sys
from dotenv import load_dotenv
import mysql.connector
from config_manager import get_pc_id

# Load .env dari lokasi yang sesuai (baik saat dev maupun saat exe)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

dotenv_path = os.path.join(base_path, ".env")
load_dotenv(dotenv_path)

def get_connection():
    """Establishes and returns a database connection."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def insert_history(record):
    """
    Inserts a new history record into the database, including the PC ID.
    Args:
        record (dict): A dictionary containing the history data.
    """
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO history
        (name, mode, squat_count, squat_duration, plank_active_time, plank_total_time, timestamp, pc_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        print(f"DB: Attempting to insert record with pc_id: {record.get('pc_id')}") # DEBUG PRINT
        cursor.execute(sql, (
            record.get("name"),
            record.get("mode"),
            record.get("squat_count", 0),
            record.get("squat_duration", 0),
            record.get("plank_active_time", 0),
            record.get("plank_total_time", 0),
            record.get("timestamp"),
            record.get("pc_id")
        ))
        conn.commit()
        print("DB: Insert successful.") # DEBUG PRINT
    except mysql.connector.Error as err:
        print(f"DB: Error inserting history: {err}") # DEBUG PRINT
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def fetch_all_history():
    """
    Fetches all history records for the current PC from the database.
    Returns:
        list: A list of dictionaries, each representing a history record.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    current_pc_id = get_pc_id() # Get the current PC's ID

    # Filter by pc_id
    sql = "SELECT * FROM history WHERE pc_id = %s ORDER BY timestamp DESC"
    try:
        cursor.execute(sql, (current_pc_id,))
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching history: {err}")
        results = []
    finally:
        cursor.close()
        conn.close()
    return results
