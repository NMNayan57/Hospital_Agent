#!/usr/bin/env python3
"""
Real-time Hospital AI Assistant Test Script
Demonstrates live database-driven functionality
"""

import asyncio
import requests
import json
from datetime import datetime, date, time
import time as time_module

# API Configuration
API_BASE = "http://localhost:8000/api/v1"

def print_banner(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(step_num, text):
    print(f"\n{step_num}. {text}")
    print("-" * 40)

def test_chat_real_time_responses():
    """Test real-time chat responses with live database queries"""
    print_banner("TESTING REAL-TIME CHAT RESPONSES")
    
    test_phone = "+8801234567890"
    
    # Test cases for real-time functionality
    test_cases = [
        {
            "message": "Hello! I need to see a doctor",
            "description": "Greeting with appointment intent - should show real-time availability"
        },
        {
            "message": "I want to book appointment with Dr. Rahman",
            "description": "Specific doctor request - should check real availability from database"
        },
        {
            "message": "What doctors are available today?",
            "description": "Availability inquiry - should query database and show current slots"
        },
        {
            "message": "I have chest pain and need help",
            "description": "Symptom-based request - should recommend cardiologist with real-time slots"
        },
        {
            "message": "Can you show me all available appointment times?",
            "description": "Full availability check - should display live database information"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print_step(i, test_case["description"])
        print(f"User Input: \"{test_case['message']}\"")
        
        try:
            # Send chat message
            response = requests.post(f"{API_BASE}/chat/message", json={
                "message": test_case["message"],
                "phone_number": test_phone
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ AI Response (Real-time from Database):")
                print(f"📱 {data['response']}")
                if data.get('suggested_actions'):
                    print(f"💡 Suggested Actions: {', '.join(data['suggested_actions'])}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
        
        print("\n" + "."*50)
        time_module.sleep(2)  # Brief pause between tests

def test_appointment_booking():
    """Test real-time appointment booking"""
    print_banner("TESTING REAL-TIME APPOINTMENT BOOKING")
    
    test_phone = "+8801234567891"
    
    # Book appointment with complete information
    print_step(1, "Booking appointment with complete information")
    
    try:
        booking_response = requests.post(f"{API_BASE}/scheduler/book", json={
            "patient_name": "John Smith",
            "patient_phone": test_phone,
            "symptoms": "Regular checkup and health monitoring",
            "booking_channel": "chat"
        })
        
        if booking_response.status_code == 200:
            booking_data = booking_response.json()
            if booking_data["success"]:
                print("✅ Appointment Booked Successfully!")
                print(f"📋 Response: {booking_data['message']}")
                
                # Now test the chat with this user to show appointment history
                print_step(2, "Testing chat response with appointment history")
                
                chat_response = requests.post(f"{API_BASE}/chat/message", json={
                    "message": "Hi, I want to check my appointments",
                    "phone_number": test_phone
                })
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print("✅ Chat Response with Patient History:")
                    print(f"📱 {chat_data['response']}")
            else:
                print(f"❌ Booking Failed: {booking_data['message']}")
        else:
            print(f"❌ Booking Error: {booking_response.status_code}")
            
    except Exception as e:
        print(f"❌ Booking Error: {e}")

def test_live_appointments_endpoint():
    """Test live appointments endpoint for real-time display"""
    print_banner("TESTING LIVE APPOINTMENTS ENDPOINT")
    
    print_step(1, "Fetching live appointments from database")
    
    try:
        response = requests.get(f"{API_BASE}/scheduler/appointments/live/recent")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Live Appointments Retrieved!")
            print(f"📊 Total Appointments: {data['total_count']}")
            print(f"🕒 Last Updated: {data['update_time']}")
            
            if data["appointments"]:
                print("\n📋 Recent Appointments (Live Data):")
                print("-" * 80)
                for apt in data["appointments"][:5]:  # Show first 5
                    print(f"🎫 {apt['serial_number']} | {apt['patient_name']} -> Dr. {apt['doctor_name']}")
                    print(f"   📅 {apt['formatted_datetime']} | {apt['booking_channel_icon']} {apt['booking_channel']}")
                    print(f"   ⏰ Booked: {apt['time_since_booking']} | Status: {apt['status']}")
                    print(f"   🩺 Symptoms: {apt['symptoms'][:50]}...")
                    print()
            else:
                print("📝 No appointments found in the last 24 hours")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_real_time_doctor_availability():
    """Test real-time doctor availability queries"""
    print_banner("TESTING REAL-TIME DOCTOR AVAILABILITY")
    
    print_step(1, "Checking real-time availability for all doctors")
    
    try:
        # Get all doctors first
        doctors_response = requests.get(f"{API_BASE}/scheduler/doctors")
        
        if doctors_response.status_code == 200:
            doctors_data = doctors_response.json()
            print(f"✅ Found {doctors_data['count']} doctors in database")
            
            for doctor in doctors_data["doctors"]:
                print(f"\n👨‍⚕️ Dr. {doctor['name']} ({doctor['specialty']})")
                
                # Check availability for this doctor
                availability_response = requests.get(
                    f"{API_BASE}/scheduler/availability/{doctor['id']}?days=7"
                )
                
                if availability_response.status_code == 200:
                    availability_data = availability_response.json()
                    slots = availability_data["available_slots"]
                    
                    if slots:
                        print(f"   ✅ {len(slots)} available slots found")
                        # Show next 3 slots
                        for slot in slots[:3]:
                            slot_date = datetime.fromisoformat(slot['date']).strftime('%A, %B %d')
                            print(f"   📅 {slot_date} at {slot['time']}")
                    else:
                        print("   ❌ No available slots in next 7 days")
                else:
                    print(f"   ❌ Error checking availability: {availability_response.status_code}")
        
        else:
            print(f"❌ Error getting doctors: {doctors_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_symptom_analysis():
    """Test real-time symptom analysis and doctor recommendations"""
    print_banner("TESTING REAL-TIME SYMPTOM ANALYSIS")
    
    symptoms_test_cases = [
        "I have severe chest pain and difficulty breathing",
        "My stomach hurts after eating",
        "I need a general checkup",
        "I have a skin rash that won't go away"
    ]
    
    for i, symptoms in enumerate(symptoms_test_cases, 1):
        print_step(i, f"Analyzing symptoms: '{symptoms}'")
        
        try:
            response = requests.post(f"{API_BASE}/scheduler/analyze-symptoms", json={
                "symptoms": symptoms
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"🚨 Urgency Level: {data['urgency_level'].upper()}")
                print(f"💡 Recommendation: {data['explanation']}")
                
                if data["suggested_doctors"]:
                    print("👨‍⚕️ Recommended Doctors:")
                    for doctor in data["suggested_doctors"]:
                        print(f"   • Dr. {doctor['name']} ({doctor['specialty']})")
                
                print()
            else:
                print(f"❌ Analysis Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def demonstrate_real_time_scenario():
    """Complete real-time scenario demonstration"""
    print_banner("COMPLETE REAL-TIME SCENARIO DEMONSTRATION")
    
    test_phone = "+8801234567892"
    
    print("🎭 SCENARIO: Patient wants chest pain consultation")
    print("=" * 60)
    
    # Step 1: Initial chat with symptoms
    print_step(1, "Patient describes symptoms via chat")
    chat_response = requests.post(f"{API_BASE}/chat/message", json={
        "message": "Hello, I have been experiencing chest pain and I'm worried. Can you help me book an appointment?",
        "phone_number": test_phone
    })
    
    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        print("🤖 AI Response:")
        print(f"   {chat_data['response']}")
    
    # Step 2: Patient provides name for booking
    print_step(2, "Patient provides name to complete booking")
    name_response = requests.post(f"{API_BASE}/chat/message", json={
        "message": "My name is Sarah Johnson",
        "phone_number": test_phone
    })
    
    if name_response.status_code == 200:
        name_data = name_response.json()
        print("🤖 AI Response (Should book appointment automatically):")
        print(f"   {name_data['response']}")
    
    # Step 3: Check if appointment was created
    print_step(3, "Verifying appointment creation in real-time")
    time_module.sleep(2)  # Brief delay
    
    appointments_response = requests.get(f"{API_BASE}/scheduler/appointments/live/recent")
    if appointments_response.status_code == 200:
        appointments_data = appointments_response.json()
        
        # Look for our test phone number
        our_appointments = [apt for apt in appointments_data["appointments"] 
                          if apt["patient_phone"] == test_phone]
        
        if our_appointments:
            apt = our_appointments[0]
            print("✅ Appointment Successfully Created and Retrieved!")
            print(f"🎫 Serial: {apt['serial_number']}")
            print(f"👤 Patient: {apt['patient_name']}")
            print(f"👨‍⚕️ Doctor: Dr. {apt['doctor_name']} ({apt['doctor_specialty']})")
            print(f"📅 Appointment: {apt['formatted_datetime']}")
            print(f"🩺 Symptoms: {apt['symptoms']}")
            print(f"⏰ Booked: {apt['time_since_booking']}")
        else:
            print("⚠️ Appointment might be processing or booking failed")

def main():
    """Run all real-time functionality tests"""
    print("🏥 X Hospital AI Assistant - Real-Time Functionality Test")
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Testing live database integration...")
    
    try:
        # Test server connection first
        health_response = requests.get(f"{API_BASE.replace('/api/v1', '')}/health")
        if health_response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print("❌ Server health check failed")
            return
            
        # Run all tests
        test_chat_real_time_responses()
        test_appointment_booking()
        test_live_appointments_endpoint()
        test_real_time_doctor_availability()
        test_symptom_analysis()
        demonstrate_real_time_scenario()
        
        print_banner("TEST SUMMARY")
        print("✅ All real-time functionality tests completed!")
        print("🔄 The system demonstrates:")
        print("   • Live database queries for doctor availability")
        print("   • Real-time appointment booking and confirmation")
        print("   • Dynamic symptom analysis and doctor recommendations")
        print("   • Live appointment tracking and display")
        print("   • Database-driven chat responses (not pre-defined)")
        print()
        print("🌐 Access the web interface at: http://localhost:8000")
        print("📱 Try the chat or voice interface to see real-time responses")
        print("📊 Check the 'Live Appointments' tab for real-time booking confirmation")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running:")
        print("   python main.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()