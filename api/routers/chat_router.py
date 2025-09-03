from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.schemas import ChatRequest, ChatResponse, ConversationHistoryCreate
from agents.chat.chat_agent import ChatAgent

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def process_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Process incoming chat message and return response"""
    try:
        chat_agent = ChatAgent(db)
        response = await chat_agent.process_chat_message(request)
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )

@router.get("/history/{phone_number}")
async def get_chat_history(
    phone_number: str,
    session_id: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get chat conversation history for a phone number"""
    try:
        from models.database import ConversationHistory
        
        query = db.query(ConversationHistory).filter(
            ConversationHistory.patient_phone == phone_number,
            ConversationHistory.channel == "chat"
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
            detail=f"Error retrieving chat history: {str(e)}"
        )

@router.delete("/history/{phone_number}")
async def clear_chat_history(
    phone_number: str,
    session_id: str = None,
    db: Session = Depends(get_db)
):
    """Clear chat history for a phone number"""
    try:
        from models.database import ConversationHistory
        
        query = db.query(ConversationHistory).filter(
            ConversationHistory.patient_phone == phone_number,
            ConversationHistory.channel == "chat"
        )
        
        if session_id:
            query = query.filter(ConversationHistory.session_id == session_id)
        
        deleted_count = query.delete()
        db.commit()
        
        return {
            "message": f"Deleted {deleted_count} chat messages",
            "phone_number": phone_number,
            "session_id": session_id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing chat history: {str(e)}"
        )

@router.get("/active-sessions")
async def get_active_chat_sessions(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of active chat sessions"""
    try:
        from models.database import ConversationHistory
        from datetime import datetime, timedelta
        
        # Sessions active in last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        active_sessions = db.query(
            ConversationHistory.patient_phone,
            ConversationHistory.session_id,
            ConversationHistory.timestamp.label("last_activity")
        ).filter(
            ConversationHistory.channel == "chat",
            ConversationHistory.timestamp > cutoff_time
        ).distinct(
            ConversationHistory.session_id
        ).order_by(
            ConversationHistory.timestamp.desc()
        ).limit(limit).all()
        
        return {
            "active_sessions": [
                {
                    "phone_number": session.patient_phone,
                    "session_id": session.session_id,
                    "last_activity": session.last_activity.isoformat()
                }
                for session in active_sessions
            ],
            "count": len(active_sessions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active sessions: {str(e)}"
        )

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle WhatsApp webhook messages"""
    try:
        # Extract WhatsApp message data
        if "messages" in request:
            for message in request["messages"]:
                phone_number = message.get("from", "")
                message_text = message.get("text", {}).get("body", "")
                
                if phone_number and message_text:
                    # Process message through chat agent
                    chat_request = ChatRequest(
                        message=message_text,
                        phone_number=phone_number
                    )
                    
                    chat_agent = ChatAgent(db)
                    response = await chat_agent.process_chat_message(chat_request)
                    
                    # Here you would send the response back via WhatsApp API
                    # For now, we'll just return it
                    return {
                        "status": "processed",
                        "response": response.response,
                        "session_id": response.session_id
                    }
        
        return {"status": "no_messages_to_process"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WhatsApp webhook error: {str(e)}"
        )

@router.get("/health")
async def chat_health_check():
    """Health check endpoint for chat service"""
    return {
        "service": "chat_agent",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }