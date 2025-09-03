import sqlite3
import os
from pathlib import Path

def init_database():
    """Initialize the hospital database with schema and demo data."""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    db_path = project_root / "hospital.db"
    schema_path = project_root / "database" / "schema.sql"
    demo_data_path = project_root / "database" / "seeds" / "demo_data_simple.sql"
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Execute schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            cursor.executescript(schema_sql)
        print("Database schema created successfully")
        
        # Execute demo data
        with open(demo_data_path, 'r') as f:
            demo_sql = f.read()
            cursor.executescript(demo_sql)
        print("Demo data inserted successfully")
        
        # Commit changes
        conn.commit()
        print(f"Database initialized successfully at: {db_path}")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appointments")
        appointment_count = cursor.fetchone()[0]
        
        print(f"Database contains: {doctor_count} doctors, {patient_count} patients, {appointment_count} appointments")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()