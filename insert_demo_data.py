#!/usr/bin/env python3
"""
Insert demo data directly into the database
"""

import sqlite3
import json
from datetime import datetime, date, time, timedelta

def insert_demo_data():
    """Insert demo data into SQLite database"""
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    print("Inserting demo data...")
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM appointments")
        cursor.execute("DELETE FROM patients") 
        cursor.execute("DELETE FROM doctor_schedules")
        cursor.execute("DELETE FROM symptom_mappings")
        cursor.execute("DELETE FROM pre_visit_instructions")
        cursor.execute("DELETE FROM specialties")
        cursor.execute("DELETE FROM doctors")
        
        # Insert specialties
        specialties = [
            (1, "Cardiology", "Heart and cardiovascular system", "Please bring previous ECG reports. Fast for 12 hours if blood tests required."),
            (2, "Gastroenterology", "Digestive system and stomach", "Fast for 8 hours before appointment. Bring list of current medications."),
            (3, "General Medicine", "General health and routine checkups", "Bring previous medical reports and vaccination records.")
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO specialties (id, name, description, pre_visit_instructions) VALUES (?, ?, ?, ?)",
            specialties
        )
        
        # Insert doctors
        doctors = [
            (1, "Dr. Rahman", "Cardiology", "+8801712345001", "rahman@xhospital.com"),
            (2, "Dr. Ayesha", "Gastroenterology", "+8801712345002", "ayesha@xhospital.com"), 
            (3, "Dr. Karim", "General Medicine", "+8801712345003", "karim@xhospital.com")
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO doctors (id, name, specialty, phone, email) VALUES (?, ?, ?, ?, ?)",
            doctors
        )
        
        # Insert doctor schedules
        schedules = [
            # Dr. Rahman (Cardiology) - Mon-Thu, 6PM-8PM
            (1, 1, 1, "18:00", "20:00", True),  # Monday
            (1, 2, 1, "18:00", "20:00", True),  # Tuesday
            (1, 3, 1, "18:00", "20:00", True),  # Wednesday
            (1, 4, 1, "18:00", "20:00", True),  # Thursday
            
            # Dr. Ayesha (Gastroenterology) - Sat-Tue, 4PM-6PM
            (2, 6, 2, "16:00", "18:00", True),  # Saturday
            (2, 0, 2, "16:00", "18:00", True),  # Sunday
            (2, 1, 2, "16:00", "18:00", True),  # Monday
            (2, 2, 2, "16:00", "18:00", True),  # Tuesday
            
            # Dr. Karim (General Medicine) - Every day, 10AM-2PM
            (3, 0, 3, "10:00", "14:00", True),  # Sunday
            (3, 1, 3, "10:00", "14:00", True),  # Monday
            (3, 2, 3, "10:00", "14:00", True),  # Tuesday
            (3, 3, 3, "10:00", "14:00", True),  # Wednesday
            (3, 4, 3, "10:00", "14:00", True),  # Thursday
            (3, 5, 3, "10:00", "14:00", True),  # Friday
            (3, 6, 3, "10:00", "14:00", True),  # Saturday
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO doctor_schedules (doctor_id, day_of_week, doctor_id, start_time, end_time, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            schedules
        )
        
        # Insert symptom mappings
        symptom_mappings = [
            # Cardiology
            (1, json.dumps(["chest pain", "heart", "cardiac", "palpitation", "chest tightness"]), 1, 3),
            
            # Gastroenterology  
            (2, json.dumps(["stomach pain", "digestion", "gastric", "stomach", "abdominal", "nausea", "vomiting"]), 2, 2),
            
            # General Medicine
            (3, json.dumps(["fever", "headache", "general", "checkup", "routine", "cold", "flu"]), 3, 1)
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO symptom_mappings (id, symptom_keywords, specialty_id, priority) VALUES (?, ?, ?, ?)",
            symptom_mappings
        )
        
        # Insert some sample patients and appointments
        patients = [
            (1, "John Smith", "+8801234567890", "john@email.com", "1990-05-15", "Male", "Dhaka, Bangladesh"),
            (2, "Jane Doe", "+8801234567891", "jane@email.com", "1985-08-22", "Female", "Chittagong, Bangladesh")
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO patients (id, name, phone, email, date_of_birth, gender, address) VALUES (?, ?, ?, ?, ?, ?, ?)",
            patients
        )
        
        # Insert sample appointments
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        appointments = [
            (1, 1, 1, tomorrow.isoformat(), "18:30", 30, "scheduled", "Chest pain and palpitations", "", "XH001", "chat"),
            (2, 2, 3, today.isoformat(), "11:00", 30, "scheduled", "General health checkup", "", "XH002", "voice")
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, duration_minutes, status, symptoms, notes, serial_number, booking_channel) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            appointments
        )
        
        conn.commit()
        print("Demo data inserted successfully!")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM specialties")
        specialty_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctor_schedules")
        schedule_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appointments")
        appointment_count = cursor.fetchone()[0]
        
        print(f"Data verification:")
        print(f"- Doctors: {doctor_count}")
        print(f"- Specialties: {specialty_count}")
        print(f"- Schedules: {schedule_count}")
        print(f"- Appointments: {appointment_count}")
        
    except Exception as e:
        print(f"Error inserting data: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    insert_demo_data()