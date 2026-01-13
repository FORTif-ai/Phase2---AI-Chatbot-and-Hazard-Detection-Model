import { Link } from 'react-router-dom'

function MemoryCard({ memory }) {
  const emotionColors = {
    positive: '#4ade80',
    negative: '#f87171',
    neutral: '#94a3b8',
    mixed: '#fbbf24',
    unknown: '#6b7280',
  }

  return (
    <div className="memory-card">
      <div className="memory-header">
        <span
          className="emotion-badge"
          style={{ backgroundColor: emotionColors[memory.emotion] || '#6b7280' }}
        >
          {memory.emotion}
        </span>
        <span className="topic-badge">{memory.topic}</span>
        {memory.is_sensitive && <span className="sensitive-badge">Sensitive</span>}
      </div>

      <div className="memory-content">
        <p>{memory.text.length > 200 ? `${memory.text.substring(0, 200)}...` : memory.text}</p>
      </div>

      <div className="memory-footer">
        <span className="memory-source">Source: {memory.source}</span>
        <span className="memory-date">
          {memory.ingested_at ? new Date(memory.ingested_at).toLocaleDateString() : 'Unknown'}
        </span>
        <Link to={`/memories/${memory.uuid}`} className="btn btn-sm">
          View Details
        </Link>
      </div>
    </div>
  )
}

export default MemoryCard
