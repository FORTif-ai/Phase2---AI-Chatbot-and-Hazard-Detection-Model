import { useState } from 'react'
import { voiceApi } from '../api/voiceClient'
import './VoiceCommand.css'

function HazardDetector() {
  const [hazardMode, setHazardMode] = useState('directory')
  const [hazardImageFilename, setHazardImageFilename] = useState('image.png')
  const [hazardVideoFilename, setHazardVideoFilename] = useState('messyPath.mp4')
  const [hazardZipFilename, setHazardZipFilename] = useState('hallway_images.zip')
  const [hazardImageDir, setHazardImageDir] = useState('test_images')
  const [hazardOutputFile, setHazardOutputFile] = useState(
    'testing_documentation/hallway_images.txt'
  )
  const [hazardPollInterval, setHazardPollInterval] = useState('4.0')
  const [isRunningHazardDetection, setIsRunningHazardDetection] = useState(false)

  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [conversationHistory, setConversationHistory] = useState([])

  const clearHistory = () => {
    setConversationHistory([])
    setResponse('')
    setError('')
  }

  const runHazardDetection = async () => {
    setIsRunningHazardDetection(true)
    setError('')

    const options = {}
    if (hazardMode === 'image') {
      options.imageFilename = hazardImageFilename
    } else if (hazardMode === 'video') {
      options.videoFilename = hazardVideoFilename
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0
    } else if (hazardMode === 'batch') {
      options.zipFilename = hazardZipFilename
      options.outputFile = hazardOutputFile
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0
    } else if (hazardMode === 'directory') {
      options.imageDir = hazardImageDir
      options.outputFile = hazardOutputFile
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0
    }

    try {
      const userMsgId = Date.now()
      setConversationHistory((prev) => [
        ...prev,
        {
          id: userMsgId,
          type: 'user',
          text: `Run hazard detection in ${hazardMode} mode`,
          timestamp: new Date(),
        },
      ])

      const result = await voiceApi.triggerHazardDetection(hazardMode, options)

      if (result.success) {
        const assistantMsgId = Date.now() + 1
        const message = {
          id: assistantMsgId,
          type: 'assistant',
          text:
            result.message +
            (result.output ? `\n\nOutput:\n${result.output}` : ''),
          timestamp: new Date(),
          images: result.images || null,
        }

        setConversationHistory((prev) => [...prev, message])
        setResponse(
          result.message + (result.output ? `\n\nOutput:\n${result.output}` : '')
        )
      } else {
        const hazardError = result.error || 'Failed to run hazard detection'
        setError(hazardError)

        const assistantMsgId = Date.now() + 1
        setConversationHistory((prev) => [
          ...prev,
          {
            id: assistantMsgId,
            type: 'assistant',
            text: `Error: ${hazardError}`,
            timestamp: new Date(),
          },
        ])
      }
    } catch (err) {
      console.error('Error running hazard detection:', err)
      const errorMsg =
        err.response?.data?.error || err.message || 'Failed to run hazard detection'
      setError(errorMsg)

      const assistantMsgId = Date.now() + 1
      setConversationHistory((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          type: 'assistant',
          text: `Error: ${errorMsg}`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsRunningHazardDetection(false)
    }
  }

  return (
    <div className="voice-command-container">
      <div className="voice-command-header">
        <h1>Hazard Detector</h1>
        <p>Run hazard detection on images, videos, or batches</p>
      </div>

      <div className="voice-command-content">
        {error && (
          <div className="error-message" role="alert">
            ⚠️ {error}
          </div>
        )}

        <div className="hazard-detection-section">
          <h2>Hazard Detection</h2>
          <div className="hazard-controls">
            <div className="hazard-mode-selector">
              <label htmlFor="hazard-mode">Mode:</label>
              <select
                id="hazard-mode"
                value={hazardMode}
                onChange={(e) => setHazardMode(e.target.value)}
                className="mode-dropdown"
                disabled={isRunningHazardDetection}
              >
                <option value="image">Image - Single Image Analysis</option>
                <option value="video">Video - Video Analysis</option>
                <option value="batch">Batch - Process Zip File</option>
                <option value="directory">Directory - Process Directory</option>
              </select>
            </div>

            {hazardMode === 'image' && (
              <div className="hazard-input-group">
                <label htmlFor="hazard-image-filename">Image Filename:</label>
                <input
                  id="hazard-image-filename"
                  type="text"
                  value={hazardImageFilename}
                  onChange={(e) => setHazardImageFilename(e.target.value)}
                  placeholder="image.png"
                  className="hazard-input"
                  disabled={isRunningHazardDetection}
                />
              </div>
            )}

            {hazardMode === 'video' && (
              <>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-video-filename">Video Filename:</label>
                  <input
                    id="hazard-video-filename"
                    type="text"
                    value={hazardVideoFilename}
                    onChange={(e) => setHazardVideoFilename(e.target.value)}
                    placeholder="messyPath.mp4"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-poll-interval">Poll Interval (seconds):</label>
                  <input
                    id="hazard-poll-interval"
                    type="number"
                    value={hazardPollInterval}
                    onChange={(e) => setHazardPollInterval(e.target.value)}
                    placeholder="4.0"
                    step="0.1"
                    min="1"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
              </>
            )}

            {hazardMode === 'batch' && (
              <>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-zip-filename">Zip Filename:</label>
                  <input
                    id="hazard-zip-filename"
                    type="text"
                    value={hazardZipFilename}
                    onChange={(e) => setHazardZipFilename(e.target.value)}
                    placeholder="hallway_images.zip"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-output-file">Output File:</label>
                  <input
                    id="hazard-output-file"
                    type="text"
                    value={hazardOutputFile}
                    onChange={(e) => setHazardOutputFile(e.target.value)}
                    placeholder="testing_documentation/hallway_images.txt"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-poll-interval-batch">Poll Interval (seconds):</label>
                  <input
                    id="hazard-poll-interval-batch"
                    type="number"
                    value={hazardPollInterval}
                    onChange={(e) => setHazardPollInterval(e.target.value)}
                    placeholder="4.0"
                    step="0.1"
                    min="1"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
              </>
            )}

            {hazardMode === 'directory' && (
              <>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-image-dir">Image Directory:</label>
                  <input
                    id="hazard-image-dir"
                    type="text"
                    value={hazardImageDir}
                    onChange={(e) => setHazardImageDir(e.target.value)}
                    placeholder="test_images"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-output-file-dir">Output File:</label>
                  <input
                    id="hazard-output-file-dir"
                    type="text"
                    value={hazardOutputFile}
                    onChange={(e) => setHazardOutputFile(e.target.value)}
                    placeholder="testing_documentation/hallway_images.txt"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
                <div className="hazard-input-group">
                  <label htmlFor="hazard-poll-interval-dir">Poll Interval (seconds):</label>
                  <input
                    id="hazard-poll-interval-dir"
                    type="number"
                    value={hazardPollInterval}
                    onChange={(e) => setHazardPollInterval(e.target.value)}
                    placeholder="4.0"
                    step="0.1"
                    min="1"
                    className="hazard-input"
                    disabled={isRunningHazardDetection}
                  />
                </div>
              </>
            )}

            <button
              onClick={runHazardDetection}
              disabled={isRunningHazardDetection}
              className="hazard-button"
            >
              {isRunningHazardDetection ? (
                'Running...'
              ) : (
                <>
                  <img
                    src="/hazard-warning-icon.png"
                    alt=""
                    aria-hidden="true"
                    className="hazard-button-icon"
                  />
                  <span>Run Hazard Detection</span>
                </>
              )}
            </button>
          </div>
        </div>

        {response && (
          <div className="response-section">
            <h3>Response:</h3>
            <div className="response-content">{response}</div>
          </div>
        )}

        {isRunningHazardDetection && (
          <div className="processing-indicator">
            <div className="spinner"></div>
            Running hazard detection...
          </div>
        )}

        {conversationHistory.length > 0 && (
          <div className="conversation-history">
            <div className="history-header">
              <h3>Conversation History</h3>
              <button onClick={clearHistory} className="clear-button">
                Clear
              </button>
            </div>
            <div className="history-content">
              {conversationHistory.map((msg) => (
                <div
                  key={msg.id}
                  className={`history-message ${msg.type}`}
                >
                  <div className="message-header">
                    <strong>{msg.type === 'user' ? 'You' : 'Assistant'}</strong>
                    <span className="timestamp">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="message-text">{msg.text}</div>

                  {msg.images && msg.images.length > 0 && (
                    <div className="message-images">
                      <h4>Hazard Detection Results:</h4>
                      {msg.images.map((img, idx) => (
                        <div
                          key={idx}
                          className="image-result-card"
                        >
                          {img.image_url && (
                            <div className="image-container">
                              <img
                                src={img.image_url}
                                alt={img.image_filename || `Image ${idx + 1}`}
                                className="result-image"
                                onError={(e) => {
                                  e.target.style.display = 'none'
                                  // eslint-disable-next-line no-param-reassign
                                  e.target.nextSibling.style.display = 'block'
                                }}
                              />
                              <div
                                className="image-error"
                                style={{ display: 'none' }}
                              >
                                Image not available: {img.image_filename || 'Unknown'}
                              </div>
                            </div>
                          )}

                          <div className="image-result-info">
                            <strong>Image: {img.image_filename || 'Unknown'}</strong>
                            {img.error ? (
                              <div className="image-error-text">Error: {img.error}</div>
                            ) : img.result ? (
                              <div className="hazard-result-details">
                                <div>
                                  People Detected: {img.result.people_detected ? 'Yes' : 'No'}
                                </div>
                                <div>
                                  Hazard Detected: {img.result.hazard_detected ? 'Yes' : 'No'}
                                </div>
                                {img.result.hazards &&
                                  img.result.hazards.length > 0 && (
                                    <div className="hazards-list">
                                      <strong>Hazards ({img.result.hazards.length}):</strong>
                                      {img.result.hazards.map((hazard, hIdx) => (
                                        <div
                                          key={hIdx}
                                          className="hazard-item"
                                        >
                                          <span className="hazard-type">{hazard.type}</span> -{' '}
                                          <span className="hazard-severity">
                                            {hazard.severity}
                                          </span>
                                          <div className="hazard-location">
                                            Location: {hazard.location}
                                          </div>
                                          {hazard.details && (
                                            <div className="hazard-details">
                                              {hazard.details}
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                {img.result.summary && (
                                  <div className="hazard-summary">
                                    Summary: {img.result.summary}
                                  </div>
                                )}
                              </div>
                            ) : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default HazardDetector

