from typing import Dict, List, Optional
from datetime import datetime, date, time
from sqlalchemy.orm import Session
import uuid
import json

from services.openai.openai_service import OpenAIService
from services.rag.rag_service import RAGService
from agents.scheduler.scheduler_agent import SchedulerAgent
from models.database import ConversationHistory, Doctor
from models.schemas import (
    ChatRequest, ChatResponse, AppointmentBookingRequest, 
    BookingChannel, MessageType, ConversationHistoryCreate
)

class ChatAgent:
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
        self.rag_service = RAGService(db)
        self.scheduler_agent = SchedulerAgent(db)
        self.hospital_info = {
            'name': 'X Hospital',
            'phone': '+8801712345000',
            'address': '123 Medical Street, Dhaka, Bangladesh',
            'services': 'General Medicine, Cardiology, Gastroenterology, Emergency Care',
            'cancer_info': 'We have experienced general physicians who can evaluate symptoms and provide referrals to specialized oncology centers when needed',
            'cardiac_surgery': 'Dr. Rahman (Cardiology) can evaluate heart conditions and coordinate with specialized cardiac surgery centers for procedures requiring heart surgery',
            'specialties': 'Our current specialists include Cardiology (Dr. Rahman), Gastroenterology (Dr. Ayesha), and General Medicine (Dr. Karim)',
            'referral_process': 'For specialized procedures beyond our current capabilities, our doctors provide expert evaluations and referrals to appropriate specialist centers'
        }
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Main chat processing function using GPT-4"""
        try:
            # Generate or use existing session ID
            session_id = request.session_id or str(uuid.uuid4())
            
            # Save user message to conversation history
            await self._save_conversation(
                phone=request.phone_number,
                message_type=MessageType.USER,
                content=request.message,
                session_id=session_id
            )
            
            # Get conversation context
            conversation_history = await self._get_conversation_context(
                request.phone_number, 
                session_id,
                limit=10
            )
            
            # Get patient history for context
            patient_history = self.rag_service.search_patient_history(request.phone_number, limit=5)
            
            message_lower = request.message.lower()
            
            # FIRST: Check for emergency keywords
            emergency_keywords = ["emergency", "urgent", "severe pain", "can't breathe", "chest pain severe"]
            if any(keyword in message_lower for keyword in emergency_keywords):
                response = await self._handle_emergency({})
            
            # SECOND: Check for CLEAR INFORMATION REQUESTS (highest priority)
            elif any(phrase in message_lower for phrase in [
                "tell me about", "information about", "do you have", "any", "available or not", 
                "about your hospital", "what services", "heart surgeon", "specialized", "cancer doctor"
            ]):
                print(f"DEBUG: Routing to general inquiry for: {request.message}")
                response = await self._handle_general_inquiry(
                    request, conversation_history, patient_history, session_id
                )
            
            # THIRD: Check for EXPLICIT booking requests
            elif any(phrase in message_lower for phrase in [
                "book appointment", "schedule appointment", "i want to book", "make appointment",
                "book me", "schedule me", "i need appointment now"
            ]):
                print(f"DEBUG: Routing to booking for: {request.message}")
                intent_data = self.openai_service.extract_appointment_intent(request.message)
                response = await self._handle_booking_intent(
                    request, intent_data, conversation_history, session_id
                )
            
            # FOURTH: Check if it's continuation of existing booking (name provided or time selection)
            elif ("my name is" in message_lower or 
                  ("let's make it" in message_lower and "at" in message_lower) or
                  ("friday" in message_lower and "at" in message_lower and ":" in message_lower)) and conversation_history:
                print(f"DEBUG: Routing to booking continuation for: {request.message}")
                intent_data = self.openai_service.extract_appointment_intent(request.message)
                response = await self._handle_booking_intent(
                    request, intent_data, conversation_history, session_id
                )
                
            # FIFTH: Check for serial number or appointment status queries
            elif any(phrase in message_lower for phrase in [
                "serial number", "appointment number", "booking number", "confirmation number",
                "do i know the", "what is my", "my appointment", "appointment details"
            ]):
                print(f"DEBUG: Routing to appointment query for: {request.message}")
                response = await self._handle_appointment_query(request, session_id)
            
            # DEFAULT: Route to general inquiry for everything else
            else:
                print(f"DEBUG: Default routing to general inquiry for: {request.message}")
                response = await self._handle_general_inquiry(
                    request, conversation_history, patient_history, session_id
                )
            
            # Save assistant response to conversation history
            await self._save_conversation(
                phone=request.phone_number,
                message_type=MessageType.ASSISTANT,
                content=response.response,
                session_id=session_id
            )
            
            return response
            
        except Exception as e:
            error_response = f"I apologize for the technical difficulty. Please call our hospital directly at {self.hospital_info['phone']} for immediate assistance. Error: {str(e)}"
            
            return ChatResponse(
                response=error_response,
                session_id=request.session_id or str(uuid.uuid4()),
                suggested_actions=["Call hospital directly", "Try again later"]
            )
    
    async def _handle_emergency(self, intent_data: Dict) -> ChatResponse:
        """Handle emergency situations"""
        emergency_response = """
