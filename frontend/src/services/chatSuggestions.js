import api from './api';

/**
 * Generate AI-powered suggestions based on conversation history
 * Uses Gemini AI to analyze messages and create contextual follow-up questions
 */

// Mock suggestions for when API is not available
const PATIENT_MOCK_SUGGESTIONS = [
  { id: 1, text: 'What tests do I need based on my symptoms?', icon: '🧪' },
  { id: 2, text: 'How often should I exercise?', icon: '🏃' },
  { id: 3, text: 'What side effects should I watch for?', icon: '⚠️' },
  { id: 4, text: 'Should I change my diet?', icon: '🥗' },
  { id: 5, text: 'When should I come back for a follow-up?', icon: '📅' },
];

const DOCTOR_MOCK_SUGGESTIONS = [
  { id: 1, text: 'I recommend we schedule more frequent check-ups', icon: '📋' },
  { id: 2, text: 'Have you noticed any new symptoms?', icon: '🔍' },
  { id: 3, text: 'Your medication may need adjustment', icon: '💊' },
  { id: 4, text: 'I want to do some additional tests', icon: '🧬' },
  { id: 5, text: 'Please monitor this closely and report back', icon: '📊' },
];

/**
 * Generate context-aware suggestions based on message history
 * @param {Array} messages - Array of message objects
 * @param {string} role - 'patient' or 'doctor'
 * @returns {Promise<Array>} Array of suggested questions/statements
 */
export async function generateChatSuggestions(messages, role) {
  try {
    // Extract recent messages for context
    const recentMessages = messages.slice(-10).map(msg => ({
      sender_role: msg.sender_role,
      content: msg.content,
      msg_type: msg.msg_type,
    }));

    // Call backend API
    const response = await api.post('/health/chat/generate-suggestions', {
      messages: recentMessages,
      role: role,
    });

    if (response.data && response.data.suggestions) {
      return response.data.suggestions;
    }

    // Fallback to mock suggestions if API doesn't return data
    return role === 'patient' ? PATIENT_MOCK_SUGGESTIONS : DOCTOR_MOCK_SUGGESTIONS;
  } catch (error) {
    // Use fallback mock suggestions on error
    console.warn('Failed to generate AI suggestions:', error);
    return role === 'patient' ? PATIENT_MOCK_SUGGESTIONS : DOCTOR_MOCK_SUGGESTIONS;
  }
}

/**
 * Analyze last message to create context-specific suggestions
 * This is a client-side fallback when API isn't available
 */
export function generateLocalSuggestions(messages, role) {
  if (!messages || messages.length === 0) {
    return role === 'patient' ? PATIENT_MOCK_SUGGESTIONS : DOCTOR_MOCK_SUGGESTIONS;
  }

  const lastMessage = messages[messages.length - 1];
  const content = lastMessage.content.toLowerCase();

  // Patient-side suggestions
  if (role === 'patient') {
    if (content.includes('symptom') || content.includes('pain') || content.includes('sick')) {
      return [
        { id: 1, text: 'What tests do I need?', icon: '🧪' },
        { id: 2, text: 'How long will this last?', icon: '⏱️' },
        { id: 3, text: 'What can I do to manage it?', icon: '💪' },
        { id: 4, text: 'Should I see a specialist?', icon: '🏥' },
        { id: 5, text: 'What medications help?', icon: '💊' },
      ];
    }

    if (content.includes('medication') || content.includes('drug') || content.includes('prescription')) {
      return [
        { id: 1, text: 'What are the side effects?', icon: '⚠️' },
        { id: 2, text: 'When should I take it?', icon: '⏰' },
        { id: 3, text: 'Can I take it with food?', icon: '🍽️' },
        { id: 4, text: 'What if I miss a dose?', icon: '❓' },
        { id: 5, text: 'How long will I need it?', icon: '📅' },
      ];
    }

    if (content.includes('exercise') || content.includes('workout') || content.includes('fitness')) {
      return [
        { id: 1, text: 'How often should I exercise?', icon: '🏃' },
        { id: 2, text: 'What type of exercise is best?', icon: '🚴' },
        { id: 3, text: 'Is this activity safe for me?', icon: '✅' },
        { id: 4, text: 'What are my limits?', icon: '⚡' },
        { id: 5, text: 'Should I modify my routine?', icon: '🔄' },
      ];
    }

    if (content.includes('diet') || content.includes('food') || content.includes('eat')) {
      return [
        { id: 1, text: 'What foods should I avoid?', icon: '🚫' },
        { id: 2, text: 'What foods are good for me?', icon: '✅' },
        { id: 3, text: 'Should I count calories?', icon: '📊' },
        { id: 4, text: 'Do I need supplements?', icon: '💊' },
        { id: 5, text: 'What about alcohol?', icon: '🍷' },
      ];
    }

    return PATIENT_MOCK_SUGGESTIONS;
  }

  // Doctor-side suggestions
  if (role === 'doctor') {
    if (content.includes('test') || content.includes('result') || content.includes('lab')) {
      return [
        { id: 1, text: 'These results show a concerning trend', icon: '📉' },
        { id: 2, text: 'We should do more tests', icon: '🧬' },
        { id: 3, text: 'Your results are within normal range', icon: '✅' },
        { id: 4, text: 'Let me adjust your treatment plan', icon: '📋' },
        { id: 5, text: 'Please repeat these tests in a month', icon: '🔄' },
      ];
    }

    if (content.includes('symptom') || content.includes('complaint') || content.includes('feel')) {
      return [
        { id: 1, text: 'I recommend we schedule more frequent visits', icon: '📅' },
        { id: 2, text: 'Have you had any other symptoms?', icon: '🔍' },
        { id: 3, text: 'This may require additional testing', icon: '🧪' },
        { id: 4, text: 'Your medication may need adjustment', icon: '💊' },
        { id: 5, text: 'Please keep a symptom journal', icon: '📔' },
      ];
    }

    if (content.includes('medication') || content.includes('treatment')) {
      return [
        { id: 1, text: 'I recommend changing your dosage', icon: '⚙️' },
        { id: 2, text: 'Try switching to this medication instead', icon: '💊' },
        { id: 3, text: 'Continue with your current plan', icon: '✅' },
        { id: 4, text: 'You may need to add another medication', icon: '➕' },
        { id: 5, text: 'We can stop this medication now', icon: '🛑' },
      ];
    }

    return DOCTOR_MOCK_SUGGESTIONS;
  }

  return [];
}

/**
 * Get suggestions with fallback to local generation
 */
export async function getSuggestions(messages, role) {
  // Use local generation for now (API endpoint can be added later)
  // Local suggestions provide smart context-aware recommendations
  const localSuggestions = generateLocalSuggestions(messages, role);
  return localSuggestions.slice(0, 5); // Limit to 5 suggestions
}

/**
 * Insert a suggested message into the input
 */
export function insertSuggestion(currentInput, suggestionText) {
  // If there's already input, append with space
  if (currentInput.trim()) {
    return `${currentInput}\n\n${suggestionText}`;
  }
  return suggestionText;
}

const chatSuggestions ={
  generateChatSuggestions,
  generateLocalSuggestions,
  getSuggestions,
  insertSuggestion,
}
export default chatSuggestions;

