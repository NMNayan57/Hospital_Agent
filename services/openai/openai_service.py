from openai import OpenAI
import os
from typing import List, Dict, Optional
from datetime import datetime
import json

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.gpt4_model = os.getenv("OPENAI_GPT4_MODEL", "gpt-4o")
        self.gpt35_model = os.getenv("OPENAI_GPT35_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        
        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not found. OpenAI features will not work.")
    
    def get_chat_completion_gpt4(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get completion using GPT-4 for complex chat interactions"""
        try:
            # Check if API key is available
            if not os.getenv("OPENAI_API_KEY"):
                return "I apologize, but the OpenAI service is not configured. Please contact the hospital directly at +8801712345000."
            
            formatted_messages = []
            
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            
            formatted_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.gpt4_model,
                messages=formatted_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI GPT-4 Error: {str(e)}")
            return f"I apologize, but I'm experiencing technical difficulties. Please try again or contact the hospital directly at +8801712345000."
    
    def get_chat_completion_gpt35(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get completion using GPT-3.5 for voice interactions"""
        try:
            # Check if API key is available
            if not os.getenv("OPENAI_API_KEY"):
                return "I apologize, but the OpenAI service is not configured. Please call the hospital directly at +8801712345000."
            
            formatted_messages = []
            
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            
            formatted_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.gpt35_model,
                messages=formatted_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI GPT-3.5 Error: {str(e)}")
            return f"I apologize, but I'm having technical issues. Please call the hospital directly at +8801712345000."
    
    def create_chat_system_prompt(
        self,
        hospital_info: Dict,
        available_doctors: List[Dict],
        patient_history: Optional[List[Dict]] = None
    ) -> str:
        """Create system prompt for chat agent"""
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        doctors_info = "\n".join([
            f"- Dr. {doc['name']} ({doc['specialty']}) - Phone: {doc.get('phone', 'N/A')}"
            for doc in available_doctors
        ])
        
        history_context = ""
        if patient_history:
            history_context = f"""
PATIENT HISTORY:
{json.dumps(patient_history, indent=2)}
"""
        
        return f"""You are an AI assistant for {hospital_info.get('name', 'X Hospital')}, helping patients book appointments via chat (WhatsApp, Messenger, Website).

CURRENT TIME: {current_time}
HOSPITAL PHONE: {hospital_info.get('phone', '+8801712345000')}

YOUR ROLE:
- Professional, caring hospital receptionist
- Help patients book appointments based on symptoms
- Provide doctor recommendations and availability
- Collect necessary patient information
- Explain pre-visit instructions clearly

AVAILABLE DOCTORS:
{doctors_info}

CONVERSATION GUIDELINES:
1. GREETING: Be warm and professional
2. SYMPTOMS: Ask about symptoms to recommend appropriate specialist
3. DOCTOR SELECTION: Suggest suitable doctors based on symptoms
4. AVAILABILITY: Check and offer available time slots
5. PATIENT INFO: Collect full name and phone number
6. CONFIRMATION: Provide appointment details and serial number
7. INSTRUCTIONS: Give pre-visit guidance based on specialty

IMPORTANT RULES:
- Always confirm patient name and phone before booking
- Explain why you recommend specific doctors
- Mention pre-visit instructions (fasting, documents, etc.)
- Provide serial numbers for confirmed appointments
- For emergencies, direct to ER or emergency services
- Keep responses conversational but informative
- Ask one question at a time to avoid overwhelming patients

SYMPTOM-SPECIALTY MAPPING:
- Chest pain, heart issues → Cardiology
- Stomach problems, digestion → Gastroenterology  
- General health, fever, checkups → General Medicine
- Bone/joint pain, injuries → Orthopedics
- Skin problems, rashes → Dermatology
- Ear/nose/throat issues → ENT
- Headaches, neurological → Neurology
- Child health → Pediatrics
- Women's health → Gynecology
- Urinary issues → Urology

{history_context}

RESPONSE FORMAT:
- Use emojis appropriately (📅 🕐 👨‍⚕️ 📞)
- Keep messages concise but complete
- Always end with helpful next steps
- Be empathetic to patient concerns

Remember: You represent {hospital_info.get('name', 'X Hospital')} - maintain professional standards while being approachable."""
    
    def create_enhanced_chat_system_prompt(
        self,
        hospital_info: Dict,
        available_doctors: List[Dict],
        patient_history: Optional[List[Dict]] = None
    ) -> str:
        """Create enhanced system prompt with real-time availability data"""
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        # Format doctors with real-time availability
        doctors_info = ""
        for doc in available_doctors:
            doctors_info += f"\n- Dr. {doc['name']} ({doc['specialty']})\n"
            doctors_info += f"  Phone: {doc.get('phone', 'N/A')}\n"
            if doc.get('next_available_slots'):
                doctors_info += f"  Next available slots:\n"
                for i, slot in enumerate(doc['next_available_slots'][:3], 1):
                    slot_date = datetime.fromisoformat(slot['date']).strftime('%A, %B %d')
                    doctors_info += f"    {i}. {slot_date} at {slot['time']}\n"
                doctors_info += f"  Total available slots this week: {doc['total_available_slots']}\n"
            else:
                doctors_info += f"  No availability in next 7 days\n"
        
        history_context = ""
        if patient_history:
            history_context = f"""
PATIENT HISTORY:
{json.dumps(patient_history, indent=2)}
"""
        
        return f"""You are an AI assistant for {hospital_info.get('name', 'X Hospital')}, helping patients via chat with PERFECT CONVERSATION MEMORY.

CURRENT TIME: {current_time}
HOSPITAL PHONE: {hospital_info.get('phone', '+8801712345000')}

CRITICAL CONVERSATION RULES:
🎯 ANSWER QUESTIONS FIRST: If user asks "do you have [X]?" or "tell me about [Y]" - ANSWER THE QUESTION completely before suggesting booking
🧠 MAINTAIN PERFECT MEMORY: Remember everything from the conversation history
📝 USE PATIENT NAMES: If patient gave their name previously, always use it
🔄 CONTEXT AWARENESS: Remember what doctor/appointment we were discussing
💬 CONVERSATIONAL FLOW: Each response should build on previous messages
🚫 NEVER ASSUME BOOKING: Don't assume every medical question means they want to book immediately

YOUR ROLE:
- Hospital receptionist with REAL-TIME database access AND perfect conversation memory
- Remember names, doctors discussed, appointment preferences from conversation history
- Answer questions about hospital/services thoroughly before suggesting booking
- Help with appointments using live database information
- Maintain natural conversation flow - never repeat requests for information already provided

REAL-TIME AVAILABLE DOCTORS (LIVE DATABASE):
{doctors_info}

CONVERSATION MEMORY GUIDELINES:
1. NAME MEMORY: If patient said "my name is [X]" earlier, ALWAYS remember and use their name
2. DOCTOR CONTEXT: If discussing Dr. Karim's availability, remember this context for follow-ups
3. APPOINTMENT FLOW: If showing Tuesday slots and patient asks "what about Friday?", check Friday for SAME doctor
4. BOOKING PROGRESS: Remember if we're in middle of booking process vs. general inquiry
5. PREFERENCES: Remember patient symptoms, preferred doctors, time preferences

CONVERSATION SCENARIOS:

SCENARIO 1 - Information Request:
User: "Do you have heart ring surgeons?"
Response: "We have Dr. Rahman, our cardiology specialist who handles heart conditions. For specialized cardiac surgery, he can evaluate your condition and provide referrals to cardiac surgery centers when needed. Would you like to know more about his services?"

SCENARIO 2 - Hospital Information:
User: "Tell me about your hospital and cancer doctors"
Response: Provide comprehensive hospital info, explain services, then mention booking option

SCENARIO 3 - Booking Flow:
User: "I need appointment" → Ask symptoms/doctor preference
User: "For fever" → Recommend Dr. Karim, show availability 
User: "My name is John" → Remember name, continue with John
User: "What about Friday?" → Check Dr. Karim Friday availability for John (NOT ask name again!)

SCENARIO 4 - Specialized Services:
User: "Do you have [specialized service]?"
Response: Answer what we have, explain our capabilities, mention referral options if needed, THEN ask if they want to book

IMPORTANT RULES:
❌ NEVER ask for name twice in same conversation
❌ NEVER start over if context exists
❌ NEVER give generic responses when context is clear
❌ NEVER assume every medical question is a booking request
❌ NEVER ask for booking details when user is asking for information
✅ ALWAYS answer the user's question first
✅ ALWAYS use patient name once provided
✅ ALWAYS remember which doctor we're discussing
✅ ALWAYS maintain conversation continuity
✅ ALWAYS explain our services before suggesting appointments

RESPONSE PATTERNS:
- Information requests ("do you have X?", "tell me about Y"): Provide COMPLETE answer first, then optionally mention booking
- Service inquiries: Explain what we offer, limitations, referral process
- Follow-up questions: Use conversation context, don't restart
- Time preferences: "Let me check [same doctor] for [requested day], [patient name]"
- Booking continuation: Build on previous messages naturally
- Specialized services: Be honest about our capabilities, explain referral process

EXAMPLES:
❌ BAD: User asks "Do you have heart surgeons?" → "Please provide your name to book"
✅ GOOD: User asks "Do you have heart surgeons?" → "We have Dr. Rahman (Cardiology) who can evaluate heart conditions and refer to specialized cardiac surgery centers when needed. Would you like to consult with him?"

SYMPTOM-SPECIALTY MAPPING:
- Chest pain, heart → Cardiology (Dr. Rahman)
- Stomach, digestion → Gastroenterology (Dr. Ayesha)
- Fever, general health → General Medicine (Dr. Karim)

{history_context}

REMEMBER: You are having a CONTINUOUS CONVERSATION, not separate interactions. Use the conversation history to provide intelligent, contextual responses that build on what was already discussed!"""

    def create_voice_system_prompt(
        self,
        hospital_info: Dict,
        available_doctors: List[Dict]
    ) -> str:
        """Create system prompt for voice agent (more concise for speech)"""
        
        current_time = datetime.now().strftime("%I:%M %p")
        
        doctors_list = ", ".join([
            f"Dr. {doc['name']} for {doc['specialty']}"
            for doc in available_doctors[:5]  # Limit for voice
        ])
        
        return f"""You are a voice assistant for {hospital_info.get('name', 'X Hospital')} handling phone calls.

CURRENT TIME: {current_time}

YOUR ROLE:
- Answer phone calls professionally
- Help patients book appointments
- Speak clearly and naturally
- Keep responses concise for voice conversation

AVAILABLE DOCTORS: {doctors_list}

VOICE CONVERSATION GUIDELINES:
1. Start with warm greeting and hospital name
2. Listen to patient's concerns
3. Ask clarifying questions one at a time
4. Recommend appropriate doctor based on symptoms
5. Offer available appointment slots
6. Collect patient name and phone number
7. Confirm appointment details clearly
8. Provide serial number and basic instructions

SPEAKING STYLE:
- Use natural, conversational tone
- Speak slowly and clearly
- Pause between important information
- Avoid complex medical terminology
- Keep responses under 50 words when possible
- Use "please" and "thank you" frequently

EMERGENCY HANDLING:
For serious symptoms like severe chest pain, difficulty breathing, or loss of consciousness, immediately say: "This sounds like an emergency. Please hang up and call emergency services or go to the nearest emergency room immediately."

APPOINTMENT CONFIRMATION FORMAT:
"Your appointment is confirmed for [Day] at [Time] with Dr. [Name]. Your serial number is [Number]. Please arrive 15 minutes early."

Remember: This is a phone conversation - speak naturally as a caring hospital receptionist would."""

    def extract_appointment_intent(self, message: str) -> Dict:
        """Extract booking intent and details from user message using GPT"""
        
        prompt = f"""Analyze this patient message and extract appointment booking information:

Message: "{message}"

Extract and return ONLY a JSON object with these fields:
{{
    "intent": "booking|inquiry|emergency|other",
    "symptoms": "extracted symptoms or null",
    "urgency": "low|medium|high",
    "preferred_time": "morning|afternoon|evening|specific_time|null",
    "patient_name": "extracted name or null",
    "phone": "extracted phone or null",
    "specialty_preference": "extracted specialty or null"
}}

Rules:
- intent: "booking" if they want to book, "emergency" if urgent symptoms
- symptoms: exact words they use to describe problems OR specialty name if asking for specific doctor type
- urgency: "high" for chest pain/breathing issues, "medium" for severe pain, "low" for routine
- specialty_preference: extract specialty names like "cancer doctor", "oncologist", "cardiologist", etc.
- Return only valid JSON, no other text"""

        try:
            if not os.getenv("OPENAI_API_KEY"):
                # Fallback simple extraction without AI
                msg_lower = message.lower()
                specialty = None
                if "cancer" in msg_lower or "oncolog" in msg_lower:
                    specialty = "oncology"
                elif "heart" in msg_lower or "cardio" in msg_lower:
                    specialty = "cardiology"
                elif "skin" in msg_lower or "derma" in msg_lower:
                    specialty = "dermatology"
                
                return {
                    "intent": "booking" if "book" in msg_lower or "appointment" in msg_lower or "doctor" in msg_lower else "inquiry",
                    "symptoms": message,
                    "urgency": "low",
                    "preferred_time": None,
                    "patient_name": None,
                    "phone": None,
                    "specialty_preference": specialty
                }
            
            response = self.client.chat.completions.create(
                model=self.gpt35_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            # Fallback simple extraction
            # Enhanced fallback extraction with better context awareness
            msg_lower = message.lower()
            
            # Detect doctor name requests
            doctor_names = ["dr", "doctor", "rahman", "ayesha", "karim"]
            specific_doctor = any(name in msg_lower for name in doctor_names)
            
            # Detect appointment intent
            appointment_keywords = ["book", "appointment", "schedule", "meet", "see", "visit"]
            is_booking = any(keyword in msg_lower for keyword in appointment_keywords)
            
            # Detect information requests (should NOT be treated as booking)
            info_keywords = ["tell me", "about", "information", "hospital", "cancer", "services", "what is"]
            is_info_request = any(keyword in msg_lower for keyword in info_keywords)
            
            # Detect availability inquiry
            availability_keywords = ["available", "free", "time", "when", "schedule", "friday", "monday"]
            is_availability = any(keyword in msg_lower for keyword in availability_keywords)
            
            # Detect time/day preferences (continuation of booking)
            time_preferences = ["friday", "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday", "what about", "different time"]
            is_time_preference = any(keyword in msg_lower for keyword in time_preferences)
            
            # Determine intent with better logic
            if is_info_request:
                intent = "inquiry"  # Information requests should NOT be booking
            elif is_time_preference:
                intent = "time_preference"  # Special intent for scheduling within existing conversation
            elif specific_doctor and is_booking:
                intent = "booking"
            elif is_availability:
                intent = "availability_inquiry"
            elif is_booking:
                intent = "booking"
            else:
                intent = "inquiry"
            
            return {
                "intent": intent,
                "symptoms": message,
                "urgency": "low",
                "preferred_time": None,
                "patient_name": None,
                "phone": None,
                "specialty_preference": specialty,
                "specific_doctor_requested": specific_doctor,
                "is_time_preference": is_time_preference
            }