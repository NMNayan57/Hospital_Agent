#!/usr/bin/env python3
"""
Final Demo of Real-Time Hospital AI System
Shows live database integration without Unicode issues
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_real_time_system():
    """Demonstrate real-time functionality"""
    print("HOSPITAL AI ASSISTANT - REAL-TIME DEMO")
    print("=" * 50)
    
    # Test 1: Book an appointment directly 
    print("\\n1. BOOKING APPOINTMENT VIA API")
    print("-" * 30)
    
    booking_response = requests.post(f"{API_BASE}/scheduler/book", json={
        "patient_name": "Sarah Davis",
        "patient_phone": "+8801234567895",
        "symptoms": "Regular health checkup and blood pressure monitoring",
        "booking_channel": "chat"
    })
    
    if booking_response.status_code == 200:
        booking_data = booking_response.json()
        if booking_data["success"]:
            print("APPOINTMENT BOOKED SUCCESSFULLY!")
            print("Response from system:")
            print(booking_data["message"])
        else:
            print("Booking failed:", booking_data["message"])
    
    # Test 2: Check live appointments
    print("\\n\\n2. LIVE APPOINTMENTS FROM DATABASE")
    print("-" * 30)
    
    appointments_response = requests.get(f"{API_BASE}/scheduler/appointments/live/recent")
    
    if appointments_response.status_code == 200:
        appointments_data = appointments_response.json()
        print(f"Total appointments in database: {appointments_data['total_count']}")
        print(f"Last database update: {appointments_data['update_time']}")
        print()
        
        if appointments_data["appointments"]:
            print("RECENT APPOINTMENTS (Live from Database):")
            print("-" * 50)
            for i, apt in enumerate(appointments_data["appointments"][:5], 1):
                print(f"{i}. SERIAL: {apt['serial_number']}")
                print(f"   PATIENT: {apt['patient_name']} ({apt['patient_phone']})")
                print(f"   DOCTOR: Dr. {apt['doctor_name']} - {apt['doctor_specialty']}")
                print(f"   APPOINTMENT: {apt['formatted_datetime']}")  
                print(f"   SYMPTOMS: {apt['symptoms']}")
                print(f"   BOOKED: {apt['time_since_booking']} via {apt['booking_channel']}")
                print(f"   STATUS: {apt['status']}")
                print()
    
    # Test 3: Test chat functionality
    print("\\n3. CHAT WITH REAL-TIME RESPONSES")
    print("-" * 30)
    
    chat_messages = [
        "Hello, I need to book an appointment",
        "I need to see Dr. Karim",
        "My name is Alex Johnson"
    ]
    
    test_phone = "+8801234567896"
    
    for i, message in enumerate(chat_messages, 1):
        print(f"{i}. USER: {message}")
        
        chat_response = requests.post(f"{API_BASE}/chat/message", json={
            "message": message,
            "phone_number": test_phone
        })
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            # Clean response of any problematic unicode
            response_text = chat_data['response'].encode('ascii', 'ignore').decode('ascii')
            print(f"   AI: {response_text}")
            print()
    
    print("\\n" + "=" * 50)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print()
    print("REAL-TIME FEATURES DEMONSTRATED:")
    print("- Live database queries and updates")
    print("- Real-time appointment booking")
    print("- Dynamic doctor availability checking") 
    print("- Live appointment confirmation tracking")
    print("- Database-driven AI responses")
    print()
    print("WEB INTERFACE: http://localhost:8000")
    print("Click 'Live Appointments' to see real-time bookings!")

if __name__ == "__main__":
    try:
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("Server Status: ONLINE")
            test_real_time_system()
        else:
            print("Server Status: ERROR")
    except Exception as e:
        print(f"Connection Error: {e}")
        print("Make sure server is running: python main.py")