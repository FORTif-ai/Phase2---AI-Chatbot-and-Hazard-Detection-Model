"""
Web UI server for Fortif.ai Chatbot
Provides a web interface for voice/text interaction with the chatbot
"""
import os
import tempfile
from pathlib import Path
import whisper
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
from starlette.requests import Request
import pipeline
import dotenv

# Load environment variables
dotenv.load_dotenv("rag/.env")
os.environ['GRPC_VERBOSITY'] = 'ERROR'

app = FastAPI(title="Fortif.ai Web UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Load Whisper model once
whisper_model = None

def get_whisper_model():
    """Lazy load Whisper model"""
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base")
    return whisper_model

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main chatbot page"""
    return templates.TemplateResponse("chatbot.html", {"request": request})

@app.get("/dashboard", response_class=RedirectResponse)
async def dashboard():
    """Redirect to the React dashboard"""
    # Dashboard runs on port 3000 according to vite.config.js
    return RedirectResponse(url="http://localhost:3000")

@app.post("/api/process-voice")
async def process_voice(
    audio: UploadFile = File(...),
    patient_id: str = Form(...)
):
    """
    Process voice audio file and return chatbot response
    """
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Transcribe audio using Whisper
            model = get_whisper_model()
            result = model.transcribe(tmp_path)
            transcription = result["text"]
            
            # Process command through pipeline
            processor = pipeline.Processor()
            response = await processor.process_command(transcription, patient_id=patient_id)
            
            return JSONResponse({
                "success": True,
                "transcription": transcription,
                "response": response if isinstance(response, str) else response.get("message", str(response))
            })
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/process-text")
async def process_text(
    text: str = Form(...),
    patient_id: str = Form(...)
):
    """
    Process text command and return chatbot response
    """
    try:
        # Process command through pipeline
        processor = pipeline.Processor()
        response = await processor.process_command(text, patient_id=patient_id)
        
        return JSONResponse({
            "success": True,
            "response": response if isinstance(response, str) else response.get("message", str(response))
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
