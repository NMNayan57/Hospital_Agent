import type { AgentContext, AgentResponse } from "../../index";
import OpenAI from "openai";
import { getVisaConsultationPrompt } from './prompt';

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY 
});

export async function visaConsultationAgent(
  context: AgentContext
): Promise<AgentResponse> {
  try {
    const { filters, profile, metadata } = context;
    const query = filters?.query || "";
    const mode = filters?.mode || "text";
    const emotionContext = filters?.emotionContext || metadata?.emotion;
    
    if (!query.trim()) {
      return {
        success: false,
        error: "No input provided for visa consultation",
      };
    }

    console.log(`[Visa Consultation Agent] Processing voice input: "${query}" (mode: ${mode})`);
    
    if (emotionContext) {
      console.log(`[Visa Consultation Agent] Emotion detected: ${emotionContext.primaryEmotion} (intensity: ${emotionContext.emotionIntensity})`);
    }

    // Generate structured LLM response for visa consultation with emotion awareness
    const conversationHistory = filters?.conversationHistory || [];
    const llmResponse = await generateVisaConsultationResponse(query, profile, conversationHistory, emotionContext);
    
    console.log(`[Visa Consultation Agent] OpenAI Response: ${JSON.stringify(llmResponse, null, 2)}`);
    
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
    console.error("Visa consultation agent error:", error);
    return {
      success: false,
      error: "Failed to process visa consultation input",
    };
  }
}

async function generateVisaConsultationResponse(
  userInput: string, 
  profile: any, 
  conversationHistory: any[],
  emotionContext?: any
): Promise<any> {
  const systemPrompt = getVisaConsultationPrompt(profile, conversationHistory);

  let emotionContextText = '';
  if (emotionContext) {
    emotionContextText = `

Emotion Context:
- Current emotion: ${emotionContext.primaryEmotion}
- Intensity: ${Math.round(emotionContext.emotionIntensity * 100)}%
- Confidence: ${Math.round(emotionContext.confidence * 100)}%
- Recommended tone: ${emotionContext.recommendedTone}
- Supportive guidance: ${emotionContext.supportiveResponse}

Please adapt your response tone and approach based on the applicant's emotional state. Use the recommended tone and incorporate supportive guidance.`;
  }

  const userPrompt = `Visa applicant said: "${userInput}"${emotionContextText}

Please analyze this visa interview response and provide constructive feedback with a realistic follow-up question in JSON format.`;

  // Use GPT-4o-mini for faster voice conversation responses
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt }
    ],
    response_format: { type: "json_object" },
    temperature: 0.7,
    max_tokens: 300 // Shorter responses for faster voice interaction
  });

  return JSON.parse(response.choices[0].message.content || '{}');
}