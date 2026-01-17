import requests
import os

# Configuration
API_URL = "http://localhost:8000/api/voice-query"
API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")  # Set OPENAI_API_KEY env var
AUDIO_FILE = "captured.wav"
PATIENT_ID = "patient_123"

def test_voice_query():
    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file '{AUDIO_FILE}' not found.")
        return

    print(f"Testing voice query with {AUDIO_FILE}...")

    headers = {
        "X-API-Key": API_KEY
    }

    data = {
        "patient_id": PATIENT_ID,
        "limit": 3
    }

    files = {
        "file": (AUDIO_FILE, open(AUDIO_FILE, "rb"), "audio/wav")
    }

    try:
        response = requests.post(API_URL, headers=headers, data=data, files=files)
        
        if response.status_code == 200:
            print("\n✅ Success!")
            result = response.json()
            print(f"Transcription: {result['metadata'].get('transcription')}")
            print(f"Response: {result['response']}")
            print(f"Sources: {len(result['sources'])}")
        else:
            print(f"\n❌ Failed with status {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_voice_query()
