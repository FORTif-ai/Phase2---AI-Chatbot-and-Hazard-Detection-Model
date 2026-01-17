# FORTif.ai: An AI assistant for Independent Safe Senior Living 
In partnership with [WAT.ai](https://watai.ca/#/)

## TPMS and Their Contact Info

### Lino Kee
- **LinkedIn:** https://www.linkedin.com/in/linokee0423/  
- **Email:** guitarkinglino@gmail.com  
- **GitHub:** d-lino-kee  
- **Discord:** dalinoman  

### Edson Takei
- **LinkedIn:** https://www.linkedin.com/in/edsontakei/  
- **Email:** etakei@my.yorku.ca  
- **GitHub:** edsontakei  
- **Discord:** luketonbeleu  

## Ultimate Objective
FORTif.ai is an AI-driven companion that empowers seniors to live independently by merging proactive safety monitoring with tailored daily support. Using a computer-vision–powered Hazard Detection model, it continuously scans the home for potential risks—like spills, cluttered pathways, and tripping hazards—and offers clear, actionable recommendations to address them. At the same time, an intuitive AI chatbot engages users in friendly, proactive conversations, providing timely medication and appointment reminders, personalized wellness check-ins, and empathetic responses to questions or concerns. With built-in voice-to-text capabilities and real-time safety insights, FORTif.ai delivers a seamless, user-centric experience designed to enhance home safety, streamline everyday routines, and foster lasting independence for seniors.

## Project Goals

1. 🤖 **AI Chatbot (LLM)**: Design and deploy a robust conversational assistant  
   - Develop reliable voice-to-text transcription with built-in quality control  
   - Implement an action-oriented interface for booking appointments and sending medication reminders  
   - Ensure LLM responses are accurate, relevant, and aligned with senior-friendly language  
   - Integrate the chatbot with the back-end Hazard Detection system for contextual alerts  
   - ***AI Topics:*** *Speech Recognition, Prompt Engineering, LLM Evaluation, System Integration*

2. ⚠️ **Hazard Detection (OpenCV)**: Build and validate a vision-based model for home-hazard identification  
   - **Subgoal 1:** Model development to detect obstacles along predefined walkways  
   - **Subgoal 2:** Define performance metrics and risk thresholds (e.g., model accuracy and obstacle risk scoring)  
   - **Subgoal 3:** Curate and preprocess high-quality training datasets (data cleansing, augmentation, transformation)  
   - Quantify obstacle count and relative size for risk prioritization  
   - Establish a 70:30 training–testing data split to evaluate generalization  
   - ***AI Topics:*** *Computer Vision, Object Detection, Data Preprocessing, Model Evaluation*
  
## Background
As the global population ages, many seniors face significant challenges in maintaining their independence while ensuring their safety. Common risks include falls, accidents at home due to environmental hazards, and difficulties in managing daily tasks, such as taking medications or attending appointments. These issues often lead to a decline in quality of life and can result in a need for constant caregiver assistance, which is not always feasible or sustainable.

The goal of this project is to address these challenges by providing seniors with an AI-driven assistant that promotes both safety and independence. By using computer vision for hazard detection, gait analysis for fall vulnerability assessment, and a user-friendly chatbot for daily reminders and check-ins, we hope to ensure that seniors can confidently navigate their living spaces while staying on top of their personal care routines. This project aims to reduce the risk of accidents, improve daily living, and empower seniors to maintain their autonomy in a safe, supportive environment.

# The Team

## Technical Project Managers

### Lino Kee

[Lino Kee](https://www.linkedin.com/in/linokee0423/) is an undergraduate student at the University of Waterloo studying Honours Management Engineering. He brings academic and practical co-op experience in project management, data analysis, automation development, quality assurance, business platform management, and software development. Lino leads the development of the computer-vision–driven Hazard Detection model and oversees the overall architecture and delivery of the FORTif.ai tool. He’s happy to answer questions about project scope, timeline, and the long-term vision for FORTif.ai.

### Edson Takei

[Edson Takei](https://www.linkedin.com/in/edsontakei/) is un undergraduate student at York University studying Software Engineering in the Big Data stream. Edson has academic and applied experience in data analysis, genAI, bioinformatics and digital public health having also pursued research opportunities at the University of Waterloo and McGill University. His work includes leveraging large language models (LLMs) in healthcare to automate manual processes, as well as evaluating the effectiveness of LLMs in public health from both technical and policy-oriented perspectives. Edson leads the development of the AI chatbot subteam of FORTif.ai and oversees the overall architecture and delivery of the FORTif.ai tool. He’s happy to answer questions about project scope, timeline, and the long-term vision for FORTif.ai. 

## Core Members

### Michelle Steen - Technical Team Lead

### Spencer Spiegelman - Research Team Lead

### Chris Jackson - Hazard Detection Developer

### Akil Giri - Hazard Detection Developer

### Rohan Tuli  - Hazard Detection Developer

### Sarvesh Sekar - Hazard Detection Developer

### Jessi Huang - AI Chatbot Developer

### Mohammed Elshrief - AI Chatbot Developer

### Marco Lee - Technical Researcher 

### Sidney Liu - Technical Researcher

### Meghana Yarlagadda - Technical Researcher

## 🎯 Project Overview

Fortif.ai is a multi-component system that provides:

- **🎤 Voice Command Interface**: Interactive voice and text command processing
- **🧠 RAG Chatbot**: Intelligent memory-based conversations using Google Gemini AI
- **📊 Memory Dashboard**: Web-based interface for managing patient memories
- **🚨 Hazard Detection**: AI-powered analysis of images/videos to detect safety hazards
- **💾 Vector Database**: Weaviate-based memory storage and retrieval

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      FORTIF.AI SYSTEM                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐ │
│  │   React UI   │───▶│  Node.js     │───▶│   Python FastAPI   │ │
│  │   Port 3000  │    │  Port 3001   │    │   Port 8081        │ │
│  └──────────────┘    └──────────────┘    └──────────┬─────────┘ │
│                                                       │           │
│  ┌──────────────┐    ┌──────────────┐               ▼           │
│  │   Voice      │───▶│  Pipeline    │───▶┌────────────────────┐ │
│  │   main.py    │    │ (Gemini LLM) │    │   RAG API Server   │ │
│  │  (sudo)      │    └──────────────┘    │   Port 8000        │ │
│  └──────────────┘                        └──────────┬─────────┘ │
│                                                       │           │
│                                                       ▼           │
│                                          ┌────────────────────┐   │
│                                          │     Weaviate       │   │
│                                          │  (Vector Database) │   │
│                                          │   Port 8080/50051  │   │
│                                          └────────────────────┘   │
│                                                       │           │
│  ┌──────────────┐                                    │           │
│  │   Hazard     │                                    ▼           │
│  │   Detection  │                          ┌────────────────────┐ │
│  │   (Gemini)   │                          │   Google Gemini    │ │
│  └──────────────┘                          │ (LLM + Embeddings)│ │
│                                             └────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

| Requirement | Installation | Notes |
|-------------|--------------|-------|
| **Python 3.10+** | `python --version` | Required for all Python components |
| **Node.js 18+** | `node --version` | Required for React dashboard and Node.js server |
| **Docker Desktop** | [Download here](https://www.docker.com/products/docker-desktop/) | Required for Weaviate vector database |
| **Google AI API Key** | [Get here](https://aistudio.google.com/app/apikey) | Free tier available (15 RPM, 1M tokens/min) |
| **Git** | `git --version` | For cloning the repository |

### Operating System Support

- ✅ **Windows 10/11** (64-bit)
- ✅ **macOS** (10.14+)
- ✅ **Linux** (Ubuntu 18.04+)

## 🚀 Quick Start

### Option 1: Start Everything at Once (Recommended)

From the project root:

```bash
# Install root dependencies (first time only)
npm install

# Start all services
npm start
```

This will start:
- ✅ RAG API Server (port 8000)
- ✅ Python FastAPI Server (port 8081)
- ✅ Node.js Server (port 3001)
- ✅ React Dashboard (port 3000)

**Open your browser:** http://localhost:3000

### Option 2: Manual Setup (Step-by-Step)

See [Complete Setup](#-complete-setup-guide) section below.

## 📦 Complete Setup Guide

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r rag/requirements.txt
```

### Step 3: Get Google AI API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Choose **"Create API key in new project"**
5. Copy your API key (starts with `AIza...`)

**Note:** Free tier includes:
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

### Step 4: Configure Environment Variables

#### For RAG System

Create `rag/.env`:

```bash
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
API_KEY=fortifai-dev-key-2024
```

#### For Hazard Detection

Create `HazardDetection/.env` (or add to root `.env`):

```bash
GEMINI_API_KEY=YOUR_GOOGLE_API_KEY_HERE
```

#### For Twilio SMS (Optional)

Add to `.env`:

```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

### Step 5: Start Docker Desktop

1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Start Docker Desktop (must be running before starting services)
3. Verify Docker is running:
   ```bash
   docker ps
   ```

### Step 6: Start Weaviate Vector Database

```bash
cd rag
docker-compose up -d
cd ..
```

Verify Weaviate is running:
```bash
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"status":"ready"}
```

### Step 7: Install Node.js Dependencies

```bash
# Root dependencies (for concurrently)
npm install

# Server dependencies
cd server
npm install
cd ..

# Dashboard dependencies
cd dashboard
npm install
cd ..
```

### Step 8: Add Sample Data (Optional)

```bash
cd rag
python add_sample_memories.py
cd ..
```

This adds 10 test memories for `patient_123` (Eleanor).

### Step 9: Start All Services

#### Quick Start (Single Command)

```bash
npm start
```

#### Manual Start (Separate Terminals)

**Terminal 1 - RAG API Server:**
```bash
cd rag
python main.py
```
Should see: `=== Fortif.ai RAG Server Ready ===`

**Terminal 2 - Python FastAPI Server:**
```bash
python web_ui.py
```
Should see: `Uvicorn running on http://0.0.0.0:8081`

**Terminal 3 - Node.js Server:**
```bash
cd server
npm start
```
Should see: `🚀 Node.js server running on http://localhost:3001`

**Terminal 4 - React Dashboard:**
```bash
cd dashboard
npm run dev
```
Should see: `Local: http://localhost:3000`

### Step 10: Access the Application

1. Open browser: **http://localhost:3000**
2. Navigate to: **http://localhost:3000/voice**
3. Enter Patient ID (e.g., `patient_123`)
4. Start using the interface!

## 🎯 Component Details

### 1. Voice Command Interface

**Location:** `http://localhost:3000/voice`

**Features:**
- 🎤 Voice recording and transcription
- 💬 Text command input
- 🚨 Hazard detection trigger with mode selection
- 📝 Conversation history
- 🖼️ Image display for hazard detection results

**Usage:**
1. Enter Patient ID
2. Click "Start Recording" and speak your command
3. Or type text commands in the text area
4. Click "Run Hazard Detection" to trigger hazard analysis

**Supported Commands:**
- "Tell me about Eleanor's family"
- "What is Eleanor's morning routine?"
- "Add an event to my calendar for tomorrow at 3pm"
- "Run hazard detection" (or use the UI button)

### 2. RAG (Retrieval-Augmented Generation) System

**API Base URL:** `http://localhost:8000`

**Features:**
- Semantic memory search
- Context-aware responses
- Patient-specific memory management
- Emotion and topic filtering

**API Endpoints:**

**Query (Chat with AI):**
```bash
POST /api/query
Headers:
  X-API-Key: fortifai-dev-key-2024
Body:
{
  "patient_id": "patient_123",
  "question": "Tell me about Eleanor's morning routine",
  "limit": 5,
  "include_sensitive": false
}
```

**Add Memory:**
```bash
POST /api/ingest
Headers:
  X-API-Key: fortifai-dev-key-2024
Body:
{
  "patient_id": "patient_123",
  "raw_text": "Eleanor loves to garden in the afternoon",
  "source": "family_interview",
  "topic": "hobbies",
  "emotion": "positive",
  "is_sensitive": false
}
```

**List Memories:**
```bash
GET /api/dashboard/patients/{patient_id}/memories
Headers:
  X-API-Key: fortifai-dev-key-2024
```

### 3. Hazard Detection System

**Location:** `HazardDetection/hazard_detector.py`

**Modes:**
- **Image**: Single image analysis
- **Video**: Continuous video monitoring (frame-by-frame)
- **Batch**: Process multiple images from a zip file
- **Directory**: Process all images in a directory

**Usage via UI:**
1. Go to Voice Command Interface
2. Select mode from dropdown
3. Configure mode-specific settings:
   - **Image**: Image filename
   - **Video**: Video filename, poll interval
   - **Batch**: Zip filename, output file, poll interval
   - **Directory**: Image directory, output file, poll interval
4. Click "Run Hazard Detection"
5. View results with images in conversation history

**Usage via Command Line:**
```bash
# Image mode
python HazardDetection/hazard_detector.py --mode image --image-filename image.png

# Video mode
python HazardDetection/hazard_detector.py --mode video --video-filename video.mp4 --poll-interval 4.0

# Batch mode (zip)
python HazardDetection/hazard_detector.py --mode batch --zip-filename images.zip --output-file results.txt

# Directory mode
python HazardDetection/hazard_detector.py --mode directory --image-dir test_images --output-file results.txt
```

**Supported Image Formats:**
- JPEG/JPG
- PNG
- GIF
- BMP
- WebP

**Detection Output:**
- People detected (Yes/No)
- Hazards detected (Yes/No)
- Hazard details (type, location, severity, details)
- Summary text
- Images displayed in UI (for image/batch/directory modes)

### 4. Memory Dashboard

**Location:** `http://localhost:5173` (if started separately)

**Features:**
- View all patient memories
- Search and filter memories
- View memory details
- Navigate between patients

## 🔌 Ports Used

| Service | Port | Description |
|---------|------|-------------|
| React Dashboard | 3000 | Main web interface |
| Node.js Server | 3001 | Proxy server |
| Python FastAPI | 8081 | Voice/text processing |
| RAG API Server | 8000 | RAG chatbot API |
| Weaviate HTTP | 8080 | Vector database HTTP API |
| Weaviate gRPC | 50051 | Vector database gRPC API |

## 🛠️ Troubleshooting

### "Port already in use" Error

**Python FastAPI (8081):**
```bash
# Windows: Find and kill process
netstat -ano | findstr :8081
taskkill /PID <PID> /F

# macOS/Linux: Find and kill process
lsof -ti:8081 | xargs kill
```

**Node.js Server (3001):**
```bash
# Windows
netstat -ano | findstr :3001
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3001 | xargs kill
```

**React (3000):**
Vite will automatically use the next available port (3001, 3002, etc.)

### "Weaviate connection refused"

1. Make sure Docker Desktop is running
2. Start Weaviate:
   ```bash
   cd rag
   docker-compose up -d
   ```
3. Verify:
   ```bash
   curl http://localhost:8080/v1/.well-known/ready
   ```

### "GOOGLE_API_KEY must be set"

1. Check if `.env` file exists in `rag/` directory
2. Verify the file contains:
   ```bash
   GOOGLE_API_KEY=your-actual-key-here
   API_KEY=fortifai-dev-key-2024
   ```
3. For Hazard Detection, also check `HazardDetection/.env` or root `.env`

### "Cannot find module" (Node.js)

```bash
# Install dependencies
npm install
cd server && npm install
cd ../dashboard && npm install
```

### "Microphone not working"

1. Grant browser permissions for microphone access
2. Try Chrome or Firefox (best browser support)
3. Check system microphone settings
4. Ensure microphone is not being used by another application

### "Hazard detection fails"

1. Verify `GEMINI_API_KEY` is set in `.env`
2. Check that image/video files exist at specified paths
3. Ensure images are in supported formats
4. For batch mode, verify zip file contains only JPG/JPEG files

### "Internal Server Error" on API calls

1. Check the server terminal for detailed error messages
2. Verify Google API key is valid
3. Check API rate limits (free tier: 15 RPM)
4. Ensure Weaviate is running for RAG queries

### "Must be run as administrator" (macOS/Linux)

For voice assistant (`main.py`), run with sudo:
```bash
sudo venv/bin/python main.py
```

This is required for microphone/keyboard access on macOS.

### Docker Installation (Windows)

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Run installer as Administrator
3. Enable WSL 2 (if available)
4. Restart computer
5. Verify: `docker --version`

## 📚 Development

### Project Structure

```
Phase2---AI-Chatbot-and-Hazard-Detection-Model/
├── dashboard/          # React frontend
│   ├── src/
│   │   ├── pages/      # React components
│   │   └── api/        # API client
│   └── package.json
├── server/             # Node.js proxy server
│   ├── server.js       # Express server
│   └── package.json
├── rag/                # RAG system
│   ├── main.py         # RAG API server
│   ├── docker-compose.yml  # Weaviate config
│   └── requirements.txt
├── HazardDetection/    # Hazard detection
│   ├── hazard_detector.py
│   └── .env
├── web_ui.py           # Python FastAPI server
├── main.py             # Voice assistant (CLI)
├── pipeline.py         # Command processing logic
├── requirements.txt    # Python dependencies
└── package.json        # Root package.json (concurrently)
```

### Adding New Features

**Voice Commands:**
- Edit `pipeline.py` to add command processing logic
- Update `web_ui.py` if new API endpoints needed

**RAG System:**
- Add memories via `/api/ingest` endpoint
- Customize prompts in `rag/main.py`

**Hazard Detection:**
- Modify detection prompt in `hazard_detector.py` (HAZARD_PROMPT)
- Add new modes by extending `main()` function

**UI:**
- Edit React components in `dashboard/src/pages/`
- Update styles in `.css` files

## 🚀 Production Deployment

### Building for Production

**React Dashboard:**
```bash
cd dashboard
npm run build
# Built files in dashboard/dist/
```

**Node.js Server:**
The server automatically serves built files from `dashboard/dist/`

**Python Services:**
- Use process managers like `systemd` (Linux) or `PM2` (Node.js-based)
- Set up reverse proxy (nginx) for production
- Use environment-specific `.env` files
- Enable HTTPS

### Environment Variables (Production)

Create `.env` files with production values:
- `GOOGLE_API_KEY`: Production API key
- `API_KEY`: Strong authentication key
- `PORT`: Production ports
- Database credentials (if applicable)

### Security Recommendations

1. **API Keys**: Never commit `.env` files to version control
2. **CORS**: Restrict CORS origins in production
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Authentication**: Add proper authentication for production
5. **HTTPS**: Use HTTPS in production
6. **Secrets Management**: Use secret management services

## 📖 API Documentation

### RAG API (Port 8000)

Full API documentation available at: `http://localhost:8000/docs`

**Key Endpoints:**
- `GET /api/health` - Health check
- `POST /api/query` - Query with RAG
- `POST /api/ingest` - Add memory
- `GET /api/dashboard/patients/{id}/memories` - List memories
- `GET /api/dashboard/memories/{uuid}` - Get memory
- `PUT /api/dashboard/memories/{uuid}` - Update memory
- `DELETE /api/dashboard/memories/{uuid}` - Delete memory

### FastAPI Server (Port 8081)

**Endpoints:**
- `POST /api/process-voice` - Process voice audio
- `POST /api/process-text` - Process text command

### Node.js Server (Port 3001)

**Endpoints:**
- `GET /api/health` - Health check
- `POST /api/process-voice` - Proxy to FastAPI
- `POST /api/process-text` - Proxy to FastAPI
- `POST /api/hazard-detection` - Trigger hazard detection
- `GET /api/hazard-images/:filename` - Serve hazard detection images

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🙏 Acknowledgments

- Google Gemini AI for LLM and embeddings
- Weaviate for vector database
- OpenAI Whisper for speech transcription
- React and Vite for frontend framework
- FastAPI and Express for backend frameworks

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section above

---

**Built with ❤️ for AI-powered healthcare assistance**
