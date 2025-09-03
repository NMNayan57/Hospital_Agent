import os
from typing import Dict, List, Optional, Any
import json
from openai import OpenAI

# Initialize OpenAI client with error handling
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

class EmotionAnalysis:
    def __init__(
        self,
        primary_emotion: str,
        emotion_intensity: float,
        confidence: float,
        emotional_indicators: List[str],
        supportive_response: str,
        recommended_tone: str
    ):
        self.primary_emotion = primary_emotion
        self.emotion_intensity = max(0.0, min(1.0, emotion_intensity))
        self.confidence = max(0.0, min(1.0, confidence))
        self.emotional_indicators = emotional_indicators
        self.supportive_response = supportive_response
        self.recommended_tone = recommended_tone

class VoiceEmotionData:
    def __init__(
        self,
        transcript: str,
        voice_features: Optional[Dict] = None,
        conversation_history: Optional[List[Any]] = None
    ):
        self.transcript = transcript
        self.voice_features = voice_features or {}
        self.conversation_history = conversation_history or []

async def analyze_emotion_from_voice(data: VoiceEmotionData) -> EmotionAnalysis:
    """Analyze emotion from voice interaction using OpenAI GPT-4"""
    
    print(f'[Emotion Recognition] Analyzing voice emotion for: {data.transcript[:50]}')
    
    try:
        system_prompt = """You are an expert emotion recognition system specializing in analyzing speech patterns and linguistic cues to identify emotional states during healthcare conversations.

EMOTION DETECTION FRAMEWORK:
Primary emotions to detect:
- Confidence (high self-assurance, assertive speech)
- Anxiety (nervous, uncertain, hesitant speech patterns)
- Frustration (impatient, strained, challenging tone)
- Enthusiasm (excited, energetic, positive engagement)
- Confusion (uncertain, questioning, seeking clarification)
- Stress (overwhelmed, pressured, tense communication)
- Determination (focused, goal-oriented, persistent)
- Disappointment (deflated, discouraged, low energy)
- Pain (discomfort, suffering, physical distress)
- Relief (calm, relaxed, grateful)

ANALYSIS CRITERIA:
1. Linguistic patterns (word choice, sentence structure, hesitations)
2. Content emotional markers (expressions of feeling, uncertainty indicators)
3. Communication style (question frequency, statement confidence)
4. Context sensitivity (healthcare/medical conversation setting)
5. Pain or discomfort indicators
6. Urgency levels

RESPONSE FORMAT (JSON):
{
  "primaryEmotion": "anxiety",
  "emotionIntensity": 0.7,
  "confidence": 0.85,
  "emotionalIndicators": ["hesitation patterns", "uncertainty words", "health concerns"],
  "supportiveResponse": "I understand you may be feeling anxious about your health concerns. That's completely normal - let's work through this together.",
  "recommendedTone": "gentle"
}

TONE RECOMMENDATIONS:
- encouraging: For low confidence, self-doubt, disappointment
- calming: For anxiety, stress, overwhelming situations, pain
- energetic: For enthusiasm, motivation building
- gentle: For frustration, confusion, emotional sensitivity, pain
- professional: For confident, focused, goal-oriented states
- compassionate: For pain, serious health concerns

Provide empathetic, context-appropriate emotional support while maintaining healthcare focus."""

        user_prompt = f"""Analyze the emotional state from this healthcare voice interaction:

TRANSCRIPT: "{data.transcript}"

CONTEXT:
- Conversation type: Healthcare/Hospital appointment system
- Voice features: {json.dumps(data.voice_features) if data.voice_features else 'Not available'}
- Previous interactions: {len(data.conversation_history)} messages
- Setting: Medical appointment booking and consultation

Please analyze the emotional state and provide supportive guidance appropriate for a healthcare setting."""

        client = get_openai_client()
        if not client:
            raise Exception("OpenAI API key not configured")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for consistent emotion detection
            max_tokens=400
        )

        emotion_data = json.loads(response.choices[0].message.content or '{}')
        
        print(f'[Emotion Recognition] Detected emotion: {emotion_data.get("primaryEmotion")} with intensity: {emotion_data.get("emotionIntensity")}')
        
        return EmotionAnalysis(
            primary_emotion=emotion_data.get('primaryEmotion', 'neutral'),
            emotion_intensity=emotion_data.get('emotionIntensity', 0.5),
            confidence=emotion_data.get('confidence', 0.5),
            emotional_indicators=emotion_data.get('emotionalIndicators', []),
            supportive_response=emotion_data.get('supportiveResponse', "I'm here to help you with your healthcare needs."),
            recommended_tone=emotion_data.get('recommendedTone', 'encouraging')
        )
        
    except Exception as error:
        print(f'[Emotion Recognition] Error: {error}')
        
        # Fallback emotion analysis based on basic text patterns
        fallback_emotion = detect_basic_emotion(data.transcript)
        
        return EmotionAnalysis(
            primary_emotion=fallback_emotion['emotion'],
            emotion_intensity=fallback_emotion['intensity'],
            confidence=0.3,
            emotional_indicators=['Basic text analysis'],
            supportive_response="I'm here to help you with your healthcare needs. Let's continue together.",
            recommended_tone='encouraging'
        )

def detect_basic_emotion(transcript: str) -> Dict[str, Any]:
    """Basic emotion detection using keyword patterns"""
    text = transcript.lower()
    
    # Healthcare-specific emotion detection patterns
    patterns = {
        'anxiety': ['nervous', 'worried', 'scared', 'unsure', 'afraid', 'concerned', 'anxious'],
        'frustration': ['frustrated', 'annoying', 'difficult', 'hard', 'stuck', 'upset'],
        'enthusiasm': ['excited', 'great', 'good', 'happy', 'wonderful', 'excellent'],
        'confidence': ['definitely', 'sure', 'certain', 'know', 'confident', 'absolutely'],
        'confusion': ['confused', 'unclear', 'what', 'how', 'why', 'don\'t understand'],
        'pain': ['hurt', 'pain', 'ache', 'sore', 'uncomfortable', 'suffering'],
        'stress': ['stressed', 'overwhelmed', 'pressure', 'urgent', 'emergency'],
        'relief': ['better', 'relieved', 'good', 'fine', 'okay', 'thankful']
    }
    
    max_score = 0
    detected_emotion = 'neutral'
    
    for emotion, keywords in patterns.items():
        score = sum(1 for keyword in keywords if keyword in text)
        
        if score > max_score:
            max_score = score
            detected_emotion = emotion
    
    return {
        'emotion': detected_emotion,
        'intensity': min(0.8, max_score * 0.2 + 0.3)
    }