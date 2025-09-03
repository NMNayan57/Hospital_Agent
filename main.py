from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="X Hospital AI Assistant",
    description="AI-powered hospital assistant for appointment booking via chat and voice",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint moved to serve frontend instead

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include routers
from api.routers import chat_router, voice_router, scheduler_router, websocket_router, system_router

app.include_router(chat_router.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(voice_router.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(scheduler_router.router, prefix="/api/v1/scheduler", tags=["Scheduler"])
app.include_router(websocket_router.router, prefix="/ws", tags=["WebSocket"])
app.include_router(system_router.router, prefix="/api/v1/system", tags=["System"])

# Serve static frontend files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount static files for CSS, JS, etc.
if os.path.exists("frontend"):
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    frontend_path = "frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    else:
        return {"message": "Frontend not found. Please ensure frontend/index.html exists."}

@app.get("/voice")
async def serve_voice_interface():
    """Serve the working real-time voice interface"""
    voice_path = "frontend/voice-working.html"
    if os.path.exists(voice_path):
        return FileResponse(voice_path, media_type="text/html")
    else:
        return {"message": "Voice interface not found. Please ensure frontend/voice-working.html exists."}

@app.get("/voice-old")
async def serve_old_voice_interface():
    """Serve the old voice interface for comparison"""
    voice_path = "frontend/voice-realtime.html"
    if os.path.exists(voice_path):
        return FileResponse(voice_path, media_type="text/html")
    else:
        return {"message": "Old voice interface not found."}

@app.get("/test")
async def test_frontend():
    """Test endpoint to verify static serving"""
    return FileResponse("test_frontend.html", media_type="text/html")

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", 8000))
    host = os.getenv("SERVER_HOST", "localhost")
    debug = os.getenv("DEBUG_MODE", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )