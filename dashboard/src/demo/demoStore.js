// A tiny in-browser "database" for the demo, backed by localStorage so a visitor's
// added/edited memories persist across reloads (per browser).

import { SAMPLE_MEMORIES, TOPICS, EMOTIONS, SOURCES } from './sampleData'

const KEY = 'fortifai_demo_memories_v1'

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  const seeded = JSON.parse(JSON.stringify(SAMPLE_MEMORIES))
  save(seeded)
  return seeded
}

function save(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list))
  } catch {
    /* ignore */
  }
}

function uid() {
  return `demo-mem-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
}

export const demoStore = {
  list({ patientId, page = 1, per_page = 20, topic, emotion, source, search, include_sensitive }) {
    let items = load().filter((m) => m.patient_id === patientId)
    if (!include_sensitive) items = items.filter((m) => !m.is_sensitive)
    if (topic) items = items.filter((m) => m.topic === topic)
    if (emotion) items = items.filter((m) => m.emotion === emotion)
    if (source) items = items.filter((m) => m.source === source)
    if (search) {
      const q = String(search).toLowerCase()
      items = items.filter(
        (m) =>
          m.text.toLowerCase().includes(q) ||
          (m.entities || []).some((e) => e.toLowerCase().includes(q))
      )
    }
    items.sort((a, b) => new Date(b.ingested_at) - new Date(a.ingested_at))

    const total_count = items.length
    const start = (page - 1) * per_page
    const memories = items.slice(start, start + per_page)
    return { memories, total_count, has_more: start + per_page < total_count }
  },

  get(uuid) {
    return load().find((m) => m.uuid === uuid) || null
  },

  create(data) {
    const list = load()
    const memory = {
      uuid: uid(),
      patient_id: data.patient_id,
      text: data.raw_text || data.text || '',
      topic: data.topic || 'daily_routine',
      emotion: data.emotion || 'neutral',
      source: data.source || 'patient_conversation',
      entities: data.entities || [],
      is_sensitive: !!data.is_sensitive,
      chunk_index: 0,
      total_chunks: 1,
      ingested_at: new Date().toISOString(),
    }
    list.unshift(memory)
    save(list)
    return { success: true, uuid: memory.uuid, message: 'Memory created (demo)' }
  },

  update(uuid, updates) {
    const list = load()
    const i = list.findIndex((m) => m.uuid === uuid)
    if (i === -1) return null
    list[i] = { ...list[i], ...updates }
    save(list)
    return list[i]
  },

  remove(uuid, hard) {
    let list = load()
    if (hard) {
      list = list.filter((m) => m.uuid !== uuid)
    } else {
      const i = list.findIndex((m) => m.uuid === uuid)
      if (i !== -1) list[i] = { ...list[i], is_sensitive: true }
    }
    save(list)
    return { success: true }
  },

  stats(patientId) {
    const items = load().filter((m) => m.patient_id === patientId)
    const emotions = {}
    const topics = {}
    for (const m of items) {
      emotions[m.emotion] = (emotions[m.emotion] || 0) + 1
      topics[m.topic] = (topics[m.topic] || 0) + 1
    }
    return { total_memories: items.length, emotions, topics }
  },

  metadata() {
    return { topics: TOPICS, emotions: EMOTIONS, sources: SOURCES }
  },
}
