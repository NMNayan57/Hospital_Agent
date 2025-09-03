import os
import base64
import json
import requests
import asyncio
import websockets
from typing import Optional, Dict, Any
import tempfile

class SpeechmaticsService:
    def __init__(self):
        self.api_key = os.getenv("SPEECHMATICS_API_KEY")
        self.base_url = "https://asr.api.speechmatics.com/v2"
        self.ws_url = "wss://eu2.rt.speechmatics.com/v2"
        
        if not self.api_key:
            print("Warning: SPEECHMATICS_API_KEY not found. Speechmatics features will not work.")
    
    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> str:
        """Transcribe audio using Speechmatics batch API"""
        if not self.api_key:
            raise Exception("Speechmatics API key not configured")
        
        url = f"{self.base_url}/jobs"
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        try:
            # Prepare the request
            config = {
                "type": "transcription",
                "transcription_config": {
                    "language": language,
                    "operating_point": "enhanced",
                    "enable_partials": False,
                    "max_delay": 3
                }
            }
            
            files = {
                "data_file": open(temp_filename, "rb"),
                "config": (None, json.dumps(config), "application/json")
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Submit transcription job
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()
            
            job_data = response.json()
            job_id = job_data["id"]
            
            # Poll for completion
            result = await self._poll_job_completion(job_id)
            
            # Extract transcript
            if result and "results" in result:
                transcript_parts = []
                for result_item in result["results"]:
                    if "alternatives" in result_item:
                        for alternative in result_item["alternatives"]:
                            transcript_parts.append(alternative.get("content", ""))
                
                return " ".join(transcript_parts).strip()
            
            return ""
            
        except Exception as e:
            raise Exception(f"Speechmatics transcription failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    async def _poll_job_completion(self, job_id: str, max_wait: int = 60) -> Optional[Dict]:
        """Poll job status until completion"""
        url = f"{self.base_url}/jobs/{job_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for _ in range(max_wait):
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            job_status = response.json()
            
            if job_status["job"]["status"] == "done":
                # Get transcript
                transcript_url = f"{self.base_url}/jobs/{job_id}/transcript?format=json-v2"
                transcript_response = requests.get(transcript_url, headers=headers)
                transcript_response.raise_for_status()
                return transcript_response.json()
            
            elif job_status["job"]["status"] == "rejected":
                raise Exception(f"Speechmatics job rejected: {job_status.get('job', {}).get('errors', 'Unknown error')}")
            
            # Wait before polling again
            await asyncio.sleep(1)
        
        raise Exception("Speechmatics job timed out")
    
    async def real_time_transcribe(self, audio_stream_callback, on_transcript_callback, language: str = "en"):
        """Real-time transcription using Speechmatics WebSocket API"""
        if not self.api_key:
            raise Exception("Speechmatics API key not configured")
        
        # WebSocket connection configuration
        config = {
            "message": "StartRecognition",
            "audio_format": {
                "type": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 16000
            },
            "transcription_config": {
                "language": language,
                "enable_partials": True,
                "max_delay": 2
            }
        }
        
        try:
            # Connect to Speechmatics real-time API
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with websockets.connect(
                f"{self.ws_url}/en",
                extra_headers=headers
            ) as websocket:
                
                # Send start recognition message
                await websocket.send(json.dumps(config))
                
                # Start audio streaming task
                async def stream_audio():
                    try:
                        async for audio_chunk in audio_stream_callback():
                            if audio_chunk:
                                # Send binary audio data
                                await websocket.send(audio_chunk)
                    except Exception as e:
                        print(f"Audio streaming error: {e}")
                
                # Start receiving transcripts
                async def receive_transcripts():
                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            
                            if data.get("message") == "AddTranscript":
                                transcript = data.get("transcript", "")
                                is_final = not data.get("is_partial", True)
                                
                                await on_transcript_callback(transcript, is_final)
                            
                            elif data.get("message") == "Error":
                                raise Exception(f"Speechmatics error: {data.get('reason', 'Unknown error')}")
                    
                    except Exception as e:
                        print(f"Transcript receiving error: {e}")
                
                # Run both tasks concurrently
                await asyncio.gather(
                    stream_audio(),
                    receive_transcripts()
                )
                
        except Exception as e:
            raise Exception(f"Real-time transcription failed: {str(e)}")

class EnhancedVoiceService:
    """Enhanced voice service with multiple STT/TTS options"""
    
    def __init__(self):
        self.speechmatics = SpeechmaticsService()
        # Import existing services
        from services.elevenlabs.voice_service import ElevenLabsService, WhisperService
        self.elevenlabs = ElevenLabsService()
        self.whisper = WhisperService()
    
    async def speech_to_text(
        self, 
        audio_data: bytes, 
        method: str = "speechmatics",
        language: str = "en"
    ) -> str:
        """Convert speech to text using specified method"""
        
        if method == "speechmatics" and self.speechmatics.api_key:
            return await self.speechmatics.transcribe_audio(audio_data, language)
        
        elif method == "whisper":
            return self.whisper.speech_to_text(audio_data)
        
        else:
            # Fallback to Whisper if Speechmatics not available
            return self.whisper.speech_to_text(audio_data)
    
    def text_to_speech(
        self,
        text: str,
        method: str = "elevenlabs",
        voice_id: Optional[str] = None
    ) -> bytes:
        """Convert text to speech using specified method"""
        
        if method == "elevenlabs":
            return self.elevenlabs.text_to_speech(text, voice_id)
        else:
            # Could add more TTS services here
            return self.elevenlabs.text_to_speech(text, voice_id)
    
    async def get_available_methods(self) -> Dict[str, Any]:
        """Get available STT/TTS methods and their status"""
        
        return {
            "speech_to_text": {
                "speechmatics": {
                    "available": bool(self.speechmatics.api_key),
                    "features": ["real-time", "batch", "multilingual", "enhanced_accuracy"]
                },
                "whisper": {
                    "available": bool(self.whisper.api_key),
                    "features": ["batch", "multilingual", "openai_powered"]
                }
            },
            "text_to_speech": {
                "elevenlabs": {
                    "available": bool(self.elevenlabs.api_key),
                    "features": ["voice_cloning", "emotional_range", "multilingual"]
                }
            }
        }
    
    async def real_time_voice_processing(
        self,
        audio_stream_callback,
        text_processor_callback,
        response_callback,
        stt_method: str = "speechmatics",
        tts_method: str = "elevenlabs",
        language: str = "en"
    ):
        """Real-time voice processing pipeline"""
        
        current_transcript = ""
        
        async def on_transcript(transcript: str, is_final: bool):
            nonlocal current_transcript
            
            if is_final and transcript.strip():
                # Process complete transcript
                response_text = await text_processor_callback(transcript)
                
                # Convert response to speech
                response_audio = self.text_to_speech(response_text, tts_method)
                
                # Send back to client
                await response_callback(response_text, response_audio)
                
                current_transcript = ""
            else:
                current_transcript = transcript
        
        # Start real-time transcription
        if stt_method == "speechmatics":
            await self.speechmatics.real_time_transcribe(
                audio_stream_callback,
                on_transcript,
                language
            )
        else:
            # For non-real-time methods, we'd need to buffer audio
            # and process in chunks
            raise NotImplementedError("Real-time processing only available with Speechmatics currently")