EMERGENCY ALERT

Based on your symptoms, this may require immediate medical attention.

PLEASE:
1. Call emergency services immediately: 999
2. Or go to the nearest emergency room
3. If at X Hospital, go directly to Emergency Department

DO NOT wait for an appointment. Seek immediate care.

For non-emergency assistance, call our hospital: +8801712345000
        """.strip()
        
        return ChatResponse(
            response=emergency_response,
            session_id=str(uuid.uuid4()),
            suggested_actions=[
                "Call 999 for emergency",
                "Go to Emergency Room",
                "Contact hospital directly"
            ]
        )
    
    async def _handle_booking_intent(
        self, 
        request: ChatRequest,
        intent_data: Dict,
        conversation_history: List[Dict],
        session_id: str
    ) -> ChatResponse:
        """Handle appointment booking requests"""
        
        print(f"DEBUG: _handle_booking_intent called with message: {request.message}")
        print(f"DEBUG: intent_data: {intent_data}")
        
        # Check if we have enough information to book
        missing_info = []
        patient_name = intent_data.get('patient_name')
        symptoms = intent_data.get('symptoms') or self._extract_symptoms_from_history(conversation_history) or request.message
        specialty_preference = intent_data.get('specialty_preference')
        
        # Extract name from conversation history if not in current message
        if not patient_name:
            patient_name = await self._extract_name_from_history(conversation_history)
        
        # If still no name, try to get from existing patient record
        if not patient_name:
            from models.database import Patient
            existing_patient = self.db.query(Patient).filter(Patient.phone == request.phone_number).first()
            if existing_patient:
                patient_name = existing_patient.name
            
        # Extract specialty preference from conversation history if not in current message
        if not specialty_preference:
            specialty_preference = await self._extract_specialty_from_history(conversation_history)
            
        # Check if this is a continuation of an existing booking conversation
        is_continuation = await self._is_booking_continuation(conversation_history, request.message)
        
        print(f"DEBUG INFO: patient_name={patient_name}")
        print(f"DEBUG INFO: specialty_preference={specialty_preference}")
        print(f"DEBUG INFO: symptoms={symptoms}")
        print(f"DEBUG INFO: missing_info before check={missing_info}")
        
        if not patient_name:
            missing_info.append("your full name")
        
        # Only require symptoms if we don't have a specialty preference
        if not specialty_preference and (not symptoms or len(symptoms.strip()) < 5):
            missing_info.append("details about your symptoms or health concern")
            
        print(f"DEBUG INFO: missing_info after check={missing_info}")
        
        # If we have enough info, try to book
        if not missing_info:
            # Use specialty preference if provided, otherwise use symptoms
            symptoms_for_booking = specialty_preference if specialty_preference else symptoms
            
            print(f"DEBUG BOOKING: patient_name={patient_name}")
            print(f"DEBUG BOOKING: specialty_preference={specialty_preference}")
            print(f"DEBUG BOOKING: symptoms={symptoms}")
            print(f"DEBUG BOOKING: symptoms_for_booking={symptoms_for_booking}")
            
            booking_request = AppointmentBookingRequest(
                patient_name=patient_name,
                patient_phone=request.phone_number,
                symptoms=symptoms_for_booking,
                booking_channel=BookingChannel.CHAT
            )
            
            booking_result = await self.scheduler_agent.book_appointment(booking_request)
            
            if booking_result.success:
                return ChatResponse(
                    response=booking_result.message,
                    session_id=session_id,
                    suggested_actions=["View appointment details", "Set reminder", "Ask about preparation"]
                )
            else:
                # Booking failed, provide alternatives
                return ChatResponse(
                    response=booking_result.message,
                    session_id=session_id,
                    suggested_actions=["Try different time", "Call hospital", "Choose different doctor"]
                )
        
        # Check if this is about scheduling/time preference within existing booking flow
        if is_continuation and patient_name and ("friday" in request.message.lower() or "time" in request.message.lower() or "when" in request.message.lower()):
            return await self._handle_time_preference_in_booking(request, patient_name, conversation_history, session_id)
        
        # Missing information - ask for it using GPT-4
        return await self._ask_for_missing_info(
            missing_info, 
            conversation_history, 
            session_id,
            symptoms
        )
    
    async def _handle_general_inquiry(
        self,
        request: ChatRequest,
        conversation_history: List[Dict],
        patient_history: Optional[List[Dict]],
        session_id: str
    ) -> ChatResponse:
        """Handle general inquiries and provide real-time database information"""
        
        message_lower = request.message.lower()
        
        print(f"DEBUG: _handle_general_inquiry called with: {request.message}")
        
        # Extract patient name if provided
        patient_name = ""
        if "my name is" in message_lower:
            name_part = message_lower.split("my name is")[-1].strip()
            patient_name = name_part.split()[0].title() if name_part else ""
        
        greeting = f"Hello{' ' + patient_name if patient_name else ''}! "
        
        # Handle HOSPITAL/SERVICE INFORMATION requests FIRST
        if any(phrase in message_lower for phrase in [
            "heart surgeon", "cardiac surgeon", "heart surgery", "cardiac surgery", "heart ring",
            "cancer doctor", "oncologist", "cancer treatment",
            "tell me about hospital", "about your hospital", "services",
            "do you have", "any", "specialized", "available or not", "avialbe or not"
        ]):
            print(f"DEBUG: Detected service information request")
            
            if any(word in message_lower for word in ["heart", "cardiac", "surgeon", "surgery", "ring"]):
                response = greeting + f"""Thank you for asking about cardiac services at {self.hospital_info['name']}.

