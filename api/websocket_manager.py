from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # phone_number -> session_id
        
    async def connect(self, websocket: WebSocket, phone_number: str):
        await websocket.accept()
        
        # Generate session ID if not exists
        if phone_number not in self.user_sessions:
            self.user_sessions[phone_number] = str(uuid.uuid4())
        
        session_id = self.user_sessions[phone_number]
        self.active_connections[session_id] = websocket
        
        # Send welcome message
        await self.send_personal_message({
            "type": "system",
            "message": "Connected to X Hospital AI Assistant",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        return session_id
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # Remove from user sessions
        phone_to_remove = None
        for phone, sid in self.user_sessions.items():
            if sid == session_id:
                phone_to_remove = phone
                break
        
        if phone_to_remove:
            del self.user_sessions[phone_to_remove]
    
    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except:
                # Connection is broken, remove it
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(session_id)
        
        # Clean up disconnected clients
        for session_id in disconnected:
            self.disconnect(session_id)
    
    def get_session_count(self) -> int:
        return len(self.active_connections)
    
    def get_user_session(self, phone_number: str) -> str:
        return self.user_sessions.get(phone_number)

# Global connection manager instance
manager = ConnectionManager()

# WebSocket endpoint handler
async def handle_websocket_chat(websocket: WebSocket, phone_number: str):
    """Handle WebSocket chat connections"""
    from sqlalchemy.orm import sessionmaker
    from models.database import engine
    from agents.chat.chat_agent import ChatAgent
    from models.schemas import ChatRequest
    
    session_id = await manager.connect(websocket, phone_number)
    
    try:
        # Initialize database session and chat agent
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        chat_agent = ChatAgent(db)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat_message":
                user_message = message_data.get("message", "")
                
                if user_message.strip():
                    # Send typing indicator
                    await manager.send_personal_message({
                        "type": "typing",
                        "message": "Assistant is typing...",
                        "timestamp": datetime.now().isoformat()
                    }, session_id)
                    
                    # Process message through chat agent
                    chat_request = ChatRequest(
                        message=user_message,
                        phone_number=phone_number,
                        session_id=session_id
                    )
                    
                    response = await chat_agent.process_chat_message(chat_request)
                    
                    # Send response back to client
                    await manager.send_personal_message({
                        "type": "chat_response",
                        "message": response.response,
                        "session_id": response.session_id,
                        "suggested_actions": response.suggested_actions,
                        "timestamp": datetime.now().isoformat()
                    }, session_id)
            
            elif message_data.get("type") == "ping":
                # Handle ping for keep-alive
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, session_id)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Client {phone_number} ({session_id}) disconnected")
    
    except Exception as e:
        print(f"WebSocket error for {phone_number}: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Connection error occurred. Please refresh the page.",
            "timestamp": datetime.now().isoformat()
        }, session_id)
    
    finally:
        if 'db' in locals():
            db.close()

# Real-time voice WebSocket handler
async def handle_websocket_voice(websocket: WebSocket, phone_number: str):
    """Handle WebSocket voice connections for real-time processing"""
    from sqlalchemy.orm import sessionmaker
    from models.database import engine
    from agents.voice.voice_agent import VoiceAgent
    from services.speechmatics.speechmatics_service import EnhancedVoiceService
    
    session_id = await manager.connect(websocket, phone_number)
    
    try:
        # Initialize services
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        voice_agent = VoiceAgent(db)
        enhanced_voice = EnhancedVoiceService()
        
        # Send voice capabilities
        capabilities = await enhanced_voice.get_available_methods()
        await manager.send_personal_message({
            "type": "voice_capabilities",
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }, session_id)
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "voice_input":
                # Handle real-time voice input
                audio_base64 = message_data.get("audio_data", "")
                is_greeting = message_data.get("is_greeting", False)
                
                # Handle greeting request
                if is_greeting:
                    greeting_text = f"Hello! Welcome to {voice_agent.hospital_info['name']}. I'm your AI assistant. How may I help you today?"
                    
                    try:
                        # Generate greeting audio (with fallback)
                        greeting_audio = voice_agent.voice_service.process_voice_output(greeting_text)
                    except Exception as e:
                        print(f"Warning: TTS failed for greeting: {e}")
                        greeting_audio = ""  # Send text-only response
                    
                    await manager.send_personal_message({
                        "type": "voice_response",
                        "text": greeting_text,
                        "audio_data": greeting_audio,
                        "session_id": session_id,
                        "is_greeting": True,
                        "timestamp": datetime.now().isoformat()
                    }, session_id)
                    
                elif audio_base64:
                    try:
                        # First, send transcription (if available)
                        transcribed_text = voice_agent.voice_service.process_voice_input(audio_base64)
                        
                        if transcribed_text:
                            await manager.send_personal_message({
                                "type": "transcription",
                                "text": transcribed_text,
                                "timestamp": datetime.now().isoformat()
                            }, session_id)
                        
                        # Process through voice agent
                        from models.schemas import VoiceRequest
                        voice_request = VoiceRequest(
                            audio_data=audio_base64,
                            phone_number=phone_number,
                            session_id=session_id
                        )
                        
                        response = await voice_agent.process_voice_call(voice_request)
                        
                        # Try to generate audio, but continue even if it fails
                        audio_response = ""
                        try:
                            if hasattr(response, 'audio_response'):
                                audio_response = response.audio_response or ""
                        except Exception as audio_error:
                            print(f"Audio generation failed: {audio_error}")
                            audio_response = ""  # Continue without audio
                        
                        # Always send text response
                        await manager.send_personal_message({
                            "type": "voice_response",
                            "text": response.response_text,
                            "audio_data": audio_response,
                            "session_id": response.session_id,
                            "emotion_context": getattr(response, 'emotion_context', None),
                            "timestamp": datetime.now().isoformat()
                        }, session_id)
                        
                    except Exception as e:
                        print(f"Voice processing error: {e}")
                        
                        # Send fallback response
                        fallback_text = "I heard you, but I'm having technical difficulties with my voice system. I can still help you via text. How can I assist you today?"
                        await manager.send_personal_message({
                            "type": "voice_response",
                            "text": fallback_text,
                            "audio_data": "",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }, session_id)
            
            elif message_data.get("type") == "start_real_time_voice":
                # Initialize real-time voice processing
                await manager.send_personal_message({
                    "type": "real_time_ready",
                    "message": "Real-time voice processing ready",
                    "timestamp": datetime.now().isoformat()
                }, session_id)
            
            elif message_data.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, session_id)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Voice client {phone_number} ({session_id}) disconnected")
    
    except Exception as e:
        print(f"Voice WebSocket error for {phone_number}: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Voice connection error occurred. Please refresh the page.",
            "timestamp": datetime.now().isoformat()
        }, session_id)
    
    finally:
        if 'db' in locals():
            db.close()

# WebSocket status endpoint
async def get_websocket_status():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": manager.get_session_count(),
        "total_sessions": len(manager.user_sessions),
        "timestamp": datetime.now().isoformat()
    }