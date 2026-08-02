// A custom axios adapter used only in demo mode (VITE_DEMO_MODE=true).
// Everything except live chat is served locally from demoStore. Chat (/process-text, /query)
// is forwarded to the serverless Gemini function when available (Vercel), or answered locally
// on a purely static host (GitHub Pages, VITE_STATIC=true).

import { demoStore } from './demoStore'
import { SAMPLE_HAZARD_RESULT } from './sampleData'
import { demoReply } from './demoChat'

const STATIC = import.meta.env.VITE_STATIC === 'true'

const ok = (config, data, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config,
  request: {},
})

function parseBody(config) {
  if (!config.data) return {}
  if (typeof config.data === 'string') {
    try {
      return JSON.parse(config.data)
    } catch {
      return {}
    }
  }
  return config.data
}

// Small artificial latency so loading states are visible (feels real).
const delay = (ms) => new Promise((r) => setTimeout(r, ms))

export default async function demoAdapter(config) {
  const method = (config.method || 'get').toLowerCase()
  const url = config.url || ''
  const params = config.params || {}
  await delay(180)

  // --- Chat ---
  if (method === 'post' && (url === '/process-text' || url === '/query')) {
    const body = parseBody(config)
    const question = body.text || body.question || ''

    // Static host: answer locally, no backend call.
    if (STATIC) {
      await delay(350)
      return ok(config, { success: true, response: demoReply(question), source: 'offline' })
    }

    // Otherwise forward to the serverless Gemini function; fall back to a local reply on error.
    try {
      const r = await fetch(`${config.baseURL || ''}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!r.ok) throw new Error(`status ${r.status}`)
      const data = await r.json()
      return ok(config, data, r.status)
    } catch {
      return ok(config, { success: true, response: demoReply(question), source: 'offline' })
    }
  }

  // --- Hazard detection: canned sample result ---
  if (method === 'post' && url === '/hazard-detection') {
    await delay(900)
    return ok(config, SAMPLE_HAZARD_RESULT)
  }

  // --- Voice: not routed here (handled client-side via Web Speech API) ---
  if (method === 'post' && url === '/process-voice') {
    return ok(config, { success: false, error: 'Use text or the microphone (browser speech).' })
  }

  // --- Memory ingest ---
  if (method === 'post' && url === '/ingest') {
    return ok(config, demoStore.create(parseBody(config)))
  }

  // --- Metadata ---
  if (method === 'get' && url === '/dashboard/metadata/topics')
    return ok(config, { topics: demoStore.metadata().topics })
  if (method === 'get' && url === '/dashboard/metadata/emotions')
    return ok(config, { emotions: demoStore.metadata().emotions })
  if (method === 'get' && url === '/dashboard/metadata/sources')
    return ok(config, { sources: demoStore.metadata().sources })

  // --- Stats ---
  let m = url.match(/^\/dashboard\/patients\/([^/]+)\/stats$/)
  if (method === 'get' && m) return ok(config, demoStore.stats(m[1]))

  // --- List memories ---
  m = url.match(/^\/dashboard\/patients\/([^/]+)\/memories$/)
  if (method === 'get' && m) {
    return ok(config, demoStore.list({ patientId: m[1], ...params }))
  }

  // --- Single memory: get / update / delete ---
  m = url.match(/^\/dashboard\/memories\/([^/]+)$/)
  if (m) {
    const uuid = m[1]
    if (method === 'get') {
      const mem = demoStore.get(uuid)
      if (!mem) return Promise.reject(notFound(config))
      return ok(config, mem)
    }
    if (method === 'put') return ok(config, demoStore.update(uuid, parseBody(config)))
    if (method === 'delete')
      return ok(config, demoStore.remove(uuid, params.hard_delete === true || params.hard_delete === 'true'))
  }

  // --- Health ---
  if (url.includes('health')) return ok(config, { status: 'healthy', demo: true })

  return Promise.reject(notFound(config))
}

function notFound(config) {
  const err = new Error(`Demo adapter: no route for ${config.method} ${config.url}`)
  err.response = { status: 404, data: { detail: 'Not found (demo)' }, config }
  return err
}
