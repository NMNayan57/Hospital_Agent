import type { AgentContext, AgentResponse } from "../../index";
import OpenAI from "openai";
import { getLanguagePracticePrompt } from './prompt';

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY 
});

export async function languagePracticeAgent(
  context: AgentContext
): Promise<AgentResponse> {
  try {
    const { filters, profile, metadata } = context;
    const userInput = filters?.query || "";
    const mode = filters?.mode || "text";
    const skill = filters?.skill || "general";
    const level = filters?.level || "intermediate";
    const conversationHistory = filters?.conversationHistory || [];
    const emotionContext = filters?.emotionContext || metadata?.emotion;
    
    if (!userInput.trim()) {
      return {
        success: false,
        error: "No input provided for language practice",
      };
    }

    console.log(`[Language Practice Agent] Processing voice input: "${userInput}" (mode: ${mode}, skill: ${skill})`);
    
    if (emotionContext) {
      console.log(`[Language Practice Agent] Emotion detected: ${emotionContext.primaryEmotion} (intensity: ${emotionContext.emotionIntensity})`);
    }

    // Generate structured LLM response for language practice with emotion awareness
    const llmResponse = await generateLanguagePracticeResponse(userInput, skill, level, profile, conversationHistory, emotionContext);
    
    console.log(`[Language Practice Agent] OpenAI Response: ${JSON.stringify(llmResponse, null, 2)}`);
    
    return {
      success: true,
      data: {
        response: llmResponse.response,
        feedback: llmResponse.feedback,
        score: llmResponse.score,
        improvements: llmResponse.improvements,
        nextSteps: llmResponse.nextSteps
      }
    };
    
  } catch (error) {
    console.error("Language practice agent error:", error);
    return {
      success: false,
      error: "Failed to process language practice input",
    };
  }
}

async function generateLanguagePracticeResponse(
  userInput: string, 
  skill: string, 
  level: string,
  profile: any, 
  conversationHistory: any[],
  emotionContext?: any
): Promise<any> {
  const systemPrompt = getLanguagePracticePrompt(skill, level, conversationHistory);
  
  let emotionContextText = '';
  if (emotionContext) {
    emotionContextText = `

Emotion Context:
- Current emotion: ${emotionContext.primaryEmotion}
- Intensity: ${Math.round(emotionContext.emotionIntensity * 100)}%
- Confidence: ${Math.round(emotionContext.confidence * 100)}%
- Recommended tone: ${emotionContext.recommendedTone}
- Supportive guidance: ${emotionContext.supportiveResponse}

Please adapt your response tone and approach based on the student's emotional state. Use the recommended tone and incorporate supportive guidance.`;
  }
  
  const userPrompt = `Student said: "${userInput}"

Student Context:
- Name: ${profile?.fullName || 'Student'}
- Country: ${profile?.nationality || 'Not specified'}
- Field: ${profile?.academicInfo?.fieldOfStudy || 'Not specified'}
- English Level: ${profile?.testScores?.englishScore || 'Not specified'}${emotionContextText}

Please provide a natural conversational response with helpful feedback in JSON format.`;

  // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt }
    ],
    response_format: { type: "json_object" },
    temperature: 0.7,
    max_tokens: 600
  });

  return JSON.parse(response.choices[0].message.content || '{}');
}