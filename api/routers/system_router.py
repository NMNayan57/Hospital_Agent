from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()

@router.get("/api-keys/status")
async def check_api_keys_status():
    """Check which API keys are configured"""
    
    return {
        "timestamp": datetime.now().isoformat(),
        "api_keys": {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "status": "✅ Ready" if os.getenv("OPENAI_API_KEY") else "❌ Missing"
            },
            "elevenlabs": {
                "configured": bool(os.getenv("ELEVENLABS_API_KEY")),
                "status": "✅ Ready" if os.getenv("ELEVENLABS_API_KEY") else "❌ Missing"
            },
            "speechmatics": {
                "configured": bool(os.getenv("SPEECHMATICS_API_KEY")),
                "status": "✅ Ready" if os.getenv("SPEECHMATICS_API_KEY") else "❌ Missing"
            },
            "anthropic": {
                "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
                "status": "✅ Ready" if os.getenv("ANTHROPIC_API_KEY") else "❌ Missing"
            }
        },
        "services": {
            "chat": "Available" if os.getenv("OPENAI_API_KEY") else "Limited (No AI)",
            "voice": "Available" if os.getenv("OPENAI_API_KEY") and os.getenv("ELEVENLABS_API_KEY") else "Limited",
            "database": "✅ Active",
            "websocket": "✅ Active"
        }
    }

@router.get("/test-chat")
async def test_chat_without_api():
    """Test chat functionality without OpenAI"""
    from sqlalchemy.orm import sessionmaker
    from models.database import engine
    from services.rag.rag_service import RAGService
    
    try:
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        rag_service = RAGService(db)
        
        # Test symptom analysis
        chest_pain_doctors = rag_service.search_doctors_by_symptoms("chest pain")
        
        if chest_pain_doctors:
            doctor = chest_pain_doctors[0]
            response = f"""Hello! I can help you even without full AI integration.

Based on your symptoms "chest pain", I recommend seeing:
👨‍⚕️ {doctor['name']} - {doctor['specialty']}

Our system found {len(chest_pain_doctors)} suitable doctor(s) for your condition.

To fully enable AI-powered conversations, please configure your OpenAI API key in the .env file.

Would you like me to check doctor availability or help you with anything else?"""
        else:
            response = "System is working, but no doctors found in database. Please contact +8801712345000."
        
        db.close()
        return {
            "success": True,
            "response": response,
            "doctor_count": len(chest_pain_doctors) if chest_pain_doctors else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "System error. Please contact +8801712345000."
        }