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

  const handleHazardDetection = async () => {
    setIsProcessing(true);
    setError('');

    try {
      const result = await voiceApi.triggerHazardDetection();
      if (result.success) {
        setResponse(`Hazard detection completed: ${result.message}`);
      } else {
        setError(result.error || 'Hazard detection failed');
      }
    } catch (err) {
      console.error('Error triggering hazard detection:', err);
      setError(err.response?.data?.error || err.message || 'Failed to trigger hazard detection');
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

        {/* Hazard Detection Button */}
        <div className="hazard-section">
          <button
            onClick={handleHazardDetection}
            disabled={isProcessing}
            className="hazard-button"
          >
            🚨 Run Hazard Detection
          </button>
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
