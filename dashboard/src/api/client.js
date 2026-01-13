import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Memory API
export const memoryApi = {
  createMemory: async (memoryData) => {
    const response = await api.post('/ingest', memoryData, {
      headers: {
        'X-API-Key': 'fortifai-dev-key-2024',
      },
    })
    return response.data
  },

  listMemories: async (patientId, params = {}) => {
    const response = await api.get(`/dashboard/patients/${patientId}/memories`, {
      params,
    })
    return response.data
  },

  getMemory: async (uuid) => {
    const response = await api.get(`/dashboard/memories/${uuid}`)
    return response.data
  },

  updateMemory: async (uuid, updates) => {
    const response = await api.put(`/dashboard/memories/${uuid}`, updates)
    return response.data
  },

  deleteMemory: async (uuid, hardDelete = false) => {
    const response = await api.delete(`/dashboard/memories/${uuid}`, {
      params: { hard_delete: hardDelete },
    })
    return response.data
  },

  getStats: async (patientId) => {
    const response = await api.get(`/dashboard/patients/${patientId}/stats`)
    return response.data
  },

  getTopics: async () => {
    const response = await api.get('/dashboard/metadata/topics')
    return response.data.topics
  },

  getEmotions: async () => {
    const response = await api.get('/dashboard/metadata/emotions')
    return response.data.emotions
  },

  getSources: async () => {
    const response = await api.get('/dashboard/metadata/sources')
    return response.data.sources
  },
}

// Chat API
export const chatApi = {
  sendMessage: async (patientId, question, options = {}) => {
    const response = await api.post('/query', {
      patient_id: patientId,
      question: question,
      include_sensitive: options.includeSensitive || false,
      emotion_filter: options.emotionFilter || null,
      limit: options.limit || 3,
      history: options.history || [],
    }, {
      headers: {
        'X-API-Key': 'fortifai-dev-key-2024',
      },
    })
    return response.data
  },
}

export default api