**Our Cardiac Care:**
We have **Dr. Rahman**, our experienced **Cardiologist** who can:
• Evaluate all types of heart conditions and symptoms
• Perform comprehensive cardiac examinations
• Provide treatment for various heart problems
• Coordinate with specialized cardiac surgery centers for procedures like heart ring surgery

For specialized cardiac surgeries, Dr. Rahman works closely with leading cardiac surgery centers and provides expert evaluations and referrals when surgical intervention is needed.

**Current Availability:** Dr. Rahman is available Monday-Thursday, 6:00-8:00 PM

Would you like me to check his current availability for a cardiac consultation?"""
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Book with Dr. Rahman", "Check availability", "Learn more"]
                )
            
            elif any(word in message_lower for word in ["cancer", "oncolog", "tumor"]):
                response = greeting + f"""Thank you for asking about cancer care at {self.hospital_info['name']}.

**Our Cancer Care Approach:**
Our experienced doctors provide:
• Initial cancer screenings and evaluations
• Comprehensive health assessments
• Expert coordination with specialized oncology centers
• Ongoing support throughout your care journey

Our **General Medicine** specialists work closely with leading cancer treatment facilities to ensure you receive appropriate specialized care when needed.

Would you like to schedule an initial consultation for evaluation?"""
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Schedule consultation", "Learn about process", "Ask questions"]
                )
            
            else:
                # General hospital information
                response = greeting + f"""Welcome to **{self.hospital_info['name']}**!

**Our Medical Team:**
• **Dr. Rahman** - Cardiology (Heart conditions, Mon-Thu 6-8 PM)
• **Dr. Ayesha** - Gastroenterology (Digestive issues, Sat-Tue 4-6 PM)  
• **Dr. Karim** - General Medicine (General health, Daily 10 AM-2 PM)

**Contact & Location:**
• **Phone:** {self.hospital_info['phone']}
• **Address:** {self.hospital_info['address']}

**Our Services:**
• Real-time appointment booking
• Specialist consultations
• Emergency care coordination
• Referrals to specialized centers

