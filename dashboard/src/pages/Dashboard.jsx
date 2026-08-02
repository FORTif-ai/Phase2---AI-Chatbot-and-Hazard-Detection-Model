import { useEffect, useState } from 'react'
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

  useEffect(() => {
    const sections = document.querySelectorAll('.dashboard-home .scroll-fade')
    if (!sections.length) return undefined

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.15) {
            entry.target.classList.add('is-visible')
          } else {
            entry.target.classList.remove('is-visible')
          }
        })
      },
      {
        threshold: [0.15, 0.35, 0.65],
      }
    )

    sections.forEach((section) => {
      section.classList.add('scroll-fade-ready')
      observer.observe(section)
    })

    return () => observer.disconnect()
  }, [stats])

  return (
    <div className="dashboard dashboard-home">
      <header className="home-hero scroll-fade is-visible" aria-labelledby="home-main-title">
        <div className="home-hero-inner">
          <span className="home-badge">✦ AI-Powered Care</span>
          <h1 id="home-main-title" className="home-title">
            Fortif.ai <span className="home-title-accent">Senior Assistant</span>
          </h1>
          <p className="home-lead">
            Check memory summaries, recent moments, suggestions and quality hazard detection to
            prevent injury, stay happy and healthy.
          </p>
          <div className="home-hero-actions" role="navigation" aria-label="Quick pages">
            <Link to="/memories" className="home-hero-link">
              Browse memories
            </Link>
            <span className="home-hero-actions-sep" aria-hidden>
              ·
            </span>
            <Link to="/voice" className="home-hero-link">
              Voice commands
            </Link>
          </div>
        </div>
      </header>

      <section className="home-image-strip scroll-fade is-visible" aria-label="Senior lifestyle banner">
        <img
          src="/senior-assistant-banner.png"
          alt="Seniors in home and community settings"
          className="home-image-strip-img"
        />
      </section>

      <section className="patient-selector home-panel scroll-fade is-visible" aria-label="Load patient data">
        <h2 className="home-panel-title">Load a patient dashboard</h2>
        <p className="home-panel-hint">Enter patient ID, then load statistics and recent memories</p>
        <form onSubmit={handleSubmit} className="patient-form">
          <div className="form-group patient-form-group">
            <label htmlFor="patientId">Patient ID</label>
            <div className="input-group">
              <input
                type="text"
                id="patientId"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g. patient_123"
                autoComplete="off"
              />
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Loading…' : 'Load'}
              </button>
            </div>
          </div>
        </form>
      </section>

      {error && (
        <div className="error-alert" role="alert">
          {error}
        </div>
      )}

      {stats && (
        <div className="home-results">
          <h2 className="visually-hidden">Dashboard results</h2>
          <div className="stats-grid scroll-fade is-visible">
            <div className="stat-card stat-card--blue">
              <h3>Total memories</h3>
              <p className="stat-value">{stats.total_memories}</p>
            </div>

            <div className="stat-card stat-card--maroon">
              <h3>Positive memories</h3>
              <p className="stat-value stat-value--positive">{stats.emotions?.positive || 0}</p>
            </div>

            <div className="stat-card stat-card--blue">
              <h3>Daily routines</h3>
              <p className="stat-value">{stats.topics?.daily_routine || 0}</p>
            </div>

            <div className="stat-card stat-card--blue">
              <h3>Family history</h3>
              <p className="stat-value">{stats.topics?.family_history || 0}</p>
            </div>
          </div>

          <div className="dashboard-section scroll-fade is-visible">
            <div className="section-header">
              <h2>Topics</h2>
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

          <div className="dashboard-section scroll-fade is-visible">
            <div className="section-header">
              <h2>Emotions</h2>
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

          <div className="dashboard-section scroll-fade is-visible">
            <div className="section-header">
              <h2>Recent memories</h2>
              <Link to={`/memories?patient=${patientId}`} className="btn btn-outline btn-maroon-outline">
                View all
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
                    <Link to={`/memories/${memory.uuid}`} className="btn btn-sm btn-secondary-soft">
                      View
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No memories found for this patient.</p>
            )}
          </div>
        </div>
      )}

      {!stats && !loading && !error && (
        <div className="empty-state home-empty">
          <h2>Start with a patient ID</h2>
          <p>Use the form above to load that person’s memory overview.</p>
        </div>
      )}
    </div>
  )
}

export default Dashboard
