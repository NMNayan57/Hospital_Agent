import type { AgentContext, AgentResponse } from "../../index";
import OpenAI from "openai";
import { getInterviewPrepPrompt } from './prompt';

const openai = new OpenAI({ 
  apiKey: process.env.OPENAI_API_KEY 
});

export async function interviewPrepAgent(
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
        error: "No input provided for interview preparation",
      };
    }

    console.log(`[Interview Prep Agent] Processing voice input: "${query}" (mode: ${mode})`);
    
    if (emotionContext) {
      console.log(`[Interview Prep Agent] Emotion detected: ${emotionContext.primaryEmotion} (intensity: ${emotionContext.emotionIntensity})`);
    }

    // Generate structured LLM response for interview preparation with emotion awareness
    const conversationHistory = filters?.conversationHistory || [];
    const llmResponse = await generateInterviewPrepResponse(query, profile, conversationHistory, emotionContext);
    
    console.log(`[Interview Prep Agent] OpenAI Response: ${JSON.stringify(llmResponse, null, 2)}`);
    
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
    console.error("Interview prep agent error:", error);
    return {
      success: false,
      error: "Failed to process interview preparation input",
    };
  }
}

async function generateInterviewPrepResponse(
  userInput: string, 
  profile: any, 
  conversationHistory: any[],
  emotionContext?: any
): Promise<any> {
  const systemPrompt = getInterviewPrepPrompt(profile, conversationHistory);

  let emotionContextText = '';
  if (emotionContext) {
    emotionContextText = `

Emotion Context:
- Current emotion: ${emotionContext.primaryEmotion}
- Intensity: ${Math.round(emotionContext.emotionIntensity * 100)}%
- Confidence: ${Math.round(emotionContext.confidence * 100)}%
- Recommended tone: ${emotionContext.recommendedTone}
- Supportive guidance: ${emotionContext.supportiveResponse}

Please adapt your response tone and approach based on the candidate's emotional state. Use the recommended tone and incorporate supportive guidance.`;
  }

  const userPrompt = `Candidate said: "${userInput}"${emotionContextText}

Please analyze this interview response and provide constructive feedback with a natural follow-up question in JSON format.`;

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