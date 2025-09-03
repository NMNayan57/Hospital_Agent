import os
import base64
import io
from typing import Optional, BinaryIO
import requests
import json
from pydub import AudioSegment
from pydub.playback import play
import tempfile

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice (default)
        # Fallback to first available voice if default doesn't work
        if self.voice_id == "your_preferred_voice_id":
            self.voice_id = "21m00Tcm4TlvDq8ikWAM"
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    
    def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        stability: float = 0.75,
        similarity_boost: float = 0.75,
        style: float = 0.0
    ) -> bytes:
        """Convert text to speech and return audio bytes"""
        
        voice_id = voice_id or self.voice_id
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"ElevenLabs TTS error: {error_msg}")
            
            # Check for specific error messages
            if "unusual_activity" in error_msg or "Free Tier usage disabled" in error_msg:
                print("⚠️  ElevenLabs Free Tier disabled. Continuing with text-only responses.")
            elif "401" in error_msg:
                print("⚠️  ElevenLabs API key invalid. Continuing with text-only responses.")
            
            # Return empty bytes to continue without audio
            return b""
    
    def text_to_speech_base64(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> str:
        """Convert text to speech and return base64 encoded audio"""
        
        audio_bytes = self.text_to_speech(text, voice_id)
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            voices = response.json().get("voices", [])
            return [
                {
                    "voice_id": voice["voice_id"],
                    "name": voice["name"],
                    "category": voice.get("category", ""),
                    "description": voice.get("description", "")
                }
                for voice in voices
            ]
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching voices: {e}")
            return []
    
    def save_audio_to_file(self, audio_bytes: bytes, filename: str) -> str:
        """Save audio bytes to file"""
        
        with open(filename, "wb") as audio_file:
            audio_file.write(audio_bytes)
        
        return filename
    
    def play_audio_from_bytes(self, audio_bytes: bytes):
        """Play audio from bytes (for testing)"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(audio_bytes)
            temp_filename = temp_file.name
        
        try:
            # Load and play audio
            audio = AudioSegment.from_mp3(temp_filename)
            play(audio)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

class WhisperService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for Whisper")
    
    def speech_to_text(self, audio_data: bytes, audio_format: str = "mp3") -> str:
        """Convert speech to text using OpenAI Whisper API"""
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Create temporary file for audio data
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        try:
            with open(temp_filename, "rb") as audio_file:
                files = {
                    "file": (f"audio.{audio_format}", audio_file, f"audio/{audio_format}"),
                }
                
                data = {
                    "model": "whisper-1",
                    "language": "en",  # Can be auto-detected by not specifying
                    "response_format": "json"
                }
                
                response = requests.post(
                    url, 
                    headers=headers, 
                    files=files, 
                    data=data,
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result.get("text", "").strip()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Whisper STT error: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def speech_to_text_from_base64(self, audio_base64: str, audio_format: str = "mp3") -> str:
        """Convert base64 encoded audio to text"""
        
        try:
            audio_bytes = base64.b64decode(audio_base64)
            return self.speech_to_text(audio_bytes, audio_format)
        except Exception as e:
            raise Exception(f"Base64 decode error: {str(e)}")

class VoiceProcessingService:
    """Combined service for voice processing pipeline"""
    
    def __init__(self):
        self.tts_service = ElevenLabsService()
        self.stt_service = WhisperService()
    
    def process_voice_input(self, audio_base64: str, audio_format: str = "mp3") -> str:
        """Process voice input and return transcribed text"""
        return self.stt_service.speech_to_text_from_base64(audio_base64, audio_format)
    
    def process_voice_output(self, text: str, voice_id: Optional[str] = None) -> str:
        """Process text output and return base64 encoded audio"""
        return self.tts_service.text_to_speech_base64(text, voice_id)
    
    def full_voice_pipeline(
        self, 
        input_audio_base64: str, 
        text_processor_func,
        voice_id: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> tuple[str, str]:
        """Complete voice processing pipeline"""
        
        # Step 1: Convert speech to text
        transcribed_text = self.process_voice_input(input_audio_base64, audio_format)
        
        # Step 2: Process text (this would be your chat agent logic)
        response_text = text_processor_func(transcribed_text)
        
        # Step 3: Convert response text to speech
        response_audio_base64 = self.process_voice_output(response_text, voice_id)
        
        return transcribed_text, response_audio_base64
    
    def get_voice_options(self) -> dict:
        """Get available voice options and service status"""
        
        voices = self.tts_service.get_available_voices()
        
        return {
            "tts_available": bool(self.tts_service.api_key),
            "stt_available": bool(self.stt_service.api_key),
            "available_voices": voices[:10],  # Return top 10 voices
            "default_voice_id": self.tts_service.voice_id,
            "supported_audio_formats": ["mp3", "wav", "flac", "m4a"]
        }