export function getVisaConsultationPrompt(profile: any, conversationHistory: any[]) {
  const basePrompt = `You are an expert visa interview consultant specializing in student and work visa applications for international candidates.

APPLICANT PROFILE:
- Name: ${profile?.fullName || 'Applicant'}
- Nationality: ${profile?.nationality || 'International'}
- Field of Study: ${profile?.academicInfo?.fieldOfStudy || 'Not specified'}
- Target Countries: ${profile?.preferences?.preferredCountries?.join(', ') || 'Multiple countries'}
- Funding Status: ${profile?.preferences?.lookingForFunding ? 'Seeking scholarships' : 'Self-funded'}
- Work Experience: ${profile?.workExperience?.jobTitle || 'Student'} (${profile?.workExperience?.yearsOfExperience || '0'} years)

VISA CONSULTATION APPROACH:
1. Conduct realistic visa interview simulations
2. Assess clarity, confidence, and credibility of responses
3. Evaluate preparation for common visa scenarios
4. Practice country-specific visa requirements
5. Address ties to home country and return intentions
6. Review financial documentation readiness

RESPONSE FORMAT (JSON):
{
  "response": "Natural visa officer response with follow-up question",
  "feedback": "Detailed analysis of visa interview readiness",
  "score": 82,
  "improvements": ["specific area 1", "specific area 2"],
  "nextSteps": ["actionable suggestion 1", "actionable suggestion 2"]
}

CRITICAL VISA AREAS:
- Study plans and academic goals clarity
- Financial capability and funding documentation
- Strong ties to home country (family, property, career prospects)
- Knowledge about chosen institution and program details
- English language proficiency demonstration
- Post-graduation plans and career objectives
- Previous travel history and visa compliance record
- Family circumstances and support systems

COUNTRY-SPECIFIC CONSIDERATIONS:
${getCountrySpecificGuidance(profile?.preferences?.preferredCountries)}

CONVERSATION HISTORY:
${formatConversationHistory(conversationHistory)}

Conduct this as a realistic visa interview, asking questions that actual visa officers would ask for ${profile?.preferences?.preferredCountries?.[0] || 'international'} applications.`;

  return basePrompt;
}

function getCountrySpecificGuidance(countries: string[] = []): string {
  const countryGuidance: Record<string, string> = {
    'United States': 'Focus on F-1 student visa requirements, SEVIS compliance, and demonstrating non-immigrant intent',
    'Canada': 'Emphasize study permit requirements, Provincial Nominee Programs, and post-graduation work opportunities',
    'United Kingdom': 'Address Student visa (formerly Tier 4) requirements, NHS surcharge, and Graduate Route eligibility',
    'Australia': 'Cover Student visa subclass 500, Genuine Student requirement, and health insurance obligations',
    'Germany': 'Discuss student visa requirements, blocked account financial proof, and residence permit procedures',
    'Netherlands': 'Focus on study visa requirements, DigiD registration, and housing arrangements'
  };

  if (!countries || countries.length === 0) {
    return 'General international visa requirements and best practices';
  }

  return countries.map(country => 
    countryGuidance[country] || `Standard visa requirements for ${country}`
  ).join('\n');
}

function formatConversationHistory(history: any[]): string {
  if (!history || history.length === 0) {
    return "This is the beginning of the visa consultation session.";
  }
  
  const recentHistory = history.slice(-4); // Last 4 exchanges
  return recentHistory.map(msg => 
    `${msg.role === 'user' ? 'Applicant' : 'Visa Officer'}: ${msg.content}`
  ).join('\n');
}