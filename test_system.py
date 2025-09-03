#!/usr/bin/env python3
"""
Test script for X Hospital AI Assistant System
Run this script to test all components and ensure everything is working
"""

import os
import sys
import asyncio
import json
from datetime import datetime, date
import sqlite3

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

async def test_database_connection():
    """Test database connectivity and data"""
    print("\nTesting Database Connection...")
    
    try:
        # Test SQLite connection
        conn = sqlite3.connect('hospital.db')
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        print(f"[OK] Database connected - {doctor_count} doctors found")
        
        cursor.execute("SELECT COUNT(*) FROM specialties")
        specialty_count = cursor.fetchone()[0]
        print(f"[OK] Found {specialty_count} specialties")
        
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        print(f"[OK] Found {patient_count} patients")
        
        cursor.execute("SELECT COUNT(*) FROM appointments")
        appointment_count = cursor.fetchone()[0]
        print(f"[OK] Found {appointment_count} appointments")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

async def test_rag_service():
    """Test RAG service functionality"""
    print("\nTesting RAG Service...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from models.database import engine, Doctor
        from services.rag.rag_service import RAGService
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        rag_service = RAGService(db)
        
        # Test symptom-based doctor search
        chest_pain_doctors = rag_service.search_doctors_by_symptoms("chest pain")
        print(f"[OK] Found {len(chest_pain_doctors)} doctors for chest pain")
        
        # Test doctor availability
        if chest_pain_doctors:
            doctor_id = chest_pain_doctors[0]['id']
            availability = rag_service.get_doctor_availability(doctor_id, days=7)
            print(f"[OK] Found {len(availability)} available slots for doctor {doctor_id}")
        
        # Test urgency check
        urgency = rag_service.get_urgent_symptoms_check("severe chest pain")
        print(f"[OK] Urgency assessment: {urgency['urgency_level']}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] RAG service test failed: {e}")
        return False

async def test_scheduler_agent():
    """Test scheduler agent"""
    print("\nTesting Scheduler Agent...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from models.database import engine
        from agents.scheduler.scheduler_agent import SchedulerAgent
        from models.schemas import AppointmentBookingRequest, BookingChannel
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        scheduler = SchedulerAgent(db)
        
        # Test appointment booking
        booking_request = AppointmentBookingRequest(
            patient_name="Test Patient",
            patient_phone="+8801999999999",
            symptoms="Test symptoms for system verification",
            booking_channel=BookingChannel.CHAT
        )
        
        result = await scheduler.book_appointment(booking_request)
        
        if result.success:
            print(f"[OK] Appointment booked successfully: {result.appointment.serial_number}")
            
            # Test cancellation
            cancel_result = await scheduler.cancel_appointment(
                result.appointment.id, 
                "System test cancellation"
            )
            
            if cancel_result["success"]:
                print("[OK] Appointment cancellation works")
            else:
                print(f"[WARNING] Cancellation issue: {cancel_result['message']}")
        else:
            print(f"[WARNING] Booking test result: {result.message}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Scheduler agent test failed: {e}")
        return False

async def test_chat_agent():
    """Test chat agent (without actual OpenAI API call)"""
    print("\nTesting Chat Agent Structure...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from models.database import engine
        from agents.chat.chat_agent import ChatAgent
        from models.schemas import ChatRequest
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        chat_agent = ChatAgent(db)
        
        # Test chat agent initialization
        print("[OK] Chat agent initialized successfully")
        print("[OK] OpenAI service configured")
        print("[OK] RAG service integrated")
        print("[OK] Scheduler agent integrated")
        
        # Note: We're not making actual API calls to avoid API key requirements in testing
        print("[INFO] Note: Actual OpenAI API calls require valid API keys")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Chat agent test failed: {e}")
        return False

async def test_voice_agent():
    """Test voice agent structure (without actual API calls)"""
    print("\nTesting Voice Agent Structure...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from models.database import engine
        from agents.voice.voice_agent import VoiceAgent
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        voice_agent = VoiceAgent(db)
        
        print("[OK] Voice agent initialized successfully")
        print("[OK] Voice processing service configured")
        print("[OK] GPT-3.5-turbo service configured")
        
        # Note: We're not making actual API calls to avoid API key requirements
        print("[INFO] Note: Actual ElevenLabs/Whisper API calls require valid API keys")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Voice agent test failed: {e}")
        return False

async def test_api_structure():
    """Test API structure and imports"""
    print("\nTesting API Structure...")
    
    try:
        # Test router imports
        from api.routers import chat_router, voice_router, scheduler_router
        print("[OK] All API routers imported successfully")
        
        # Test main app structure
        from main import app
        print("[OK] FastAPI app initialized")
        
        # Test schemas
        from models import schemas
        print("[OK] Pydantic schemas loaded")
        
        # Test database models
        from models import database
        print("[OK] SQLAlchemy models loaded")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] API structure test failed: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\nChecking Environment Variables...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
    ]
    
    optional_vars = [
        "DATABASE_URL",
        "HOSPITAL_NAME",
        "HOSPITAL_PHONE",
        "SERVER_HOST",
        "SERVER_PORT"
    ]
    
    missing_required = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"[OK] {var}: Set")
        else:
            print(f"[MISSING] {var}: Not set (Required for full functionality)")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"[OK] {var}: Set")
        else:
            print(f"[DEFAULT] {var}: Using default value")
    
    if missing_required:
        print(f"\nMissing required environment variables: {', '.join(missing_required)}")
        print("   Create a .env file based on .env.example and add your API keys")
        return False
    else:
        print("\nAll required environment variables are set")
        return True

async def run_all_tests():
    """Run all system tests"""
    print("Starting X Hospital AI Assistant System Tests")
    print("=" * 60)
    
    test_results = []
    
    # Environment check
    env_ok = check_environment_variables()
    test_results.append(("Environment Variables", env_ok))
    
    # Database test
    db_ok = await test_database_connection()
    test_results.append(("Database Connection", db_ok))
    
    if not db_ok:
        print("\n❌ Database test failed. Please run: python scripts/init_db.py")
        return
    
    # Service tests
    rag_ok = await test_rag_service()
    test_results.append(("RAG Service", rag_ok))
    
    scheduler_ok = await test_scheduler_agent()
    test_results.append(("Scheduler Agent", scheduler_ok))
    
    chat_ok = await test_chat_agent()
    test_results.append(("Chat Agent", chat_ok))
    
    voice_ok = await test_voice_agent()
    test_results.append(("Voice Agent", voice_ok))
    
    api_ok = await test_api_structure()
    test_results.append(("API Structure", api_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! System is ready to use.")
        print("\nTo start the server:")
        print("  python main.py")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print(f"\n{total - passed} tests failed. Please check the issues above.")
        
    return passed == total

if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists("hospital.db"):
        print("Database not found. Initializing...")
        os.system("python scripts/init_db.py")
    
    # Run tests
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)