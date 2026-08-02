import axios from 'axios';
import demoAdapter from '../demo/demoAdapter';

// In demo mode (static Vercel build) chat is forwarded to the serverless Gemini
// function and everything else is served locally.
const DEMO = import.meta.env.VITE_DEMO_MODE === 'true';

// Create axios instance for voice command API
// Use relative URL to go through Vite proxy in development
const voiceApiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

if (DEMO) voiceApiClient.defaults.adapter = demoAdapter;

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
  triggerHazardDetection: async (mode, options = {}) => {
    const payload = {
      mode: mode || 'directory',
      ...options
    };
    const response = await voiceApiClient.post('/hazard-detection', payload, {
      timeout: 300000, // 5 minute timeout for hazard detection (videos can take longer)
    });
    return response.data;
  },
};

export default voiceApiClient;
