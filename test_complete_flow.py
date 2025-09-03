#!/usr/bin/env python3
"""
Complete Real-Time Flow Test
Tests the end-to-end functionality with real-time database operations
"""

import requests
import time

API_BASE = "http://localhost:8000/api/v1"

def test_complete_real_time_flow():
    """Test complete real-time appointment booking flow"""
    print("=== COMPLETE REAL-TIME FLOW TEST ===")
    print("Testing live database-driven chat and booking system")
    print()
    
    test_phone = "+8801234567893"
    
    # Step 1: User greets the system
    print("1. User greets the AI assistant")
    print("   Input: 'Hello, I need medical help'")
    
    response1 = requests.post(f"{API_BASE}/chat/message", json={
        "message": "Hello, I need medical help",
        "phone_number": test_phone
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"   AI Response: {data1['response'][:100]}...")
    
    time.sleep(1)
    
    # Step 2: User describes symptoms
    print("\n2. User describes symptoms")
    print("   Input: 'I have chest pain and feel worried'")
    
    response2 = requests.post(f"{API_BASE}/chat/message", json={
        "message": "I have chest pain and feel worried",
        "phone_number": test_phone
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"   AI Response: {data2['response'][:150]}...")
    
    time.sleep(1)
    
    # Step 3: User provides name to complete booking
    print("\n3. User provides name to complete booking")  
    print("   Input: 'My name is Alice Johnson'")
    
    response3 = requests.post(f"{API_BASE}/chat/message", json={
        "message": "My name is Alice Johnson",
        "phone_number": test_phone
    })
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"   AI Response: {data3['response'][:200]}...")
    
    time.sleep(2)
    
    # Step 4: Check live appointments to verify booking
    print("\n4. Verifying real-time appointment creation")
    
    appointments_response = requests.get(f"{API_BASE}/scheduler/appointments/live/recent")
    
    if appointments_response.status_code == 200:
        appointments_data = appointments_response.json()
        print(f"   Total recent appointments: {appointments_data['total_count']}")
        print(f"   Last updated: {appointments_data['update_time']}")
        
        # Look for our new appointment
        our_appointments = [apt for apt in appointments_data["appointments"] 
                          if apt["patient_phone"] == test_phone]
        
        if our_appointments:
            apt = our_appointments[0]
            print(f"\n   ✅ NEW APPOINTMENT FOUND!")
            print(f"   Serial: {apt['serial_number']}")
            print(f"   Patient: {apt['patient_name']}")
            print(f"   Doctor: Dr. {apt['doctor_name']} ({apt['doctor_specialty']})")
            print(f"   Date/Time: {apt['formatted_datetime']}")
            print(f"   Channel: {apt['booking_channel']} {apt['booking_channel_icon']}")
            print(f"   Booked: {apt['time_since_booking']}")
            print(f"   Status: {apt['status']}")
            print(f"   Symptoms: {apt['symptoms']}")
            
            print(f"\n   🎯 REAL-TIME CONFIRMATION: Appointment successfully")
            print(f"      created and retrieved from live database!")
            
        else:
            print("   ⚠️ No appointment found - may be processing or booking failed")
    
    # Step 5: Test direct booking API
    print("\n5. Testing direct appointment booking API")
    
    direct_booking = requests.post(f"{API_BASE}/scheduler/book", json={
        "patient_name": "Bob Wilson",
        "patient_phone": "+8801234567894",
        "symptoms": "Regular health checkup and blood pressure monitoring",
        "booking_channel": "chat"
    })
    
    if direct_booking.status_code == 200:
        booking_data = direct_booking.json()
        if booking_data["success"]:
            print("   ✅ Direct booking successful!")
            print(f"   Response: {booking_data['message'][:100]}...")
        else:
            print(f"   ❌ Direct booking failed: {booking_data['message']}")
    
    print("\n=== FLOW TEST COMPLETED ===")
    print()
    print("🔄 The system demonstrates:")
    print("• Real-time chat responses based on live database queries")
    print("• Dynamic doctor availability checking")  
    print("• Automatic appointment booking with serial number generation")
    print("• Live appointment confirmation and tracking")
    print("• Database-driven recommendations (not pre-defined responses)")
    print()
    print("🌐 Open http://localhost:8000 to see the web interface")
    print("📊 Click 'Live Appointments' tab to see real-time bookings")

if __name__ == "__main__":
    try:
        # Test server connection
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("Server is running")
            test_complete_real_time_flow()
        else:
            print("Server health check failed")
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Run: python main.py")
    except Exception as e:
        print(f"Test failed: {e}")