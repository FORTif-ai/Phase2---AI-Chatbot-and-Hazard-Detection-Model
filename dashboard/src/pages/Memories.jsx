import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { memoryApi } from '../api/client'
import MemoryList from '../components/MemoryList'

function Memories() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [patientId, setPatientId] = useState(searchParams.get('patient') || '')
  const [memories, setMemories] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Filters
  const [topicFilter, setTopicFilter] = useState('')
  const [emotionFilter, setEmotionFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [includeSensitive, setIncludeSensitive] = useState(false)

  // Metadata options
  const [topics, setTopics] = useState([])
  const [emotions, setEmotions] = useState([])
  const [sources, setSources] = useState([])

  useEffect(() => {
    // Load metadata options
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
      }
    }
    loadMetadata()
  }, [])

  const loadMemories = async (resetPage = false) => {
    if (!patientId.trim()) {
      setError('Please enter a patient ID')
      return
    }

    setLoading(true)
    setError('')

    const currentPage = resetPage ? 1 : page

    try {
      const params = {
        page: currentPage,
        per_page: 20,
        include_sensitive: includeSensitive,
      }

      if (topicFilter) params.topic = topicFilter
      if (emotionFilter) params.emotion = emotionFilter
      if (sourceFilter) params.source = sourceFilter
      if (searchQuery) params.search = searchQuery

      const data = await memoryApi.listMemories(patientId, params)

      setMemories(data.memories)
      setTotalCount(data.total_count)
      setHasMore(data.has_more)

      if (resetPage) setPage(1)

      // Update URL
      setSearchParams({ patient: patientId })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load memories')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    loadMemories(true)
  }

  const handlePageChange = (newPage) => {
    setPage(newPage)
  }

  useEffect(() => {
    if (patientId && page > 1) {
      loadMemories()
    }
  }, [page])

  const clearFilters = () => {
    setTopicFilter('')
    setEmotionFilter('')
    setSourceFilter('')
    setSearchQuery('')
    setIncludeSensitive(false)
  }

  return (
    <div className="memories-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Memories</h1>
          <p>Browse and manage patient memories</p>
        </div>
        <Link
          to={patientId ? `/memories/new?patient=${patientId}` : '/memories/new'}
          className="btn btn-primary"
        >
          + New Memory
        </Link>
      </div>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-row">
          <div className="form-group">
            <label htmlFor="patientId">Patient ID</label>
            <input
              type="text"
              id="patientId"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="Enter patient ID"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="search">Search</label>
            <input
              type="text"
              id="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories..."
            />
          </div>
        </div>

        <div className="filters-row">
          <div className="form-group">
            <label htmlFor="topic">Topic</label>
            <select
              id="topic"
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
            >
              <option value="">All Topics</option>
              {topics.map((topic) => (
                <option key={topic} value={topic}>
                  {topic.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="emotion">Emotion</label>
            <select
              id="emotion"
              value={emotionFilter}
              onChange={(e) => setEmotionFilter(e.target.value)}
            >
              <option value="">All Emotions</option>
              {emotions.map((emotion) => (
                <option key={emotion} value={emotion}>
                  {emotion}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="source">Source</label>
            <select
              id="source"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
            >
              <option value="">All Sources</option>
              {sources.map((source) => (
                <option key={source} value={source}>
                  {source.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={includeSensitive}
                onChange={(e) => setIncludeSensitive(e.target.checked)}
              />
              Include Sensitive
            </label>
          </div>
        </div>

        <div className="button-row">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button type="button" className="btn btn-outline" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>
      </form>

      {error && <div className="error-alert">{error}</div>}

      {memories.length > 0 && (
        <div className="results-header">
          <p>
            Showing {memories.length} of {totalCount} memories
          </p>
        </div>
      )}

      <MemoryList memories={memories} loading={loading} error={null} />

      {memories.length > 0 && (
        <div className="pagination">
          <button
            className="btn btn-outline"
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1 || loading}
          >
            Previous
          </button>
          <span className="page-info">Page {page}</span>
          <button
            className="btn btn-outline"
            onClick={() => handlePageChange(page + 1)}
            disabled={!hasMore || loading}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

export default Memories
