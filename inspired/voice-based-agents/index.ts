// Voice-Based Agents - Specialized conversational AI agents for real-time voice interaction
// Each agent has its own folder with structured prompts and conversation logic

export { languagePracticeAgent } from './language-practice';
export { interviewPrepAgent } from './interview-prep';
export { visaConsultationAgent } from './visa-consultation';

/**
 * Voice-Based Agent Architecture:
 * 
 * /voice-based-agents/
 * ├── language-practice/
 * │   ├── index.ts          # Main agent logic with OpenAI integration
 * │   └── prompt.ts         # Specialized prompts for different skill levels (IELTS, TOEFL, academic, general)
 * ├── interview-prep/
 * │   ├── index.ts          # Interview coaching logic with feedback scoring
 * │   └── prompt.ts         # Industry-specific interview questions and behavioral assessment
 * └── visa-consultation/
 *     ├── index.ts          # Visa interview simulation with country-specific guidance
 *     └── prompt.ts         # Country-specific visa requirements and common questions
 * 
 * Each agent provides:
 * - Real-time conversational responses
 * - Structured feedback with scoring (0-100)
 * - Specific improvement suggestions
 * - Next steps for continued practice
 * - Context-aware follow-up questions
 */