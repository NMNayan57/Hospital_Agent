from fastapi import APIRouter, WebSocket, Depends, Query
from api.websocket_manager import handle_websocket_chat, handle_websocket_voice, get_websocket_status

router = APIRouter()

@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    phone_number: str = Query(..., description="Patient phone number")
):
    """WebSocket endpoint for real-time chat"""
    await handle_websocket_chat(websocket, phone_number)

@router.websocket("/voice")
async def websocket_voice_endpoint(
    websocket: WebSocket,
    phone_number: str = Query(..., description="Patient phone number")
):
    """WebSocket endpoint for real-time voice processing"""
    await handle_websocket_voice(websocket, phone_number)

@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return await get_websocket_status()