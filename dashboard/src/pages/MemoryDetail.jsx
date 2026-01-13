import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { memoryApi } from '../api/client'

function MemoryDetail() {
  const { uuid } = useParams()
  const navigate = useNavigate()

  const [memory, setMemory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Edit mode
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState('')
  const [editTopic, setEditTopic] = useState('')
  const [editEmotion, setEditEmotion] = useState('')
  const [editSensitive, setEditSensitive] = useState(false)

  // Metadata
  const [topics, setTopics] = useState([])
  const [emotions, setEmotions] = useState([])

  useEffect(() => {
    const loadData = async () => {
      try {
        const [memoryData, topicsData, emotionsData] = await Promise.all([
          memoryApi.getMemory(uuid),
          memoryApi.getTopics(),
          memoryApi.getEmotions(),
        ])

        setMemory(memoryData)
        setTopics(topicsData)
        setEmotions(emotionsData)

        // Initialize edit fields
        setEditText(memoryData.text)
        setEditTopic(memoryData.topic)
        setEditEmotion(memoryData.emotion)
        setEditSensitive(memoryData.is_sensitive)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load memory')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [uuid])

  const handleSave = async () => {
    setSaving(true)
    setError('')

    try {
      const updates = {
        text: editText,
        topic: editTopic,
        emotion: editEmotion,
        is_sensitive: editSensitive,
      }

      const updated = await memoryApi.updateMemory(uuid, updates)
      setMemory(updated)
      setIsEditing(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (hardDelete = false) => {
    const confirmMessage = hardDelete
      ? 'Are you sure you want to permanently delete this memory? This cannot be undone.'
      : 'Are you sure you want to hide this memory? It will be marked as sensitive.'

    if (!window.confirm(confirmMessage)) return

    setDeleting(true)
    setError('')

    try {
      await memoryApi.deleteMemory(uuid, hardDelete)
      navigate('/memories')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete memory')
      setDeleting(false)
    }
  }

  const cancelEdit = () => {
    setEditText(memory.text)
    setEditTopic(memory.topic)
    setEditEmotion(memory.emotion)
    setEditSensitive(memory.is_sensitive)
    setIsEditing(false)
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading memory...</p>
      </div>
    )
  }

  if (!memory) {
    return (
      <div className="error-container">
        <h2>Memory Not Found</h2>
        <p>{error || 'The requested memory could not be found.'}</p>
        <button onClick={() => navigate('/memories')} className="btn btn-primary">
          Back to Memories
        </button>
      </div>
    )
  }

  // Allow all users to edit and delete in simplified mode
  const canEdit = true
  const canHardDelete = true

  return (
    <div className="memory-detail">
      <div className="page-header">
        <button onClick={() => navigate(-1)} className="btn btn-outline">
          Back
        </button>
        <h1>Memory Details</h1>
      </div>

      {error && <div className="error-alert">{error}</div>}

      <div className="memory-detail-card">
        <div className="detail-header">
          <div className="detail-badges">
            <span className={`emotion-badge emotion-${memory.emotion}`}>
              {memory.emotion}
            </span>
            <span className="topic-badge">{memory.topic}</span>
            {memory.is_sensitive && <span className="sensitive-badge">Sensitive</span>}
          </div>

          {canEdit && !isEditing && (
            <div className="detail-actions">
              <button onClick={() => setIsEditing(true)} className="btn btn-primary">
                Edit
              </button>
              <button
                onClick={() => handleDelete(false)}
                className="btn btn-warning"
                disabled={deleting}
              >
                Hide
              </button>
              {canHardDelete && (
                <button
                  onClick={() => handleDelete(true)}
                  className="btn btn-danger"
                  disabled={deleting}
                >
                  Delete
                </button>
              )}
            </div>
          )}
        </div>

        {isEditing ? (
          <div className="edit-form">
            <div className="form-group">
              <label htmlFor="editText">Memory Text</label>
              <textarea
                id="editText"
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={6}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="editTopic">Topic</label>
                <select
                  id="editTopic"
                  value={editTopic}
                  onChange={(e) => setEditTopic(e.target.value)}
                >
                  {topics.map((topic) => (
                    <option key={topic} value={topic}>
                      {topic.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="editEmotion">Emotion</label>
                <select
                  id="editEmotion"
                  value={editEmotion}
                  onChange={(e) => setEditEmotion(e.target.value)}
                >
                  {emotions.map((emotion) => (
                    <option key={emotion} value={emotion}>
                      {emotion}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={editSensitive}
                  onChange={(e) => setEditSensitive(e.target.checked)}
                />
                Mark as Sensitive
              </label>
            </div>

            <div className="button-row">
              <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button onClick={cancelEdit} className="btn btn-outline" disabled={saving}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="memory-content-detail">
            <p>{memory.text}</p>
          </div>
        )}

        <div className="detail-metadata">
          <div className="metadata-item">
            <strong>Patient ID:</strong> {memory.patient_id}
          </div>
          <div className="metadata-item">
            <strong>Source:</strong> {memory.source}
          </div>
          <div className="metadata-item">
            <strong>Entities:</strong> {memory.entities?.join(', ') || 'None'}
          </div>
          <div className="metadata-item">
            <strong>Chunk:</strong> {memory.chunk_index + 1} of {memory.total_chunks}
          </div>
          <div className="metadata-item">
            <strong>Created:</strong>{' '}
            {memory.ingested_at
              ? new Date(memory.ingested_at).toLocaleString()
              : 'Unknown'}
          </div>
          <div className="metadata-item">
            <strong>UUID:</strong> <code>{memory.uuid}</code>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MemoryDetail
