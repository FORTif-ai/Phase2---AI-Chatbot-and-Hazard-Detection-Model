import { useState, useRef, useEffect } from 'react';
import { voiceApi } from '../api/voiceClient';
import './VoiceCommand.css';

// In the free demo, voice uses the browser's built-in Web Speech API (no Whisper backend).
const DEMO = import.meta.env.VITE_DEMO_MODE === 'true';

function VoiceCommand() {
  const [patientId, setPatientId] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [textInput, setTextInput] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const recognitionRef = useRef(null);

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

    // Demo: transcribe in the browser with the free Web Speech API.
    if (DEMO) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        setError(
          'Voice input needs the Web Speech API (try Chrome or Edge). You can type a command instead.'
        );
        return;
      }
      try {
        setError('');
        setTranscription('');
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          setTranscription(transcript);
          submitText(transcript);
        };
        recognition.onerror = (event) => {
          setError(
            event.error === 'no-speech'
              ? "I didn't catch that — please try again."
              : `Voice error: ${event.error}`
          );
        };
        recognition.onend = () => setIsRecording(false);
        recognitionRef.current = recognition;
        recognition.start();
        setIsRecording(true);
      } catch (err) {
        console.error('Web Speech error:', err);
        setError('Could not start voice input. You can type a command instead.');
      }
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
    if (DEMO) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Shared: send a text command through the chat pipeline and record it in history.
  const submitText = async (text) => {
    const trimmed = (text || '').trim();
    if (!trimmed || !patientId) {
      setError('Please enter text and Patient ID');
      return;
    }

    setIsProcessing(true);
    setError('');
    setResponse('');

    try {
      const result = await voiceApi.processText(trimmed, patientId);
      if (result.success) {
        setResponse(result.response || '');
        setConversationHistory((prev) => [
          ...prev,
          { id: Date.now(), type: 'user', text: trimmed, timestamp: new Date() },
          { id: Date.now() + 1, type: 'assistant', text: result.response || '', timestamp: new Date() },
        ]);
      } else {
        setError(result.error || 'Failed to process command');
      }
    } catch (err) {
      console.error('Error processing text:', err);
      setError(err.response?.data?.error || err.message || 'Failed to process command');
    } finally {
      setIsProcessing(false);
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
    const text = textInput;
    setTextInput('');
    await submitText(text);
  };

  const clearHistory = () => {
    setConversationHistory([]);
    setTranscription('');
    setResponse('');
    setError('');
  };

  return (
    <div className="voice-command-container">
      <div className="voice-command-header">
        <h1>Voice Command Interface</h1>
        <p>Interact with our Fortif.ai Bot using voice or text commands</p>
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
                <span className="record-button-icon" aria-hidden="true">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M12 14c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v5c0 1.66 1.34 3 3 3Z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M19 11v1a7 7 0 0 1-14 0v-1"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M12 19v3"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
                <span>Start Recording</span>
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

        {/* Response Display */}
        {response && (
          <div className="response-section">
            <h3>Response:</h3>
            <div className="response-content">{response}</div>
          </div>
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="processing-indicator">
            <div className="spinner"></div>
            Processing...
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
