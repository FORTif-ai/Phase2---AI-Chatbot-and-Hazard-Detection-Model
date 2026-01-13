# Fortif.ai RAG System - Complete Setup Guide

## Prerequisites

- **Python 3.10+**
- **Docker Desktop** (for Weaviate)
- **Node.js 18+** (for dashboard)
- **Google AI API Key** (free from Google AI Studio)

---

## Step 1: Clone and Navigate

```bash
git clone <repository-url>
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model/rag
```

---

## Step 2: Start Weaviate (Vector Database)

```bash
# Make sure Docker Desktop is running first!
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"status":"ready"}
```

---

## Step 3: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Step 4: Get Google AI API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

---

## Step 5: Create Environment File

Create a file named `.env` in the `rag` folder:

```bash
# Create .env file
cat > .env << 'EOF'
GOOGLE_API_KEY=paste-your-google-api-key-here
API_KEY=fortifai-dev-key-2024
EOF
```

**IMPORTANT:** Replace `paste-your-google-api-key-here` with your actual Google API key.

---

## Step 6: Start the Backend Server

```bash
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
```

---

## Step 7: Add Sample Data (Optional)

In a new terminal (keep server running):

```bash
cd rag
source venv/bin/activate
python add_sample_memories.py
```

This adds 10 test memories for `patient_123` (Eleanor).

---

## Step 8: Test the Chatbot

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fortifai-dev-key-2024" \
  -d '{
    "patient_id": "patient_123",
    "question": "Tell me about Eleanor morning routine"
  }'
```

Expected response:
```json
{
  "response": "Eleanor loves her morning routine...",
  "sources": [...],
  "patient_id": "patient_123"
}
```

---

## Step 9: Set Up Dashboard (Optional)

In a new terminal:

```bash
cd dashboard
npm install
npm run dev
```

Open: http://localhost:5173

---

## Quick Reference Commands

| Action | Command |
|--------|---------|
| Start Weaviate | `docker-compose up -d` |
| Stop Weaviate | `docker-compose down` |
| Start Backend | `python main.py` |
| Start Dashboard | `cd dashboard && npm run dev` |
| Add Test Data | `python add_sample_memories.py` |
| Check Weaviate | `curl http://localhost:8080/v1/.well-known/ready` |
| Check API Health | `curl http://localhost:8000/api/health` |

---

## API Endpoints

### Chat with AI (RAG)
```bash
POST /api/query
{
  "patient_id": "patient_123",
  "question": "Your question here",
  "include_sensitive": false,
  "limit": 3
}
```

### Add New Memory
```bash
POST /api/ingest
{
  "patient_id": "patient_123",
  "raw_text": "Memory text here...",
  "source": "family_questionnaire",
  "topic": "daily_routine",
  "emotion": "positive",
  "is_sensitive": false,
  "entities": ["Person", "Place"]
}
```

### List Memories
```bash
GET /api/dashboard/patients/patient_123/memories
```

### Health Check
```bash
GET /api/health
```

---

## Troubleshooting

### "Weaviate connection refused"
- Make sure Docker Desktop is running
- Run: `docker-compose up -d`

### "GOOGLE_API_KEY must be set"
- Create `.env` file with your Google API key

### "Internal Server Error" on /api/query
- Check server terminal for error details
- Usually means missing/invalid Google API key

### Port already in use
- Kill existing process: `lsof -ti:8000 | xargs kill`
- Or change port in `main.py`

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dashboard     │────▶│   FastAPI       │────▶│   Weaviate      │
│   (React)       │     │   Backend       │     │   (Vectors)     │
│   Port 5173     │     │   Port 8000     │     │   Port 8080     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Google Gemini  │
                        │  (LLM + Embed)  │
                        └─────────────────┘
```

**Data Flow for Chat:**
1. User asks question → Dashboard or curl
2. FastAPI receives request → `/api/query`
3. RAG Pipeline:
   - Embeds question using Google
   - Searches Weaviate for similar memories
   - Sends memories + question to Gemini LLM
4. Returns AI-generated response
