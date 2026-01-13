# Fortif.ai Complete Setup Guide

This guide covers running the **entire** Fortif.ai system: Voice Assistant + RAG Chatbot + Memory Dashboard.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        FORTIF.AI SYSTEM                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Voice     │───▶│  Pipeline   │───▶│   RAG API Server    │  │
│  │   main.py   │    │ (Gemini LLM)│    │   (rag/main.py)     │  │
│  │  (sudo)     │    │             │    │   Port 8000         │  │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘  │
│        │                                          │              │
│        │                                          ▼              │
│        │                               ┌─────────────────────┐   │
│        │                               │     Weaviate        │   │
│        │                               │  (Vector Database)  │   │
│        │                               │   Port 8080/50051   │   │
│        │                               └─────────────────────┘   │
│        │                                          │              │
│        ▼                                          ▼              │
│  ┌─────────────┐                       ┌─────────────────────┐   │
│  │  Whisper    │                       │   Google Gemini     │   │
│  │  (Speech)   │                       │   (LLM + Embeddings)│   │
│  └─────────────┘                       └─────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Memory Dashboard (React)                    │    │
│  │              http://localhost:5173                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | How to Install |
|-------------|----------------|
| **Python 3.10+** | `brew install python@3.11` |
| **Docker Desktop** | Download from docker.com |
| **Node.js 18+** | `brew install node` |
| **Google AI API Key** | https://aistudio.google.com/app/apikey |
| **Microphone** | Built-in or external mic |

---

## Step-by-Step Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
```

---

### Step 2: Create Python Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate
```

---

### Step 3: Install Python Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install RAG dependencies
pip install -r rag/requirements.txt
```

---

### Step 4: Get Google AI API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Copy the key (starts with `AIza...`)

---

### Step 5: Create Environment File

```bash
# Create .env file in rag folder
cat > rag/.env << 'EOF'
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
API_KEY=fortifai-dev-key-2024
EOF
```

**IMPORTANT:** Replace `YOUR_GOOGLE_API_KEY_HERE` with your actual key!

---

### Step 6: Start Docker Desktop

Open **Docker Desktop** application and wait until it says "Running".

---

### Step 7: Start Weaviate (Vector Database)

```bash
cd rag
docker-compose up -d
cd ..
```

Verify it's running:
```bash
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"status":"ready"}
```

---

### Step 8: Start RAG API Server (Terminal 1)

Open a **new terminal** and run:

```bash
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
source venv/bin/activate
cd rag
python main.py
```

You should see:
```
=== Initializing Fortif.ai RAG Server ===
✓ Weaviate client connected
✓ Collection 'FortifAiMasterMemory' ready
✓ Embedding model initialized
✓ LLM initialized
✓ RAG pipeline ready
=== Fortif.ai RAG Server Ready ===
API Documentation: http://localhost:8000/docs
```

**Keep this terminal running!**

---

### Step 9: Add Sample Patient Data (One-time)

Open a **new terminal** and run:

```bash
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
source venv/bin/activate
cd rag
python add_sample_memories.py
```

This adds 10 test memories for `patient_123` (Eleanor).

---

### Step 10: Grant Accessibility Permissions (macOS)

The voice app needs keyboard access. Do this **once**:

1. Go to **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Add **Terminal** (or your terminal app like iTerm2)
4. Toggle it **ON**

---

### Step 11: Start Voice Assistant (Terminal 2) - WITH SUDO

Open a **new terminal** and run:

```bash
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
sudo venv/bin/python main.py
```

Enter your Mac password when prompted.

You'll see:
```
--- Fortif.ai Voice Command Listener ---
Please enter the Patient ID for this session (e.g., patient_123):
```

Type: `patient_123` and press Enter.

```
✅ Session Patient ID set to: patient_123
Press 's' to speak (10 s). Press 'q' to quit. Press 'h' for hazard detection
```

---

### Step 12: Start Dashboard (Optional - Terminal 3)

Open a **new terminal**:

```bash
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model/dashboard
npm install
npm run dev
```

Open browser: http://localhost:5173

---

## Using the Voice Assistant

| Key | Action |
|-----|--------|
| **s** | Start speaking (records for up to 20 seconds) |
| **h** | Run hazard detection (camera) |
| **q** | Quit the app |

**Example commands to say:**
- "Tell me about Eleanor's family"
- "What is Eleanor's morning routine?"
- "Does Eleanor have any hobbies?"
- "Add an event to my calendar for tomorrow at 3pm"

---

## Quick Reference: Running Everything

You need **3 terminals** running:

| Terminal | Directory | Command |
|----------|-----------|---------|
| 1 | `rag/` | `python main.py` |
| 2 | Root | `sudo venv/bin/python main.py` |
| 3 | `dashboard/` | `npm run dev` (optional) |

Plus **Docker Desktop** running in background.

---

## Quick Start Script

Create a file called `start.sh` in the project root:

```bash
#!/bin/bash

echo "Starting Fortif.ai System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start Weaviate
echo "Starting Weaviate..."
cd rag
docker-compose up -d
cd ..

# Wait for Weaviate
echo "Waiting for Weaviate to be ready..."
sleep 5

# Check Weaviate
if curl -s http://localhost:8080/v1/.well-known/ready | grep -q "ready"; then
    echo "✅ Weaviate is ready"
else
    echo "❌ Weaviate failed to start"
    exit 1
fi

echo ""
echo "========================================"
echo "  Weaviate is running!"
echo "========================================"
echo ""
echo "Now open 3 terminals and run:"
echo ""
echo "Terminal 1 (RAG Server):"
echo "  cd rag && source ../venv/bin/activate && python main.py"
echo ""
echo "Terminal 2 (Voice Assistant):"
echo "  sudo venv/bin/python main.py"
echo ""
echo "Terminal 3 (Dashboard - optional):"
echo "  cd dashboard && npm run dev"
echo ""
```

Make it executable and run:
```bash
chmod +x start.sh
./start.sh
```

---

## Troubleshooting

### "Must be run as administrator"
```bash
# Use sudo with the venv python
sudo venv/bin/python main.py
```

### "Weaviate connection refused"
```bash
# Make sure Docker Desktop is running, then:
cd rag
docker-compose up -d
```

### "GOOGLE_API_KEY must be set"
```bash
# Check if .env exists and has the key
cat rag/.env

# If missing, create it:
echo "GOOGLE_API_KEY=your-key-here" > rag/.env
echo "API_KEY=fortifai-dev-key-2024" >> rag/.env
```

### "Internal Server Error" on queries
- Check the RAG server terminal for error details
- Usually means invalid Google API key
- Verify key at https://aistudio.google.com/app/apikey

### Voice not being recognized
- Check microphone permissions in System Settings
- Speak clearly and wait for "Capturing audio segment..."
- Try speaking louder or closer to mic

### Dashboard not loading
- Make sure RAG server is running on port 8000
- Check browser console for errors
- Try: `cd dashboard && npm install && npm run dev`

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/query` | POST | Chat with AI (RAG) |
| `/api/ingest` | POST | Add new memory |
| `/api/dashboard/patients/{id}/memories` | GET | List memories |
| `/api/dashboard/memories/{uuid}` | GET/PUT/DELETE | Memory CRUD |

---

## Ports Used

| Service | Port |
|---------|------|
| RAG API Server | 8000 |
| Weaviate HTTP | 8080 |
| Weaviate gRPC | 50051 |
| Dashboard (React) | 5173 |
