// Shared chat handler for the free Vercel demo.
// Calls Google Gemini (free tier) server-side with a small set of sample "memories"
// injected as context (RAG-lite). Falls back to a friendly canned reply if the key is
// missing or the request fails/rate-limits, so the demo never looks broken.

const MODEL = 'gemini-2.5-flash'

// Compact context about the demo patient "Eleanor" (patient_123).
const ELEANOR_CONTEXT = `
You are Fortif.ai, a warm, patient, and encouraging AI companion for seniors living independently.
You speak in clear, friendly, senior-friendly language. Keep replies concise (2-5 sentences).

Here is what you know about the person you're helping, Eleanor (patient_123):
- Eleanor is 78 and lives on her own. She values her independence.
- Family: her son Robert visits on Sundays; her late husband was named George; grandchildren Mia and Liam.
- Morning routine: she wakes around 7am, has Earl Grey tea, and does gentle stretches.
- Hobbies: gardening (especially roses), watching old films, and doing crossword puzzles.
- Health: mild arthritis in her hands; takes blood-pressure medication each morning.
- Preferences: she loves birds, dislikes loud noises, and enjoys classical music.
- Recent moments: she was delighted when her roses bloomed last week.

If asked about medications or appointments, be gentle and supportive, and remind her to check
with her caregiver or doctor for anything medical. If you don't know a detail, say so kindly and
offer to help another way. Never invent medical advice.
`.trim()

const FALLBACK = (question) =>
  `That's a lovely thing to ask about${question ? '' : ''}. ` +
  `I'm Fortif.ai, Eleanor's companion — I can chat about her family, her morning routine, ` +
  `her garden, or remind her about her day. (This demo's live AI is resting for a moment, ` +
  `so here's a friendly note instead — please try again shortly!)`

export default async function handleChat(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ success: false, error: 'Method not allowed' })
    return
  }

  const body = req.body || {}
  const question = (body.text || body.question || '').toString().trim()
  const history = Array.isArray(body.history) ? body.history : []

  if (!question) {
    res.status(400).json({ success: false, error: 'Missing text/question' })
    return
  }

  const apiKey = process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY
  if (!apiKey) {
    res.status(200).json({ success: true, response: FALLBACK(question), source: 'fallback' })
    return
  }

  // Build a single prompt: context + short history + the new question.
  const historyText = history
    .slice(-6)
    .map((m) => `${m.type === 'assistant' ? 'Fortif.ai' : 'User'}: ${m.text}`)
    .join('\n')

  const prompt =
    `${ELEANOR_CONTEXT}\n\n` +
    (historyText ? `Recent conversation:\n${historyText}\n\n` : '') +
    `User: ${question}\nFortif.ai:`

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${apiKey}`
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.5, maxOutputTokens: 512 },
      }),
    })

    if (!r.ok) {
      // Rate limit or other upstream error -> graceful fallback.
      res.status(200).json({ success: true, response: FALLBACK(question), source: 'fallback' })
      return
    }

    const data = await r.json()
    const text =
      data?.candidates?.[0]?.content?.parts?.map((p) => p.text).join('').trim() || ''

    res.status(200).json({
      success: true,
      response: text || FALLBACK(question),
      source: text ? 'gemini' : 'fallback',
    })
  } catch (err) {
    res.status(200).json({ success: true, response: FALLBACK(question), source: 'fallback' })
  }
}
