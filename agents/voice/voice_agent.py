from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import json
import asyncio

from services.openai.openai_service import OpenAIService
from services.speechmatics.speechmatics_service import EnhancedVoiceService
from services.rag.rag_service import RAGService
from agents.scheduler.scheduler_agent import SchedulerAgent
from models.database import ConversationHistory, Doctor
from models.schemas import (
    VoiceRequest, VoiceResponse, AppointmentBookingRequest,
    BookingChannel, MessageType
)
from agents.voice.emotion_recognition import (
    analyze_emotion_from_voice, VoiceEmotionData, EmotionAnalysis
)
from agents.voice.voice_prompts import (
    get_hospital_voice_prompt, get_appointment_booking_prompt,
    get_emergency_detection_prompt, get_emotional_support_prompts,
    get_confirmation_prompts
)

class VoiceAgent:
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
        self.voice_service = EnhancedVoiceService()
        self.rag_service = RAGService(db)
        self.scheduler_agent = SchedulerAgent(db)
        self.hospital_info = {
            'name': 'X Hospital',
            'phone': '+8801712345000',
            'address': '123 Medical Street, Dhaka, Bangladesh'
        }
        
        # Voice-specific settings
        self.voice_id = None  # Will use default
        self.max_response_length = 150  # Words limit for voice responses
    
    async def process_voice_call(self, request: VoiceRequest) -> VoiceResponse:
        """Enhanced voice processing with emotion recognition and context awareness"""
        try:
            # Generate or use existing session ID
            session_id = request.session_id or str(uuid.uuid4())
            
            # Convert speech to text using 3-layer architecture
            import base64
            audio_bytes = base64.b64decode(request.audio_data)
            
            # Try Speechmatics first, fallback to Whisper
            try:
                transcribed_text = await self.voice_service.speech_to_text(
                    audio_bytes, 
                    method="speechmatics"
                )
            except Exception as stt_error:
                print(f"Speechmatics STT failed, falling back to Whisper: {stt_error}")
                try:
                    transcribed_text = await self.voice_service.speech_to_text(
                        audio_bytes, 
                        method="whisper"
                    )
                except Exception as whisper_error:
                    print(f"Whisper STT also failed: {whisper_error}")
                    transcribed_text = ""
            
            if not transcribed_text or len(transcribed_text.strip()) < 2:
                error_response = "I'm sorry, I couldn't hear you clearly. Could you please repeat that?"
                try:
                    error_audio = self.voice_service.text_to_speech(error_response, method="elevenlabs")
                    if not error_audio:
                        error_audio = ""  # Continue with text-only if TTS fails
                except Exception:
                    error_audio = ""  # Continue with text-only if TTS fails
                
                return VoiceResponse(
                    response_text=error_response,
                    audio_response=error_audio,
                    session_id=session_id
                )
            
            # Save user message to conversation history
            await self._save_conversation(
                phone=request.phone_number,
                message_type=MessageType.USER,
                content=transcribed_text,
                session_id=session_id
            )
            
            # Get conversation context
            conversation_history = await self._get_conversation_context(
                request.phone_number,
                session_id,
                limit=8
            )
            
            # Analyze emotion from voice input
            emotion_analysis = await self._analyze_patient_emotion(
                transcribed_text, conversation_history
            )
            
            # Check for emergency first
            if await self._detect_emergency(transcribed_text):
                response_text = await self._handle_voice_emergency()
            else:
                # Extract intent from voice input with emotion context
                intent_data = self.openai_service.extract_appointment_intent(transcribed_text)
                
                # Process based on intent with emotional awareness
                if intent_data.get('intent') == 'booking':
                    response_text = await self._handle_voice_booking_enhanced(
                        transcribed_text, intent_data, conversation_history, 
                        request.phone_number, session_id, emotion_analysis
                    )
                else:
                    response_text = await self._handle_voice_inquiry_enhanced(
                        transcribed_text, conversation_history, session_id, emotion_analysis
                    )
            
            # Keep response concise for voice
            response_text = self._limit_response_length(response_text)
            
            # Convert response to speech using 3-layer architecture with fallbacks
            try:
                response_audio = self.voice_service.text_to_speech(
                    response_text, 
                    method="elevenlabs",
                    voice_id=self._get_voice_settings_for_emotion(emotion_analysis)
                )
                
                # Convert to base64 for transport
                if response_audio:
                    import base64
                    response_audio = base64.b64encode(response_audio).decode('utf-8')
                else:
                    response_audio = ""  # Continue with text-only if TTS fails
                    
            except Exception as tts_error:
                print(f"TTS failed: {tts_error}")
                response_audio = ""  # Continue with text-only if TTS fails
            
            # Save assistant response to conversation history
            await self._save_conversation(
                phone=request.phone_number,
                message_type=MessageType.ASSISTANT,
                content=response_text,
                session_id=session_id
            )
            
            return VoiceResponse(
                response_text=response_text,
                audio_response=response_audio,
                session_id=session_id,
                emotion_context={
                    'detected_emotion': emotion_analysis.primary_emotion,
                    'intensity': emotion_analysis.emotion_intensity,
                    'recommended_tone': emotion_analysis.recommended_tone
                }
            )
            
        except Exception as e:
            print(f"Voice agent error: {e}")
            error_text = f"I apologize, but I'm experiencing technical difficulties. Please call our hospital directly at {self.hospital_info['phone']}."
            
            try:
                error_audio = self.voice_service.text_to_speech(error_text, method="elevenlabs")
                if error_audio:
                    import base64
                    error_audio = base64.b64encode(error_audio).decode('utf-8')
                else:
                    error_audio = ""
            except Exception:
                error_audio = ""
            
            return VoiceResponse(
                response_text=error_text,
                audio_response=error_audio,
                session_id=request.session_id or str(uuid.uuid4())
            )
    
    async def _handle_voice_emergency(self) -> str:
        """Handle emergency situations via voice"""
        return """This sounds like an emergency. Please hang up immediately and call emergency services at 999, or go to the nearest emergency room. If you are at X Hospital, go directly to our Emergency Department. Do not wait."""
    
    async def _handle_voice_booking(
        self,
        transcribed_text: str,
        intent_data: Dict,
        conversation_history: List[Dict],
        phone_number: str,
        session_id: str
    ) -> str:
        """Handle appointment booking via voice"""
        
        # Extract information we have
        patient_name = intent_data.get('patient_name')
        symptoms = intent_data.get('symptoms') or transcribed_text
        
        # Extract name from conversation if not in current message
        if not patient_name:
            patient_name = await self._extract_name_from_voice_history(conversation_history)
        
        # Check what information we're missing
        if not patient_name:
            return "To book your appointment, I need your full name. Please tell me your name."
        
        if not symptoms or len(symptoms.strip()) < 5:
            return "Could you please describe your symptoms or what you need to see the doctor for?"
        
        # We have enough information, try to book
        try:
            booking_request = AppointmentBookingRequest(
                patient_name=patient_name,
                patient_phone=phone_number,
                symptoms=symptoms,
                booking_channel=BookingChannel.VOICE
            )
            
            booking_result = await self.scheduler_agent.book_appointment(booking_request)
            
            if booking_result.success:
                # Parse appointment details for voice response
                appointment = booking_result.appointment
                doctor = self.db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
                
                return f"""Great! Your appointment is confirmed. 
Date: {appointment.appointment_date.strftime('%A, %B %d')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Doctor: Dr. {doctor.name}
Serial number: {appointment.serial_number}

Please arrive 15 minutes early and bring your ID. Is there anything else I can help you with?"""
            else:
                # Booking failed - provide concise alternative
                if booking_result.available_slots:
                    first_slot = booking_result.available_slots[0]
                    return f"""I don't have immediate availability, but I can offer you {first_slot['date']} at {first_slot['time']} with Dr. {first_slot['doctor_name']}. Would this work for you?"""
                else:
                    return "I'm having trouble finding availability right now. Please call our booking line at +8801712345000 for assistance."
        
        except Exception as e:
            return "I'm having trouble processing your booking right now. Please call our hospital at +8801712345000."
    
    async def _handle_voice_inquiry(
        self,
        transcribed_text: str,
        conversation_history: List[Dict],
        session_id: str
    ) -> str:
        """Handle general inquiries via voice"""
        
        # Check if this is a greeting or general inquiry
        text_lower = transcribed_text.lower()
        
        if any(greeting in text_lower for greeting in ["hello", "hi", "good morning", "good afternoon"]):
            return f"Hello! Welcome to {self.hospital_info['name']}. How can I help you today?"
        
        # Get available doctors for context
        all_doctors = self.db.query(Doctor).all()
        available_doctors = [self.rag_service._doctor_to_dict(doc) for doc in all_doctors[:8]]  # Limit for voice
        
        # Create voice-optimized system prompt
        system_prompt = self.openai_service.create_voice_system_prompt(
            hospital_info=self.hospital_info,
            available_doctors=available_doctors
        )
        
        # Prepare conversation context (less history for voice)
        messages = []
        for msg in conversation_history[-4:]:  # Last 4 messages only
            messages.append({
                "role": "user" if msg['message_type'] == 'user' else "assistant",
                "content": msg['message_content']
            })
        
        messages.append({
            "role": "user",
            "content": transcribed_text
        })
        
        # Get GPT-3.5-turbo response (faster and more concise)
        response = self.openai_service.get_chat_completion_gpt35(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=200  # Limit for voice responses
        )
        
        return response
    
    def _limit_response_length(self, text: str) -> str:
        """Limit response length for voice output"""
        words = text.split()
        if len(words) > self.max_response_length:
            # Try to find a natural breaking point
            truncated = " ".join(words[:self.max_response_length])
            
            # Find last sentence ending
            last_period = truncated.rfind('.')
            last_question = truncated.rfind('?')
            last_exclamation = truncated.rfind('!')
            
            last_sentence_end = max(last_period, last_question, last_exclamation)
            
            if last_sentence_end > len(truncated) * 0.7:  # If we can keep 70%+ of the text
                return truncated[:last_sentence_end + 1]
            else:
                return truncated + "..."
        
        return text
    
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
                channel="voice",
                message_type=message_type.value,
                message_content=content,
                session_id=session_id
            )
            
            self.db.add(conversation)
            self.db.commit()
        except Exception as e:
            print(f"Error saving voice conversation: {e}")
    
    async def _get_conversation_context(
        self,
        phone_number: str,
        session_id: str,
        limit: int = 8
    ) -> List[Dict]:
        """Get recent conversation history for context"""
        try:
            conversations = self.db.query(ConversationHistory).filter(
                ConversationHistory.patient_phone == phone_number,
                ConversationHistory.session_id == session_id,
                ConversationHistory.channel == "voice"
            ).order_by(ConversationHistory.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'message_type': conv.message_type,
                    'message_content': conv.message_content,
                    'timestamp': conv.timestamp.isoformat()
                }
                for conv in reversed(conversations)
            ]
        except Exception:
            return []
    
    async def _extract_name_from_voice_history(self, conversation_history: List[Dict]) -> Optional[str]:
        """Extract patient name from voice conversation history"""
        for message in reversed(conversation_history):
            if message['message_type'] == 'user':
                content = message['message_content'].lower()
                
                # Voice-specific patterns
                if "my name is" in content:
                    name_part = content.split("my name is")[-1].strip()
                    # Extract first 2 words as name
                    name_words = name_part.split()[:2]
                    return " ".join(name_words) if name_words else None
                elif "i am" in content and len(content.split()) <= 6:
                    name_part = content.replace("i am", "").strip()
                    name_words = name_part.split()[:2]
                    return " ".join(name_words) if name_words and len(name_part) < 30 else None
                elif "this is" in content:
                    name_part = content.split("this is")[-1].strip()
                    name_words = name_part.split()[:2]
                    return " ".join(name_words) if name_words else None
        
        return None
    
    async def handle_call_transfer(self, session_id: str) -> str:
        """Handle requests to transfer to human operator"""
        transfer_message = f"""I'll transfer you to our human operator now. Please hold the line. 

If the call drops, you can call us directly at {self.hospital_info['phone']}. 

Thank you for calling {self.hospital_info['name']}."""
        
        # Here you would implement actual call transfer logic
        # For now, we provide instructions
        
        return transfer_message
    
    async def _analyze_patient_emotion(self, transcript: str, conversation_history: List[Dict]) -> EmotionAnalysis:
        """Analyze patient's emotional state from voice transcript"""
        try:
            emotion_data = VoiceEmotionData(
                transcript=transcript,
                conversation_history=conversation_history
            )
            
            emotion_analysis = await analyze_emotion_from_voice(emotion_data)
            return emotion_analysis
            
        except Exception as e:
            print(f"Error analyzing emotion: {e}")
            # Return neutral emotion as fallback
            from agents.voice.emotion_recognition import EmotionAnalysis
            return EmotionAnalysis(
                primary_emotion='neutral',
                emotion_intensity=0.5,
                confidence=0.3,
                emotional_indicators=['Error in analysis'],
                supportive_response="I'm here to help you with your healthcare needs.",
                recommended_tone='professional'
            )
    
    async def _detect_emergency(self, transcript: str) -> bool:
        """Detect emergency situations from transcript"""
        emergency_keywords = [
            'emergency', 'urgent', 'chest pain', 'heart attack', 'can\'t breathe',
            'bleeding', 'unconscious', 'stroke', 'choking', 'overdose',
            'severe pain', 'dying', 'help me', 'ambulance'
        ]
        
        text_lower = transcript.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)
    
    async def _handle_voice_booking_enhanced(
        self,
        transcribed_text: str,
        intent_data: Dict,
        conversation_history: List[Dict],
        phone_number: str,
        session_id: str,
        emotion_analysis: EmotionAnalysis
    ) -> str:
        """Enhanced booking handler with emotional awareness"""
        
        # Add emotional support if needed
        emotional_support = ""
        if emotion_analysis.emotion_intensity > 0.6:
            support_prompts = get_emotional_support_prompts()
            emotional_support = support_prompts.get(emotion_analysis.primary_emotion, "") + " "
        
        # Extract information we have
        patient_name = intent_data.get('patient_name')
        symptoms = intent_data.get('symptoms') or transcribed_text
        
        # Extract name from conversation if not in current message
        if not patient_name:
            patient_name = await self._extract_name_from_voice_history(conversation_history)
        
        # Check what information we're missing
        if not patient_name:
            return f"{emotional_support}To book your appointment, I'll need your full name. Could you please tell me your name?"
        
        if not symptoms or len(symptoms.strip()) < 5:
            return f"{emotional_support}Could you please describe your symptoms or what you need to see the doctor for?"
        
        # We have enough information, try to book
        try:
            booking_request = AppointmentBookingRequest(
                patient_name=patient_name,
                patient_phone=phone_number,
                symptoms=symptoms,
                booking_channel=BookingChannel.VOICE
            )
            
            booking_result = await self.scheduler_agent.book_appointment(booking_request)
            
            if booking_result.success:
                # Parse appointment details for voice response
                appointment = booking_result.appointment
                doctor = self.db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
                
                confirmation_response = f"""Excellent! Your appointment is confirmed. 
                
Date: {appointment.appointment_date.strftime('%A, %B %d')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Doctor: Dr. {doctor.name}
Serial number: {appointment.serial_number}
                
Please arrive 15 minutes early and bring your ID. Is there anything else I can help you with?"""
                
                return confirmation_response
                
            else:
                # Booking failed - provide empathetic alternative
                if booking_result.available_slots:
                    first_slot = booking_result.available_slots[0]
                    return f"{emotional_support}I don't have immediate availability, but I can offer you {first_slot['date']} at {first_slot['time']} with Dr. {first_slot['doctor_name']}. Would this work for you?"
                else:
                    return f"{emotional_support}I'm having trouble finding availability right now. Let me transfer you to our booking specialist who can help you better. Please hold on."
        
        except Exception as e:
            return f"{emotional_support}I'm experiencing technical difficulties right now. Please call our hospital directly at {self.hospital_info['phone']} for immediate assistance."
    
    async def _handle_voice_inquiry_enhanced(
        self,
        transcribed_text: str,
        conversation_history: List[Dict],
        session_id: str,
        emotion_analysis: EmotionAnalysis
    ) -> str:
        """Enhanced inquiry handler with emotional awareness"""
        
        # Check if this is a greeting or general inquiry
        text_lower = transcribed_text.lower()
        
        if any(greeting in text_lower for greeting in ["hello", "hi", "good morning", "good afternoon"]):
            return f"Hello! Welcome to {self.hospital_info['name']}. How can I help you today?"
        
        # Get available doctors for context
        all_doctors = self.db.query(Doctor).all()
        available_doctors = [self.rag_service._doctor_to_dict(doc) for doc in all_doctors[:5]]  # Limit for voice
        
        # Create emotion-aware system prompt
        system_prompt = get_hospital_voice_prompt(
            conversation_history=conversation_history,
            hospital_info=self.hospital_info,
            available_doctors=available_doctors
        )
        
        # Add emotion context to system prompt
        if emotion_analysis.emotion_intensity > 0.5:
            emotion_context = f"""
            
EMOTION CONTEXT:
- Patient's current emotion: {emotion_analysis.primary_emotion}
- Intensity level: {int(emotion_analysis.emotion_intensity * 100)}%
- Recommended tone: {emotion_analysis.recommended_tone}
- Supportive response: {emotion_analysis.supportive_response}
            
Please adapt your response tone and approach based on the patient's emotional state."""
            system_prompt += emotion_context
        
        # Prepare conversation context
        messages = []
        for msg in conversation_history[-4:]:  # Last 4 messages only
            messages.append({
                "role": "user" if msg['message_type'] == 'user' else "assistant",
                "content": msg['message_content']
            })
        
        messages.append({
            "role": "user",
            "content": transcribed_text
        })
        
        # Get enhanced GPT response
        response = self.openai_service.get_chat_completion_gpt35(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7,  # Slightly higher for more natural responses
            max_tokens=200
        )
        
        return response
    
    def _get_voice_settings_for_emotion(self, emotion_analysis: EmotionAnalysis) -> Optional[str]:
        """Get appropriate voice settings based on detected emotion"""
        # You can customize voice settings based on emotion here
        # For now, return default voice
        return self.voice_id
    
    async def handle_call_end(self, session_id: str) -> str:
        """Handle call ending gracefully"""
        return f"""Thank you for calling {self.hospital_info['name']}. If you need further assistance, please call us at {self.hospital_info['phone']}. Have a great day and feel better soon!"""