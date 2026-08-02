import handleChat from './_gemini.js'

// POST /api/process-text — used by the Voice/Text command page (voiceApi.processText).
export default function handler(req, res) {
  return handleChat(req, res)
}
