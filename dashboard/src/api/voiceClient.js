import axios from 'axios';

// Create axios instance for voice command API
// Use relative URL to go through Vite proxy in development
const voiceApiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const voiceApi = {
  // Process voice audio
  processVoice: async (formData) => {
    const response = await voiceApiClient.post('/process-voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 second timeout
    });
    return response.data;
  },

  // Process text command
  processText: async (text, patientId) => {
    const response = await voiceApiClient.post('/process-text', {
      text,
      patient_id: patientId,
    });
    return response.data;
  },

  // Trigger hazard detection
  triggerHazardDetection: async () => {
    const response = await voiceApiClient.post('/hazard-detection', {}, {
      timeout: 120000, // 2 minute timeout for hazard detection
    });
    return response.data;
  },
};

export default voiceApiClient;
