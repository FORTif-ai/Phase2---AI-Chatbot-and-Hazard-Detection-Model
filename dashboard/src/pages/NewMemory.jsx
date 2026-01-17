import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { memoryApi } from '../api/client'

function NewMemory() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Form fields
  const [patientId, setPatientId] = useState(searchParams.get('patient') || '')
  const [rawText, setRawText] = useState('')
  const [topic, setTopic] = useState('daily_routine')
  const [emotion, setEmotion] = useState('neutral')
  const [source, setSource] = useState('family_questionnaire')
  const [isSensitive, setIsSensitive] = useState(false)
  const [entitiesText, setEntitiesText] = useState('')

  // Metadata options
  const [topics, setTopics] = useState([])
  const [emotions, setEmotions] = useState([])
  const [sources, setSources] = useState([])

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [topicsData, emotionsData, sourcesData] = await Promise.all([
          memoryApi.getTopics(),
          memoryApi.getEmotions(),
          memoryApi.getSources(),
        ])
        setTopics(topicsData)
        setEmotions(emotionsData)
        setSources(sourcesData)
      } catch (err) {
        console.error('Failed to load metadata:', err)
        // Use defaults if metadata fails to load
        setTopics(['daily_routine', 'family_history', 'hobbies', 'health_info', 'preferences', 'positive_memory', 'career'])
        setEmotions(['positive', 'negative', 'neutral', 'mixed'])
        setSources(['family_questionnaire', 'caregiver_input', 'patient_conversation', 'medical_record'])
      }
    }
    loadMetadata()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!patientId.trim()) {
      setError('Patient ID is required')
      return
    }

    if (!rawText.trim()) {
      setError('Memory text is required')
      return
    }

    if (rawText.trim().length < 10) {
      setError('Memory text must be at least 10 characters')
      return
    }

    setSaving(true)

    try {
      // Parse entities from comma-separated text
      const entities = entitiesText
        .split(',')
        .map((e) => e.trim())
        .filter((e) => e.length > 0)

      const memoryData = {
        patient_id: patientId.trim(),
        raw_text: rawText.trim(),
        topic: topic,
        emotion: emotion,
        source: source,
        is_sensitive: isSensitive,
        entities: entities,
      }

      await memoryApi.createMemory(memoryData)

      setSuccess('Memory created successfully!')

      // Clear form
      setRawText('')
      setEntitiesText('')
      setIsSensitive(false)

      // Redirect after short delay
      setTimeout(() => {
        navigate(`/memories?patient=${patientId}`)
      }, 1500)
    } catch (err) {
      console.error('Error creating memory:', err)
      
      // Extract error message from various possible response formats
      let errorMessage = 'Failed to create memory'
      
      if (err.response) {
        // Try different possible error formats
        errorMessage = err.response.data?.detail || 
                      err.response.data?.error || 
                      err.response.data?.message ||
                      err.response.statusText ||
                      `Server error (${err.response.status})`
      } else if (err.request) {
        errorMessage = 'Unable to connect to server. Please check if the API server is running.'
      } else {
        errorMessage = err.message || 'An unexpected error occurred'
      }
      
      setError(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    if (patientId) {
      navigate(`/memories?patient=${patientId}`)
    } else {
      navigate('/memories')
    }
  }

  return (
    <div className="new-memory-page">
      <div className="page-header">
        <button onClick={handleCancel} className="btn btn-outline">
          Back
        </button>
        <h1>Add New Memory</h1>
      </div>

      {error && <div className="error-alert">{error}</div>}
      {success && <div className="success-alert">{success}</div>}

      <div className="memory-form-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="patientId">Patient ID *</label>
            <input
              type="text"
              id="patientId"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="e.g., patient_123"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="rawText">Memory Text *</label>
            <textarea
              id="rawText"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Describe the memory in detail. Include names, places, dates, and feelings..."
              rows={6}
              required
            />
            <small className="form-help">
              Write a detailed description of the memory. Longer text may be split into chunks automatically.
            </small>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="topic">Topic</label>
              <select
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              >
                {topics.map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="emotion">Emotion</label>
              <select
                id="emotion"
                value={emotion}
                onChange={(e) => setEmotion(e.target.value)}
              >
                {emotions.map((em) => (
                  <option key={em} value={em}>
                    {em}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="source">Source</label>
              <select
                id="source"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                {sources.map((s) => (
                  <option key={s} value={s}>
                    {s.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="entities">Entities (comma-separated)</label>
            <input
              type="text"
              id="entities"
              value={entitiesText}
              onChange={(e) => setEntitiesText(e.target.value)}
              placeholder="e.g., Robert, Earl Grey tea, garden, birds"
            />
            <small className="form-help">
              Names of people, places, objects, or other important things mentioned in the memory.
            </small>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={isSensitive}
                onChange={(e) => setIsSensitive(e.target.checked)}
              />
              Mark as Sensitive
            </label>
            <small className="form-help">
              Sensitive memories (health info, private details) are hidden by default.
            </small>
          </div>

          <div className="button-row">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Creating...' : 'Create Memory'}
            </button>
            <button type="button" className="btn btn-outline" onClick={handleCancel} disabled={saving}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default NewMemory