What specific service or doctor would you like to know more about?"""
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Ask about doctor", "Book appointment", "Emergency info"]
                )
        
        # Check if greeting
        elif any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return await self._handle_greeting_with_options(request, session_id)
        
        # Check if user is asking to reschedule or change appointment
        elif any(word in message_lower for word in ["change", "reschedule", "different time", "another time"]):
            return await self._handle_reschedule_request(request, session_id)
        
        # Check if user is asking for specific doctor or appointment
        elif "appointment" in message_lower and ("dr" in message_lower or "doctor" in message_lower):
            return await self._handle_specific_doctor_request(request, session_id)
        
        # Check if user is asking about doctor availability
        elif "available" in message_lower or "schedule" in message_lower or "time" in message_lower:
            return await self._handle_availability_inquiry(request, session_id)
        
        else:
            print(f"DEBUG: Falling back to GPT for: {request.message}")
            # Get real-time available doctors with current availability
            all_doctors = self.db.query(Doctor).all()
            available_doctors_with_slots = []
            
            for doctor in all_doctors:
                doctor_dict = self.rag_service._doctor_to_dict(doctor)
                # Get next 3 available slots for each doctor
                slots = self.rag_service.get_doctor_availability(doctor.id, days=7)
                doctor_dict['next_available_slots'] = slots[:3]
                doctor_dict['total_available_slots'] = len(slots)
                available_doctors_with_slots.append(doctor_dict)
            
            # Create enhanced system prompt with real-time data
            system_prompt = self.openai_service.create_enhanced_chat_system_prompt(
                hospital_info=self.hospital_info,
                available_doctors=available_doctors_with_slots,
                patient_history=patient_history
            )
        
        # Prepare conversation messages for GPT-4
        messages = []
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            messages.append({
                "role": "user" if msg['message_type'] == 'user' else "assistant",
                "content": msg['message_content']
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Get GPT-4 response with real-time context
        gpt_response = self.openai_service.get_chat_completion_gpt4(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        # Generate suggested actions based on response
        suggested_actions = await self._generate_suggested_actions(request.message, gpt_response)
        
        return ChatResponse(
            response=gpt_response,
            session_id=session_id,
            suggested_actions=suggested_actions
        )
    
    async def _ask_for_missing_info(
        self,
        missing_info: List[str],
        conversation_history: List[Dict],
        session_id: str,
        symptoms: str
    ) -> ChatResponse:
        """Ask for missing information needed for booking"""
        
        # Analyze symptoms to provide doctor suggestion while asking for missing info
        recommended_doctors = []
        if symptoms:
            recommended_doctors = self.rag_service.search_doctors_by_symptoms(symptoms)
        
        if len(missing_info) == 1 and "name" in missing_info[0]:
            if recommended_doctors:
                response = f"""Thank you for wanting to book an appointment with us! 

I can help you with that. Based on your symptoms, I recommend seeing our {recommended_doctors[0]['specialty'].lower()} specialist, Dr. {recommended_doctors[0]['name']}.

To complete your booking, please provide your full name."""
            else:
                response = """Thank you for wanting to book an appointment with us! 

I can help you with that. To complete your booking, please provide your full name."""
        
        elif len(missing_info) == 1 and "symptoms" in missing_info[0]:
            response = """I'd be happy to help you book an appointment! 

To recommend the right doctor for you, could you please describe your symptoms or health concerns in more detail?

For example:
- What specific symptoms are you experiencing?
- How long have you had these symptoms?
- Are you looking for a routine checkup?"""
        
        else:
            missing_list = " and ".join(missing_info)
            response = f"""I'd be happy to help you book an appointment! 

To complete your booking, I need {missing_list}.

