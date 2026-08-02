import handleChat from './_gemini.js'

// POST /api/query  — used by the dashboard chat client (chatApi).
export default function handler(req, res) {
  return handleChat(req, res)
}
