import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { memoryApi } from '../api/client'

function Dashboard() {
  const [patientId, setPatientId] = useState('')
  const [stats, setStats] = useState(null)
  const [recentMemories, setRecentMemories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadDashboard = async () => {
    if (!patientId.trim()) return

    setLoading(true)
    setError('')

    try {
      const [statsData, memoriesData] = await Promise.all([
        memoryApi.getStats(patientId),
        memoryApi.listMemories(patientId, { per_page: 5 }),
      ])

      setStats(statsData)
      setRecentMemories(memoriesData.memories)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    loadDashboard()
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>View memory statistics and recent activity</p>
      </div>

      <div className="patient-selector">
        <form onSubmit={handleSubmit} className="patient-form">
          <div className="form-group">
            <label htmlFor="patientId">Patient ID</label>
            <div className="input-group">
              <input
                type="text"
                id="patientId"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="Enter patient ID (e.g., patient_123)"
              />
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Loading...' : 'Load'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {error && <div className="error-alert">{error}</div>}

      {stats && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Memories</h3>
              <p className="stat-value">{stats.total_memories}</p>
            </div>

            <div className="stat-card">
              <h3>Positive Memories</h3>
              <p className="stat-value positive">{stats.emotions?.positive || 0}</p>
            </div>

            <div className="stat-card">
              <h3>Daily Routines</h3>
              <p className="stat-value">{stats.topics?.daily_routine || 0}</p>
            </div>

            <div className="stat-card">
              <h3>Family History</h3>
              <p className="stat-value">{stats.topics?.family_history || 0}</p>
            </div>
          </div>

          <div className="dashboard-section">
            <div className="section-header">
              <h2>Topics Distribution</h2>
            </div>
            <div className="topics-grid">
              {Object.entries(stats.topics || {}).map(([topic, count]) => (
                <div key={topic} className="topic-item">
                  <span className="topic-name">{topic.replace(/_/g, ' ')}</span>
                  <span className="topic-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-section">
            <div className="section-header">
              <h2>Emotions Distribution</h2>
            </div>
            <div className="emotions-grid">
              {Object.entries(stats.emotions || {}).map(([emotion, count]) => (
                <div key={emotion} className={`emotion-item emotion-${emotion}`}>
                  <span className="emotion-name">{emotion}</span>
                  <span className="emotion-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-section">
            <div className="section-header">
              <h2>Recent Memories</h2>
              <Link to={`/memories?patient=${patientId}`} className="btn btn-outline">
                View All
              </Link>
            </div>

            {recentMemories.length > 0 ? (
              <div className="recent-memories">
                {recentMemories.map((memory) => (
                  <div key={memory.uuid} className="recent-memory-item">
                    <div className="memory-preview">
                      <span className={`emotion-dot emotion-${memory.emotion}`}></span>
                      <p>{memory.text.substring(0, 100)}...</p>
                    </div>
                    <Link to={`/memories/${memory.uuid}`} className="btn btn-sm">
                      View
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No memories found for this patient.</p>
            )}
          </div>
        </>
      )}

      {!stats && !loading && !error && (
        <div className="empty-state">
          <h2>Enter a Patient ID</h2>
          <p>Enter a patient ID above to view their memory dashboard.</p>
        </div>
      )}
    </div>
  )
}

export default Dashboard
