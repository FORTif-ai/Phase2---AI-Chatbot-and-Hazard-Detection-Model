# Docker Installation Instructions for Windows

## ✅ Python Version Check
**Status:** ✅ Python 3.11.9 is installed (meets requirement of Python 3.8+)

## 📦 Docker Installation Steps

### Option 1: Download Docker Desktop (Recommended)

1. **Download Docker Desktop for Windows:**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - This will download `Docker Desktop Installer.exe`

2. **Install Docker Desktop:**
   - Run the installer as Administrator
   - Follow the installation wizard
   - Make sure to check "Use WSL 2 instead of Hyper-V" (recommended for Windows 10/11)
   - Restart your computer when prompted

3. **Start Docker Desktop:**
   - After restart, launch Docker Desktop from the Start menu
   - Wait for Docker to start (you'll see a whale icon in the system tray)
   - Docker Desktop will run in the background

4. **Verify Installation:**
   ```powershell
   docker --version
   docker run hello-world
   ```

### Option 2: Using Winget (Windows Package Manager)

If you have winget installed, you can install Docker Desktop directly:

```powershell
winget install Docker.DockerDesktop
```

### Option 3: Using Chocolatey

If you have Chocolatey installed:

```powershell
choco install docker-desktop
```

## 🔧 Post-Installation Setup

After installing Docker Desktop:

1. **Start Docker Desktop** (it should auto-start, but verify it's running)

2. **Verify Docker is running:**
   ```powershell
   docker ps
   ```

3. **Start Qdrant Vector Database** (as per the README):
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
   ```

4. **Verify Qdrant is running:**
   ```bash
   docker ps | Select-String qdrant
   ```

   Or visit: http://localhost:6333/dashboard in your browser

## 📝 Notes

- Docker Desktop requires Windows 10 64-bit: Pro, Enterprise, or Education (Build 15063 or later)
- OR Windows 11 64-bit: Home or Pro version 21H2 or higher
- WSL 2 feature must be enabled (Docker Desktop will guide you through this)
- You may need to enable virtualization in your BIOS if it's not already enabled

## 🚀 Next Steps After Docker Installation

Once Docker is installed and running:

1. Navigate to the RAG directory:
   ```bash
   cd Phase2---AI-Chatbot-and-Hazard-Detection-Model/rag
   ```

2. Start Qdrant:
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
   ```

3. Install Python dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

4. Create `.env` file with your Google API key:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. Run data ingestion:
   ```bash
   python ingest.py
   ```

6. Test queries:
   ```bash
   python query.py
   ```

