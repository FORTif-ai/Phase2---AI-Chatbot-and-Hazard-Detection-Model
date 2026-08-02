// A custom axios adapter used only in demo mode (VITE_DEMO_MODE=true).
// Everything except live chat is served locally from demoStore; chat (/process-text, /query)
// is forwarded to the real serverless function so it uses live Gemini.

import { demoStore } from './demoStore'
import { SAMPLE_HAZARD_RESULT } from './sampleData'

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

  // --- Live chat: forward to the serverless Gemini function ---
  if (method === 'post' && (url === '/process-text' || url === '/query')) {
    const target = `${config.baseURL || ''}${url}`
    const body = parseBody(config)
    const r = await fetch(target, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await r.json().catch(() => ({
      success: true,
      response: "I'm here to help Eleanor — could you try asking that again?",
    }))
    return ok(config, data, r.status)
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
