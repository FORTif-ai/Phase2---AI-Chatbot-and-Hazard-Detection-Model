import { useState, useRef, useEffect } from 'react';
import { voiceApi } from '../api/voiceClient';
import './VoiceCommand.css';

function VoiceCommand() {
  const [patientId, setPatientId] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [hazardMode, setHazardMode] = useState('directory');
  const [hazardImageFilename, setHazardImageFilename] = useState('image.png');
  const [hazardVideoFilename, setHazardVideoFilename] = useState('messyPath.mp4');
  const [hazardZipFilename, setHazardZipFilename] = useState('hallway_images.zip');
  const [hazardImageDir, setHazardImageDir] = useState('test_images');
  const [hazardOutputFile, setHazardOutputFile] = useState('testing_documentation/hallway_images.txt');
  const [hazardPollInterval, setHazardPollInterval] = useState('4.0');
  const [isRunningHazardDetection, setIsRunningHazardDetection] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  // Load patient ID from localStorage on mount
  useEffect(() => {
    const savedPatientId = localStorage.getItem('fortifai_patient_id');
    if (savedPatientId) {
      setPatientId(savedPatientId);
    }
  }, []);

  // Save patient ID to localStorage when it changes
  useEffect(() => {
    if (patientId) {
      localStorage.setItem('fortifai_patient_id', patientId);
    }
  }, [patientId]);

  const startRecording = async () => {
    if (!patientId) {
      setError('Please enter a Patient ID first');
      return;
    }

    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob) => {
    if (!patientId) {
      setError('Patient ID is required');
      return;
    }

    setIsProcessing(true);
    setError('');
    setTranscription('');
    setResponse('');

    try {
      // Convert audio blob to WAV format if needed, or send as-is
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('patient_id', patientId);

      const result = await voiceApi.processVoice(formData);

      if (result.success) {
        setTranscription(result.transcription || '');
        setResponse(result.response || '');
        
        // Add to conversation history
        setConversationHistory(prev => [
          ...prev,
          {
            id: Date.now(),
            type: 'user',
            text: result.transcription || '',
            timestamp: new Date()
          },
          {
            id: Date.now() + 1,
            type: 'assistant',
            text: result.response || '',
            timestamp: new Date()
          }
        ]);
      } else {
        setError(result.error || 'Failed to process voice command');
      }
    } catch (err) {
      console.error('Error processing audio:', err);
      setError(err.response?.data?.error || err.message || 'Failed to process audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!textInput.trim() || !patientId) {
      setError('Please enter text and Patient ID');
      return;
    }

    setIsProcessing(true);
    setError('');
    setResponse('');

    try {
      const result = await voiceApi.processText(textInput, patientId);

      if (result.success) {
        setResponse(result.response || '');
        
        // Add to conversation history
        setConversationHistory(prev => [
          ...prev,
          {
            id: Date.now(),
            type: 'user',
            text: textInput,
            timestamp: new Date()
          },
          {
            id: Date.now() + 1,
            type: 'assistant',
            text: result.response || '',
            timestamp: new Date()
          }
        ]);
        
        setTextInput('');
      } else {
        setError(result.error || 'Failed to process text command');
      }
    } catch (err) {
      console.error('Error processing text:', err);
      setError(err.response?.data?.error || err.message || 'Failed to process text');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearHistory = () => {
    setConversationHistory([]);
    setTranscription('');
    setResponse('');
    setError('');
  };

  const runHazardDetection = async () => {
    setIsRunningHazardDetection(true);
    setError('');

    // Build options based on selected mode
    const options = {};
    if (hazardMode === 'image') {
      options.imageFilename = hazardImageFilename;
    } else if (hazardMode === 'video') {
      options.videoFilename = hazardVideoFilename;
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0;
    } else if (hazardMode === 'batch') {
      options.zipFilename = hazardZipFilename;
      options.outputFile = hazardOutputFile;
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0;
    } else if (hazardMode === 'directory') {
      options.imageDir = hazardImageDir;
      options.outputFile = hazardOutputFile;
      options.pollInterval = parseFloat(hazardPollInterval) || 4.0;
    }

    try {
      // Add user message to conversation
      const userMsgId = Date.now();
      setConversationHistory(prev => [
        ...prev,
        {
          id: userMsgId,
          type: 'user',
          text: `Run hazard detection in ${hazardMode} mode`,
          timestamp: new Date()
        }
      ]);

      const result = await voiceApi.triggerHazardDetection(hazardMode, options);

      if (result.success) {
        // Add assistant response to conversation with images
        const assistantMsgId = Date.now() + 1;
        const message = {
          id: assistantMsgId,
          type: 'assistant',
          text: result.message + (result.output ? `\n\nOutput:\n${result.output}` : ''),
          timestamp: new Date(),
          images: result.images || null
        };
        setConversationHistory(prev => [...prev, message]);
        setResponse(result.message + (result.output ? `\n\nOutput:\n${result.output}` : ''));
      } else {
        setError(result.error || 'Failed to run hazard detection');
        // Add error message to conversation
        const assistantMsgId = Date.now() + 1;
        setConversationHistory(prev => [
          ...prev,
          {
            id: assistantMsgId,
            type: 'assistant',
            text: `Error: ${result.error || 'Failed to run hazard detection'}`,
            timestamp: new Date()
          }
        ]);
      }
    } catch (err) {
      console.error('Error running hazard detection:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Failed to run hazard detection';
      setError(errorMsg);
      // Add error message to conversation
      const assistantMsgId = Date.now() + 1;
      setConversationHistory(prev => [
        ...prev,
        {
          id: assistantMsgId,
          type: 'assistant',
          text: `Error: ${errorMsg}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsRunningHazardDetection(false);
    }
  };

  return (
    <div className="voice-command-container">
      <div className="voice-command-header">
        <h1>🎤 Fortif.ai Voice Command Interface</h1>
        <p>Interact with the AI chatbot using voice or text commands</p>
      </div>

      <div className="voice-command-content">
        {/* Patient ID Input */}
        <div className="patient-id-section">
          <label htmlFor="patient-id">Patient ID:</label>
          <input
            id="patient-id"
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter Patient ID (e.g., patient_123)"
            className="patient-id-input"
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {/* Voice Recording Section */}
        <div className="voice-section">
          <h2>Voice Commands</h2>
          <div className="recording-controls">
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isProcessing || !patientId}
                className="record-button start"
              >
                🎤 Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="record-button stop"
              >
                ⏹️ Stop Recording
              </button>
            )}
          </div>

          {isRecording && (
            <div className="recording-indicator">
              <span className="pulse"></span>
              Recording... Speak now
            </div>
          )}

          {transcription && (
            <div className="transcription">
              <strong>You said:</strong> {transcription}
            </div>
          )}
        </div>

        {/* Text Input Section */}
        <div className="text-section">
          <h2>Text Commands</h2>
          <form onSubmit={handleTextSubmit} className="text-form">
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your command here..."
              rows="3"
              className="text-input"
              disabled={isProcessing || !patientId}
            />
            <button
              type="submit"
              disabled={isProcessing || !textInput.trim() || !patientId}
              className="submit-button"
            >
              Send
            </button>
          </form>
        </div>

        {/* Hazard Detection Section */}
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

            {/* Mode-specific inputs */}
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
              {isRunningHazardDetection ? '🔄 Running...' : '🚨 Run Hazard Detection'}
            </button>
          </div>
        </div>

        {/* Response Display */}
        {response && (
          <div className="response-section">
            <h3>Response:</h3>
            <div className="response-content">{response}</div>
          </div>
        )}

        {/* Processing Indicator */}
        {(isProcessing || isRunningHazardDetection) && (
          <div className="processing-indicator">
            <div className="spinner"></div>
            {isRunningHazardDetection ? 'Running hazard detection...' : 'Processing...'}
          </div>
        )}

        {/* Conversation History */}
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
                <div key={msg.id} className={`history-message ${msg.type}`}>
                  <div className="message-header">
                    <strong>{msg.type === 'user' ? 'You' : 'Assistant'}</strong>
                    <span className="timestamp">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="message-text">{msg.text}</div>
                  
                  {/* Display images if available */}
                  {msg.images && msg.images.length > 0 && (
                    <div className="message-images">
                      <h4>Hazard Detection Results:</h4>
                      {msg.images.map((img, idx) => (
                        <div key={idx} className="image-result-card">
                          {img.image_url && (
                            <div className="image-container">
                              <img 
                                src={img.image_url} 
                                alt={img.image_filename || `Image ${idx + 1}`}
                                className="result-image"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'block';
                                }}
                              />
                              <div className="image-error" style={{ display: 'none' }}>
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
                                <div>People Detected: {img.result.people_detected ? 'Yes' : 'No'}</div>
                                <div>Hazard Detected: {img.result.hazard_detected ? 'Yes' : 'No'}</div>
                                {img.result.hazards && img.result.hazards.length > 0 && (
                                  <div className="hazards-list">
                                    <strong>Hazards ({img.result.hazards.length}):</strong>
                                    {img.result.hazards.map((hazard, hIdx) => (
                                      <div key={hIdx} className="hazard-item">
                                        <span className="hazard-type">{hazard.type}</span> - 
                                        <span className="hazard-severity"> {hazard.severity}</span>
                                        <div className="hazard-location">Location: {hazard.location}</div>
                                        {hazard.details && (
                                          <div className="hazard-details">{hazard.details}</div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                                {img.result.summary && (
                                  <div className="hazard-summary">Summary: {img.result.summary}</div>
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
  );
}

export default VoiceCommand;
