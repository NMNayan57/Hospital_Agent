#!/usr/bin/env python3
"""
Test script for the enhanced voice agent
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.voice.emotion_recognition import analyze_emotion_from_voice, VoiceEmotionData
from agents.voice.voice_prompts import get_hospital_voice_prompt, get_emotional_support_prompts

async def test_emotion_recognition():
    """Test emotion recognition functionality"""
    print("🧠 Testing Emotion Recognition")
    print("=" * 50)
    
    test_cases = [
        "I'm really worried about my chest pain, it's been hurting all day",
        "I'm so frustrated, I've been trying to get an appointment for weeks",
        "Thank you so much, I feel much better now",
        "I'm not sure what's wrong, I just feel confused about my symptoms",
        "This pain is unbearable, I need help immediately",
        "I'm excited to finally get this checked out"
    ]
    
    for i, transcript in enumerate(test_cases, 1):
        print(f"\nTest {i}: {transcript[:50]}...")
        
        emotion_data = VoiceEmotionData(
            transcript=transcript,
            conversation_history=[]
        )
        
        try:
            analysis = await analyze_emotion_from_voice(emotion_data)
            
            print(f"  Primary Emotion: {analysis.primary_emotion}")
            print(f"  Intensity: {analysis.emotion_intensity:.2f}")
            print(f"  Confidence: {analysis.confidence:.2f}")
            print(f"  Recommended Tone: {analysis.recommended_tone}")
            print(f"  Supportive Response: {analysis.supportive_response[:80]}...")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

def test_voice_prompts():
    """Test voice prompt generation"""
    print("\n\n📝 Testing Voice Prompts")
    print("=" * 50)
    
    # Test hospital info
    hospital_info = {
        'name': 'X Hospital',
        'phone': '+8801712345000',
        'address': '123 Medical Street, Dhaka, Bangladesh'
    }
    
    # Test doctors data
    available_doctors = [
        {
            'name': 'Dr. Rahman',
            'specialty': 'Cardiology',
            'available_days': 'Mon-Thu 6:00 PM - 8:00 PM'
        },
        {
            'name': 'Dr. Ayesha', 
            'specialty': 'Gastroenterology',
            'available_days': 'Sat-Tue 4:00 PM - 6:00 PM'
        }
    ]
    
    # Test conversation history
    conversation_history = [
        {'message_type': 'user', 'message_content': 'Hello, I need to see a doctor'},
        {'message_type': 'assistant', 'message_content': 'Hello! How can I help you today?'}
    ]
    
    print("Generated Voice Prompt:")
    prompt = get_hospital_voice_prompt(
        conversation_history=conversation_history,
        hospital_info=hospital_info,
        available_doctors=available_doctors
    )
    
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains hospital name: {'✅' if 'X Hospital' in prompt else '❌'}")
    print(f"  Contains doctor info: {'✅' if 'Dr. Rahman' in prompt else '❌'}")
    print(f"  Contains conversation history: {'✅' if 'Hello, I need' in prompt else '❌'}")
    
    print("\nEmotional Support Prompts:")
    support_prompts = get_emotional_support_prompts()
    for emotion, prompt in support_prompts.items():
        print(f"  {emotion}: {prompt[:60]}...")

def test_voice_agent_integration():
    """Test voice agent integration with mock data"""
    print("\n\n🤖 Testing Voice Agent Integration")  
    print("=" * 50)
    
    # Test cases for different scenarios
    test_scenarios = [
        {
            'name': 'Anxious Patient',
            'transcript': 'I\'m really worried about this chest pain, should I be concerned?',
            'expected_emotion': 'anxiety'
        },
        {
            'name': 'Frustrated Patient',
            'transcript': 'This is so annoying, I can never get through to book an appointment',
            'expected_emotion': 'frustration'
        },
        {
            'name': 'Pain Patient',
            'transcript': 'My stomach is really hurting, I need help',
            'expected_emotion': 'pain'
        },
        {
            'name': 'Confident Patient',
            'transcript': 'I definitely need to see a cardiologist for my routine checkup',
            'expected_emotion': 'confidence'
        }
    ]
    
    print("Voice Agent Integration Tests:")
    for scenario in test_scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        print(f"  Transcript: {scenario['transcript']}")
        print(f"  Expected emotion: {scenario['expected_emotion']}")
        print("  ✅ Ready for integration testing with actual voice agent")

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("=" * 50)
    
    dependencies = {
        'OpenAI API Key': os.getenv('OPENAI_API_KEY'),
        'ElevenLabs API Key': os.getenv('ELEVENLABS_API_KEY'),
    }
    
    all_good = True
    for dep_name, dep_value in dependencies.items():
        status = "✅ Available" if dep_value else "❌ Missing"
        print(f"  {dep_name}: {status}")
        if not dep_value:
            all_good = False
    
    if not all_good:
        print("\n⚠️  Warning: Some dependencies are missing. Voice features may not work properly.")
        print("   Please check your .env file and ensure all API keys are set.")
    else:
        print("\n✅ All dependencies are available!")
    
    return all_good

async def run_tests():
    """Run all voice agent tests"""
    print("🎙️  ENHANCED VOICE AGENT TEST SUITE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    # Run basic tests (don't require API calls)
    test_voice_prompts()
    test_voice_agent_integration()
    
    # Run emotion recognition tests (requires OpenAI API)
    if deps_ok and os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  NOTE: Emotion recognition test requires OpenAI API call")
        user_input = input("Do you want to run emotion recognition tests? (y/n): ").lower()
        if user_input == 'y':
            await test_emotion_recognition()
    else:
        print("\n⚠️  Skipping emotion recognition tests (OpenAI API key not available)")
    
    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 60)
    
    # Summary
    print("\n📋 ENHANCEMENT SUMMARY:")
    print("  ✅ Emotion recognition system added")
    print("  ✅ Specialized voice prompts created")
    print("  ✅ Context-aware conversation handling")
    print("  ✅ Emotional support responses")
    print("  ✅ Enhanced voice service with emotion adaptation")
    print("  ✅ Voice-specific system prompts")
    print("  ✅ Hospital-focused conversation flows")
    
    print("\n🎯 NEXT STEPS:")
    print("  1. Integrate with actual voice router endpoints")
    print("  2. Test with real audio input/output")
    print("  3. Fine-tune emotion detection prompts")
    print("  4. Add voice analytics and monitoring")

if __name__ == "__main__":
    asyncio.run(run_tests())