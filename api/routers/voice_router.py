from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import base64
import io

from models.database import get_db
from models.schemas import VoiceRequest, VoiceResponse
from agents.voice.voice_agent import VoiceAgent
from services.elevenlabs.voice_service import VoiceProcessingService

router = APIRouter()

@router.post("/call", response_model=VoiceResponse)
async def process_voice_call(
    request: VoiceRequest,
    db: Session = Depends(get_db)
):
    """Process incoming voice call and return audio response"""
    try:
        voice_agent = VoiceAgent(db)
        response = await voice_agent.process_voice_call(request)
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice call: {str(e)}"
        )

@router.post("/upload-audio", response_model=VoiceResponse)
async def upload_audio_file(
    phone_number: str,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload audio file and get voice response"""
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Create voice request
        voice_request = VoiceRequest(
            audio_data=audio_base64,
            phone_number=phone_number,
            session_id=session_id
        )
        
        # Process through voice agent
        voice_agent = VoiceAgent(db)
        response = await voice_agent.process_voice_call(voice_request)
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing uploaded audio: {str(e)}"
        )

@router.post("/text-to-speech")
async def text_to_speech(
    text: str,
    voice_id: Optional[str] = None
):
    """Convert text to speech (for testing purposes)"""
    try:
        voice_service = VoiceProcessingService()
        audio_base64 = voice_service.process_voice_output(text, voice_id)
        
        return {
            "text": text,
            "audio_base64": audio_base64,
            "voice_id": voice_id or "default"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech error: {str(e)}"
        )

@router.post("/speech-to-text")
async def speech_to_text(
    audio_file: UploadFile = File(...)
):
    """Convert speech to text (for testing purposes)"""
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Process through voice service
        voice_service = VoiceProcessingService()
        transcribed_text = voice_service.process_voice_input(audio_base64)
        
        return {
            "transcribed_text": transcribed_text,
            "audio_filename": audio_file.filename,
            "audio_content_type": audio_file.content_type
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text error: {str(e)}"
        )

@router.get("/voices")
async def get_available_voices():
    """Get list of available voices"""
    try:
        voice_service = VoiceProcessingService()
        voice_options = voice_service.get_voice_options()
        return voice_options
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving voices: {str(e)}"
        )

@router.get("/call-history/{phone_number}")
async def get_call_history(
    phone_number: str,
    session_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get voice call conversation history"""
    try:
        from models.database import ConversationHistory
        
        query = db.query(ConversationHistory).filter(
            ConversationHistory.patient_phone == phone_number,
            ConversationHistory.channel == "voice"
        )
        
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        
        conversations = query.order_by(
            ConversationHistory.timestamp.desc()
        ).limit(limit).all()
        
        return {
            "phone_number": phone_number,
            "session_id": session_id,
            "conversations": [
                {
                    "id": conv.id,
                    "message_type": conv.message_type,
                    "message_content": conv.message_content,
                    "timestamp": conv.timestamp.isoformat(),
                    "session_id": conv.session_id
                }
                for conv in reversed(conversations)
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving call history: {str(e)}"
        )

@router.post("/call-transfer")
async def initiate_call_transfer(
    session_id: str,
    transfer_reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Initiate call transfer to human operator"""
    try:
        voice_agent = VoiceAgent(db)
        transfer_message = await voice_agent.handle_call_transfer(session_id)
        
        # Convert message to speech
        voice_service = VoiceProcessingService()
        transfer_audio = voice_service.process_voice_output(transfer_message)
        
        return {
            "status": "transfer_initiated",
            "message": transfer_message,
            "audio_response": transfer_audio,
            "session_id": session_id,
            "transfer_reason": transfer_reason
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Call transfer error: {str(e)}"
        )

@router.post("/end-call")
async def end_call(
    session_id: str,
    db: Session = Depends(get_db)
):
    """End call gracefully"""
    try:
        voice_agent = VoiceAgent(db)
        end_message = await voice_agent.handle_call_end(session_id)
        
        # Convert message to speech
        voice_service = VoiceProcessingService()
        end_audio = voice_service.process_voice_output(end_message)
        
        return {
            "status": "call_ended",
            "message": end_message,
            "audio_response": end_audio,
            "session_id": session_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Call end error: {str(e)}"
        )

@router.get("/active-calls")
async def get_active_calls(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of active voice calls"""
    try:
        from models.database import ConversationHistory
        from datetime import datetime, timedelta
        
        # Calls active in last 2 hours
        cutoff_time = datetime.now() - timedelta(hours=2)
        
        active_calls = db.query(
            ConversationHistory.patient_phone,
            ConversationHistory.session_id,
            ConversationHistory.timestamp.label("last_activity")
        ).filter(
            ConversationHistory.channel == "voice",
            ConversationHistory.timestamp > cutoff_time
        ).distinct(
            ConversationHistory.session_id
        ).order_by(
            ConversationHistory.timestamp.desc()
        ).limit(limit).all()
        
        return {
            "active_calls": [
                {
                    "phone_number": call.patient_phone,
                    "session_id": call.session_id,
                    "last_activity": call.last_activity.isoformat()
                }
                for call in active_calls
            ],
            "count": len(active_calls)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active calls: {str(e)}"
        )

@router.get("/health")
async def voice_health_check():
    """Health check endpoint for voice service"""
    try:
        voice_service = VoiceProcessingService()
        voice_options = voice_service.get_voice_options()
        
        return {
            "service": "voice_agent",
            "status": "healthy",
            "tts_available": voice_options["tts_available"],
            "stt_available": voice_options["stt_available"],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "service": "voice_agent",
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }