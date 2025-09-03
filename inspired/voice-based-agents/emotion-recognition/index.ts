import OpenAI from "openai";

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY 
});

export interface EmotionAnalysis {
  primaryEmotion: string;
  emotionIntensity: number; // 0-1 scale
  confidence: number; // 0-1 scale
  emotionalIndicators: string[];
  supportiveResponse: string;
  recommendedTone: 'encouraging' | 'calming' | 'energetic' | 'gentle' | 'professional';
}

export interface VoiceEmotionData {
  transcript: string;
  voiceFeatures?: {
    pitch?: number;
    pace?: number;
    volume?: number;
    pauseFrequency?: number;
  };
  conversationHistory?: any[];
}

export async function analyzeEmotionFromVoice(data: VoiceEmotionData): Promise<EmotionAnalysis> {
  console.log('[Emotion Recognition] Analyzing voice emotion for:', data.transcript.substring(0, 50));
  
  try {
    const systemPrompt = `You are an expert emotion recognition system specializing in analyzing speech patterns and linguistic cues to identify emotional states during educational conversations.

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

ANALYSIS CRITERIA:
1. Linguistic patterns (word choice, sentence structure, hesitations)
2. Content emotional markers (expressions of feeling, uncertainty indicators)
3. Communication style (question frequency, statement confidence)
4. Context sensitivity (educational/professional conversation setting)

RESPONSE FORMAT (JSON):
{
  "primaryEmotion": "anxiety",
  "emotionIntensity": 0.7,
  "confidence": 0.85,
  "emotionalIndicators": ["hesitation patterns", "uncertainty words", "self-doubt expressions"],
  "supportiveResponse": "I can sense some nervousness in your response. That's completely normal when practicing - let's take this step by step.",
  "recommendedTone": "gentle"
}

TONE RECOMMENDATIONS:
- encouraging: For low confidence, self-doubt, disappointment
- calming: For anxiety, stress, overwhelming situations
- energetic: For enthusiasm, motivation building
- gentle: For frustration, confusion, emotional sensitivity
- professional: For confident, focused, goal-oriented states

Provide empathetic, context-appropriate emotional support while maintaining educational focus.`;

    const userPrompt = `Analyze the emotional state from this voice interaction:

TRANSCRIPT: "${data.transcript}"

CONTEXT:
- Conversation type: Educational/Professional development
- Voice features: ${data.voiceFeatures ? JSON.stringify(data.voiceFeatures) : 'Not available'}
- Previous interactions: ${data.conversationHistory?.length || 0} messages

Please analyze the emotional state and provide supportive guidance.`;

    // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ],
      response_format: { type: "json_object" },
      temperature: 0.3, // Lower temperature for more consistent emotion detection
      max_tokens: 400
    });

    const emotionData = JSON.parse(response.choices[0].message.content || '{}');
    
    console.log('[Emotion Recognition] Detected emotion:', emotionData.primaryEmotion, 'with intensity:', emotionData.emotionIntensity);
    
    return {
      primaryEmotion: emotionData.primaryEmotion || 'neutral',
      emotionIntensity: Math.max(0, Math.min(1, emotionData.emotionIntensity || 0.5)),
      confidence: Math.max(0, Math.min(1, emotionData.confidence || 0.5)),
      emotionalIndicators: emotionData.emotionalIndicators || [],
      supportiveResponse: emotionData.supportiveResponse || "I'm here to support your learning journey.",
      recommendedTone: emotionData.recommendedTone || 'encouraging'
    };
    
  } catch (error) {
    console.error('[Emotion Recognition] Error:', error);
    
    // Fallback emotion analysis based on basic text patterns
    const fallbackEmotion = detectBasicEmotion(data.transcript);
    
    return {
      primaryEmotion: fallbackEmotion.emotion,
      emotionIntensity: fallbackEmotion.intensity,
      confidence: 0.3,
      emotionalIndicators: ['Basic text analysis'],
      supportiveResponse: "I'm here to help you with your learning. Let's continue together.",
      recommendedTone: 'encouraging'
    };
  }
}

function detectBasicEmotion(transcript: string): { emotion: string; intensity: number } {
  const text = transcript.toLowerCase();
  
  // Basic emotion detection patterns
  const patterns = {
    anxiety: ['nervous', 'worried', 'scared', 'unsure', 'maybe', 'i think', 'not sure'],
    frustration: ['frustrated', 'annoying', 'difficult', 'hard', 'stuck', 'confused'],
    enthusiasm: ['excited', 'great', 'awesome', 'love', 'amazing', 'wonderful'],
    confidence: ['definitely', 'sure', 'certain', 'know', 'confident', 'absolutely'],
    confusion: ['confused', 'unclear', 'what', 'how', 'why', 'don\'t understand']
  };
  
  let maxScore = 0;
  let detectedEmotion = 'neutral';
  
  for (const [emotion, keywords] of Object.entries(patterns)) {
    const score = keywords.reduce((count, keyword) => {
      return count + (text.includes(keyword) ? 1 : 0);
    }, 0);
    
    if (score > maxScore) {
      maxScore = score;
      detectedEmotion = emotion;
    }
  }
  
  return {
    emotion: detectedEmotion,
    intensity: Math.min(0.8, maxScore * 0.2 + 0.3)
  };
}