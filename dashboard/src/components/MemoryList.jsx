import MemoryCard from './MemoryCard'

function MemoryList({ memories, loading, error }) {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading memories...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
      </div>
    )
  }

  if (!memories || memories.length === 0) {
    return (
      <div className="empty-container">
        <p>No memories found.</p>
      </div>
    )
  }

  return (
    <div className="memory-list">
      {memories.map((memory) => (
        <MemoryCard key={memory.uuid} memory={memory} />
      ))}
    </div>
  )
}

export default MemoryList