Please provide this information and I'll find the best available appointment slot for you."""
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            suggested_actions=["Provide missing information", "Ask about doctors", "Call hospital"]
        )
    
    async def _save_conversation(
        self,
        phone: str,
        message_type: MessageType,
        content: str,
        session_id: str
    ):
        """Save conversation message to database"""
        try:
            conversation = ConversationHistory(
                patient_phone=phone,
                channel="chat",
                message_type=message_type.value,
                message_content=content,
                session_id=session_id
            )
            
            self.db.add(conversation)
            self.db.commit()
        except Exception as e:
            # Log error but don't fail the main process
            print(f"Error saving conversation: {e}")
    
    async def _get_conversation_context(
        self,
        phone_number: str,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history for context"""
        try:
            conversations = self.db.query(ConversationHistory).filter(
                ConversationHistory.patient_phone == phone_number,
                ConversationHistory.session_id == session_id,
                ConversationHistory.channel == "chat"
            ).order_by(ConversationHistory.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'message_type': conv.message_type,
                    'message_content': conv.message_content,
                    'timestamp': conv.timestamp.isoformat()
                }
                for conv in reversed(conversations)  # Reverse to get chronological order
            ]
        except Exception:
            return []
    
    async def _extract_name_from_history(self, conversation_history: List[Dict]) -> Optional[str]:
        """Extract patient name from conversation history"""
        for message in reversed(conversation_history):
            if message['message_type'] == 'user':
                content = message['message_content'].lower()
                # Simple name extraction patterns
                if "my name is" in content:
                    name_part = content.split("my name is")[-1].strip()
                    return name_part.split()[0:2] if name_part else None
                elif "i am" in content and len(content.split()) <= 5:
                    name_part = content.replace("i am", "").strip()
                    return name_part if len(name_part.split()) <= 3 else None
        return None
    
    async def _extract_specialty_from_history(self, conversation_history: List[Dict]) -> Optional[str]:
        """Extract specialty preference from conversation history"""
        for message in reversed(conversation_history):
            if message['message_type'] == 'user':
                content = message['message_content'].lower()
                
                # Check for specific doctor names first (higher priority)
                if "dr. rahman" in content or "rahman" in content:
                    return "chest pain consultation with cardiology specialist"  # Use symptoms that match Dr. Rahman
                elif "dr. ayesha" in content or "ayesha" in content:
                    return "stomach issues consultation with gastroenterology specialist"
                elif "dr. karim" in content or "karim" in content:
                    return "general health checkup with general medicine specialist"
                
                # Check for specialty keywords
                elif "cancer" in content or "oncolog" in content:
                    return "oncology"
                elif "heart" in content or "cardio" in content:
                    return "cardiology"
                elif "skin" in content or "derma" in content:
                    return "dermatology"
                elif "stomach" in content or "gastro" in content:
                    return "gastroenterology"
                elif "bone" in content or "orthoped" in content:
                    return "orthopedics"
                elif "general" in content or "checkup" in content:
                    return "general medicine"
        return None
    
    def _extract_symptoms_from_history(self, conversation_history: List[Dict]) -> Optional[str]:
        """Extract symptoms from conversation history"""
        for message in reversed(conversation_history):
            if message['message_type'] == 'user':
                content = message['message_content'].lower()
                # Look for actual medical symptoms, not booking-related messages
                if (any(symptom in content for symptom in ["fever", "cough", "pain", "ache", "sick", "problem", "headache", "stomach", "nausea", "chest", "throat"]) and 
                    not any(booking_word in content for booking_word in ["let's make", "appointment", "book", "schedule", "friday", "time", "at "])):
                    return message['message_content']
        return None
    
    async def _handle_specific_doctor_request(self, request: ChatRequest, session_id: str) -> ChatResponse:
        """Handle requests for specific doctors"""
        message = request.message.lower()
        
        # Extract doctor name from message
        doctors = self.db.query(Doctor).all()
        requested_doctor = None
        
        for doctor in doctors:
            if doctor.name.lower() in message:
                requested_doctor = doctor
                break
        
        if requested_doctor:
            # Get real-time availability for this doctor
            slots = self.rag_service.get_doctor_availability(requested_doctor.id, days=14)
            
            if slots:
                response = f"Great! Dr. {requested_doctor.name} ({requested_doctor.specialty}) is available. Here are the next available slots:\n\n"
                for i, slot in enumerate(slots[:5], 1):
                    slot_date = datetime.fromisoformat(slot['date']).strftime('%A, %B %d')
                    response += f"{i}. {slot_date} at {slot['time']}\n"
                response += "\nWould you like me to book one of these slots for you? Please provide your full name to proceed."
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Book appointment", "See more times", "Choose different doctor"]
                )
            else:
                response = f"I'm sorry, Dr. {requested_doctor.name} doesn't have any available slots in the next 14 days. Let me suggest some alternatives:\n\n"
                # Find doctors in same specialty
                similar_doctors = self.db.query(Doctor).filter(
                    Doctor.specialty == requested_doctor.specialty,
                    Doctor.id != requested_doctor.id
                ).all()
                
                for doctor in similar_doctors[:2]:
                    alt_slots = self.rag_service.get_doctor_availability(doctor.id, days=7)
                    if alt_slots:
                        response += f"• Dr. {doctor.name} ({doctor.specialty}) - Available {alt_slots[0]['date']} at {alt_slots[0]['time']}\n"
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Book alternative doctor", "Check later dates", "Call hospital"]
                )
        else:
            # Doctor not found
            available_doctors = [f"Dr. {doc.name} ({doc.specialty})" for doc in doctors]
            response = f"I couldn't find that doctor. Here are our available doctors:\n\n"
            for doctor_info in available_doctors:
                response += f"• {doctor_info}\n"
            response += "\nWould you like to see availability for any of these doctors?"
            
            return ChatResponse(
                response=response,
                session_id=session_id,
                suggested_actions=["Check doctor availability", "Book appointment", "Ask about symptoms"]
            )
    
    async def _handle_availability_inquiry(self, request: ChatRequest, session_id: str) -> ChatResponse:
        """Handle availability inquiries with real-time data"""
        message = request.message.lower()
        
        # Get all doctors with their current availability
        doctors = self.db.query(Doctor).all()
        availability_info = "📅 **Current Doctor Availability** (Real-time from database)\n\n"
        
        for doctor in doctors:
            slots = self.rag_service.get_doctor_availability(doctor.id, days=7)
            if slots:
                next_slot = slots[0]
                slot_date = datetime.fromisoformat(next_slot['date']).strftime('%A, %B %d')
                availability_info += f"👨‍⚕️ **Dr. {doctor.name}** ({doctor.specialty})\n"
                availability_info += f"   Next available: {slot_date} at {next_slot['time']}\n"
                availability_info += f"   Total slots this week: {len(slots)}\n\n"
            else:
                availability_info += f"👨‍⚕️ **Dr. {doctor.name}** ({doctor.specialty})\n"
                availability_info += f"   No availability in next 7 days\n\n"
        
        availability_info += "Would you like me to book an appointment with any of these doctors?"
        
        return ChatResponse(
            response=availability_info,
            session_id=session_id,
            suggested_actions=["Book with available doctor", "Check specific doctor", "Describe symptoms"]
        )
    
    async def _handle_greeting_with_options(self, request: ChatRequest, session_id: str) -> ChatResponse:
        """Handle greetings with personalized options based on real-time data"""
        
        # Get patient history if available
        patient_history = self.rag_service.search_patient_history(request.phone_number, limit=3)
        
        greeting = f"Hello! Welcome to {self.hospital_info['name']}! 👋\n\n"
        
        if patient_history:
            last_appointment = patient_history[0]
            greeting += f"I see you've visited us before (last appointment with Dr. {last_appointment['doctor_name']}). "
        
        greeting += "I'm here to help you with:\n\n"
        greeting += "Book an appointment - I'll find the perfect doctor and time for you\n"
        greeting += "Check doctor availability - See real-time availability\n"
        greeting += "Get recommendations - Tell me your symptoms for doctor suggestions\n"
        greeting += "Hospital information - Address, phone, services\n\n"
        
        # Add quick availability summary
        doctors = self.db.query(Doctor).all()
        available_today = []
        for doctor in doctors[:3]:  # Check first 3 doctors
            slots = self.rag_service.get_doctor_availability(doctor.id, days=1)
            if slots:
                available_today.append(f"Dr. {doctor.name} ({doctor.specialty})")
        
        if available_today:
            greeting += f"Available today: {', '.join(available_today)}\n\n"
        
        greeting += "How can I help you today?"
        
        return ChatResponse(
            response=greeting,
            session_id=session_id,
            suggested_actions=["Book appointment", "Check availability", "Ask about symptoms"]
        )
    
    async def _handle_reschedule_request(self, request: ChatRequest, session_id: str) -> ChatResponse:
        """Handle rescheduling requests with real-time availability"""
        message = request.message.lower()
        
        # Extract day preference if mentioned
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        requested_day = None
        for day in days:
            if day in message:
                requested_day = day
                break
        
        # Get patient's recent appointments to understand context
        patient_history = self.rag_service.search_patient_history(request.phone_number, limit=3)
        
        if patient_history:
            recent_apt = patient_history[0]
            doctor_name = recent_apt['doctor_name']
            current_date = recent_apt['date']
            current_time = recent_apt['time']
            
            # Extract doctor ID to check availability
            doctor = None
            if "dr. karim" in message or "karim" in message:
                doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%karim%")).first()
            elif "dr. rahman" in message or "rahman" in message:
                doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%rahman%")).first()
            elif "dr. ayesha" in message or "ayesha" in message:
                doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%ayesha%")).first()
            
            # If no specific doctor mentioned, find the doctor from recent appointment
            if not doctor:
                doctor = self.db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name.split()[-1]}%")).first()
            
            if doctor and requested_day:
                # Check availability for requested day
                from datetime import datetime, timedelta, date
                
                # Find next occurrence of requested day
                today = date.today()
                days_ahead = 0
                day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                target_weekday = day_names.index(requested_day)
                
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:  # If it's the same day, get next week
                    days_ahead = 7
                    
                target_date = today + timedelta(days=days_ahead)
                
                # Get availability for that specific day
                slots = self.rag_service.get_doctor_availability(doctor.id, target_date, days=1)
                
                if slots:
                    response = f"Great! Dr. {doctor.name} is available on {requested_day.title()}, {target_date.strftime('%B %d')}:\n\n"
                    for i, slot in enumerate(slots[:5], 1):
                        response += f"{i}. {slot['time']}\n"
                    response += f"\nYour current appointment: {current_date} at {current_time}\n"
                    response += f"Would you like me to reschedule to one of these {requested_day.title()} slots?"
                    
                    return ChatResponse(
                        response=response,
                        session_id=session_id,
                        suggested_actions=["Reschedule appointment", "Keep current time", "See more options"]
                    )
                else:
                    response = f"I'm sorry, Dr. {doctor.name} doesn't have availability on {requested_day.title()}, {target_date.strftime('%B %d')}.\n\n"
                    response += f"Your current appointment: {current_date} at {current_time}\n\n"
                    response += "Let me check other available days for Dr. " + doctor.name + ":"
                    
                    # Check next 7 days
                    week_slots = self.rag_service.get_doctor_availability(doctor.id, today, days=7)
                    if week_slots:
                        response += "\n\nAvailable this week:\n"
                        for slot in week_slots[:5]:
                            slot_date = datetime.fromisoformat(slot['date']).strftime('%A, %B %d')
                            response += f"• {slot_date} at {slot['time']}\n"
                    
                    return ChatResponse(
                        response=response,
                        session_id=session_id,
                        suggested_actions=["Choose different day", "Keep current appointment", "Call hospital"]
                    )
            
            else:
                return ChatResponse(
                    response=f"I can help you reschedule your appointment with Dr. {doctor_name} (currently {current_date} at {current_time}).\n\nWhich day would you prefer? I can check availability for any day of the week.",
                    session_id=session_id,
                    suggested_actions=["Check Friday", "Check Monday", "See all availability"]
                )
        else:
            return ChatResponse(
                response="I'd be happy to help you reschedule! However, I don't see any recent appointments in your history. Could you provide more details about which appointment you'd like to change?",
                session_id=session_id,
                suggested_actions=["Book new appointment", "Check availability", "Call hospital"]
            )
    
    async def _is_booking_continuation(self, conversation_history: List[Dict], current_message: str) -> bool:
        """Check if current message is continuation of booking conversation"""
        if not conversation_history:
            return False
        
        # Look for recent assistant messages about booking/appointments
        recent_messages = conversation_history[-4:]
        for msg in recent_messages:
            if msg['message_type'] == 'assistant':
                content = msg['message_content'].lower()
                if any(word in content for word in ["appointment", "booking", "available slots", "time works", "confirm"]):
                    return True
        return False
    
    async def _handle_time_preference_in_booking(self, request: ChatRequest, patient_name: str, conversation_history: List[Dict], session_id: str) -> ChatResponse:
        """Handle time preferences within ongoing booking conversation"""
        message = request.message.lower()
        
        # Check if user is specifying exact time slot (e.g., "Friday, September 05 at 10:00")
        if "at " in message and any(day in message for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            return await self._handle_specific_time_selection(request, patient_name, conversation_history, session_id)
        
        # Extract day preference
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        requested_day = None
        for day in days:
            if day in message:
                requested_day = day
                break
        
        # Find which doctor we were discussing from conversation history
        current_doctor = None
        for msg in reversed(conversation_history[-6:]):
            if msg['message_type'] == 'assistant':
                content = msg['message_content']
                if "dr. karim" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%karim%")).first()
                    break
                elif "dr. rahman" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%rahman%")).first()
                    break
                elif "dr. ayesha" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%ayesha%")).first()
                    break
        
        if current_doctor and requested_day:
            # Check availability for requested day
            from datetime import datetime, timedelta, date
            
            today = date.today()
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            target_weekday = day_names.index(requested_day)
            
            current_weekday = today.weekday()
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:  # If same day, get next occurrence
                days_ahead = 7
                
            target_date = today + timedelta(days=days_ahead)
            
            # Get availability for that day
            slots = self.rag_service.get_doctor_availability(current_doctor.id, target_date, days=1)
            
            if slots:
                response = f"Perfect, {patient_name}! Dr. {current_doctor.name} is available on {requested_day.title()}, {target_date.strftime('%B %d')}:\n\n"
                for i, slot in enumerate(slots[:4], 1):
                    response += f"{i}. {target_date.strftime('%A, %B %d')} at {slot['time']}\n"
                response += f"\nWhich time slot would you prefer? I'll book it for you right away!"
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Choose time slot", "See more times", "Book first available"]
                )
            else:
                response = f"I'm sorry {patient_name}, Dr. {current_doctor.name} doesn't have availability on {requested_day.title()}, {target_date.strftime('%B %d')}.\n\n"
                response += f"Let me check other days this week for Dr. {current_doctor.name}:\n\n"
                
                # Check next 7 days
                week_slots = self.rag_service.get_doctor_availability(current_doctor.id, today, days=7)
                if week_slots:
                    for slot in week_slots[:5]:
                        slot_date = datetime.fromisoformat(slot['date']).strftime('%A, %B %d')
                        response += f"• {slot_date} at {slot['time']}\n"
                    response += f"\nWould any of these work for you?"
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["Choose available time", "Try different doctor", "Call hospital"]
                )
        
        # Fallback if we can't determine context
        return ChatResponse(
            response=f"I'd be happy to help you with scheduling, {patient_name}! Could you clarify which doctor and day you're interested in?",
            session_id=session_id,
            suggested_actions=["Check Dr. Karim Friday", "See all availability", "Start over"]
        )
    
    async def _generate_suggested_actions(self, user_message: str, response: str) -> List[str]:
        """Generate contextual suggested actions"""
        message_lower = user_message.lower()
        response_lower = response.lower()
        
        actions = []
        
        if "appointment" in message_lower or "book" in message_lower:
            actions.extend(["Book appointment", "Check doctor availability", "View specialties"])
        elif "doctor" in message_lower:
            actions.extend(["See doctor list", "Check specialties", "Book appointment"])
        elif "time" in message_lower or "schedule" in message_lower:
            actions.extend(["View available times", "Book appointment", "Call hospital"])
        elif "symptoms" in response_lower or "recommend" in response_lower:
            actions.extend(["Book with recommended doctor", "Ask about preparation", "Get directions"])
        else:
            actions.extend(["Book appointment", "Ask about services", "Get contact info"])
        
        return actions[:3]  # Return top 3 actions
    
    async def _handle_specific_time_selection(self, request: ChatRequest, patient_name: str, conversation_history: List[Dict], session_id: str) -> ChatResponse:
        """Handle when user selects a specific time slot for booking"""
        message = request.message.lower()
        
        # Extract symptoms from conversation history (look for actual medical symptoms, not booking messages)
        symptoms = ""
        for msg in reversed(conversation_history):
            if msg['message_type'] == 'user':
                content = msg['message_content'].lower()
                # Only consider messages with actual symptoms, not booking/time-related messages
                if (any(symptom in content for symptom in ["fever", "cough", "pain", "ache", "sick", "problem", "headache", "stomach", "nausea"]) and 
                    not any(booking_word in content for booking_word in ["let's make", "appointment", "book", "schedule", "friday", "time"])):
                    symptoms = msg['message_content']
                    break
        
        if not symptoms:
            symptoms = "fever and general health concerns"  # Default for medical consultation
        
        # Find which doctor from conversation history
        current_doctor = None
        for msg in reversed(conversation_history[-6:]):
            if msg['message_type'] == 'assistant':
                content = msg['message_content']
                if "dr. karim" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%karim%")).first()
                    break
                elif "dr. rahman" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%rahman%")).first()
                    break
                elif "dr. ayesha" in content.lower():
                    current_doctor = self.db.query(Doctor).filter(Doctor.name.ilike("%ayesha%")).first()
                    break
        
        if not current_doctor:
            # Default to general medicine if no specific doctor mentioned
            current_doctor = self.db.query(Doctor).filter(Doctor.specialty.ilike("%general%")).first()
        
        if current_doctor:
            # Create booking request and book the appointment
            booking_request = AppointmentBookingRequest(
                patient_name=patient_name,
                patient_phone=request.phone_number,
                symptoms=symptoms,
                booking_channel=BookingChannel.CHAT
            )
            
            booking_result = await self.scheduler_agent.book_appointment(booking_request)
            
            if booking_result.success:
                response = f"Perfect! {booking_result.message}"
                
                return ChatResponse(
                    response=response,
                    session_id=session_id,
                    suggested_actions=["View appointment details", "Set reminder", "Ask about preparation"]
                )
            else:
                return ChatResponse(
                    response=f"I'm sorry, there was an issue booking your appointment: {booking_result.message}",
                    session_id=session_id,
                    suggested_actions=["Try different time", "Call hospital", "Choose different doctor"]
                )
        else:
            return ChatResponse(
                response="I'm sorry, I couldn't determine which doctor you'd like to see. Could you please specify?",
                session_id=session_id,
                suggested_actions=["Choose Dr. Karim", "Choose Dr. Rahman", "See all doctors"]
            )
    
    async def _handle_appointment_query(self, request: ChatRequest, session_id: str) -> ChatResponse:
        """Handle queries about appointment details, serial numbers, etc."""
        try:
            # Get patient's most recent appointments
            appointments = await self.scheduler_agent.get_patient_appointments(request.phone_number)
            
            if not appointments:
                return ChatResponse(
                    response="I don't see any appointments for your phone number. Would you like to book a new appointment?",
                    session_id=session_id,
                    suggested_actions=["Book new appointment", "Check availability", "Contact hospital"]
                )
            
            # Get the most recent appointment
            recent_appointment = appointments[0]
            
            response = f"""Your most recent appointment details:
            
📅 **Date:** {datetime.fromisoformat(recent_appointment['date']).strftime('%A, %B %d, %Y')}
⏰ **Time:** {recent_appointment['time']}
👨‍⚕️ **Doctor:** {recent_appointment['doctor_name']} ({recent_appointment['specialty']})
🔢 **Serial Number:** {recent_appointment['serial_number']}
📋 **Status:** {recent_appointment['status'].title()}
📞 **Hospital Phone:** +8801712345000

Please arrive 15 minutes early and bring a valid ID."""
            
            if len(appointments) > 1:
                response += f"\n\nYou have {len(appointments)} total appointments with us."
            
            return ChatResponse(
                response=response,
                session_id=session_id,
                suggested_actions=["View all appointments", "Reschedule appointment", "Cancel appointment"]
            )
            
        except Exception as e:
            return ChatResponse(
                response="I'm having trouble accessing your appointment information right now. Please call our hospital at +8801712345000 for assistance.",
                session_id=session_id,
                suggested_actions=["Call hospital", "Try again later", "Book new appointment"]
            )