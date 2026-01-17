"""
Fortif.ai RAG API Server
FastAPI application providing empathetic chatbot responses for dementia patients.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import weaviate
import os
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from models import (
    QueryRequest,
    QueryResponse,
    SourceDocument,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    ErrorResponse,
    TranscriptionRequest,
    TranscriptionResponse
)
from auth import verify_api_key
from rag_pipeline import RAGPipeline
from ingest import (
    validate_patient_record,
    ensure_collection_exists,
    process_and_ingest_data
)
from routers import memories_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan: initialize clients on startup, cleanup on shutdown.
    """
    logger.info("=== Initializing Fortif.ai RAG Server ===")

    try:
        # Initialize Weaviate client
        logger.info(f"Connecting to Weaviate at {settings.weaviate_host}:{settings.weaviate_port}")
        app.state.weaviate_client = weaviate.connect_to_local(
            host=settings.weaviate_host,
            port=settings.weaviate_port,
            grpc_port=settings.weaviate_grpc_port
        )
        logger.info("✓ Weaviate client connected")

        # Ensure collection exists
        ensure_collection_exists(app.state.weaviate_client, settings.weaviate_collection_name)
        logger.info(f"✓ Collection '{settings.weaviate_collection_name}' ready")

        # Initialize Google embeddings for queries
        logger.info(f"Initializing Google embeddings: {settings.embedding_model}")
        app.state.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            task_type="retrieval_query"
        )
        logger.info("✓ Embedding model initialized")

        # Initialize Google LLM
        logger.info(f"Initializing Google LLM: {settings.llm_model} (temp={settings.llm_temperature})")
        app.state.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature
        )
        logger.info("✓ LLM initialized")

        # Initialize RAG pipeline
        app.state.rag_pipeline = RAGPipeline(
            weaviate_client=app.state.weaviate_client,
            embeddings=app.state.embeddings,
            llm=app.state.llm
        )
        logger.info("✓ RAG pipeline ready")

        # Initialize embeddings for ingestion (separate instance with different task_type)
        app.state.ingest_embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            task_type="retrieval_document"
        )
        logger.info("✓ Ingest embeddings initialized")

        logger.info("=== Fortif.ai RAG Server Ready ===")
        logger.info(f"API Documentation: http://localhost:8000/docs")

    except Exception as e:
        logger.error(f"✗ Failed to initialize server: {e}", exc_info=True)
        raise

    yield

    # Cleanup
    logger.info("Shutting down Fortif.ai RAG Server...")
    if hasattr(app.state, "weaviate_client"):
        app.state.weaviate_client.close()
        logger.info("✓ Weaviate client closed")
    logger.info("=== Shutdown complete ===")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description="RAG-powered empathetic chatbot for dementia patients",
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail),
            path=str(request.url.path),
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Please try again later.",
            path=str(request.url.path),
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files directory mounted: {static_dir}")

# Include routers
app.include_router(memories_router)
logger.info("✓ Dashboard router included")

# === API Endpoints ===

@app.get("/", tags=["General"])
async def root():
    """Root endpoint - serves the web front-end."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "Fortif.ai RAG API",
        "version": settings.api_version,
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Verifies:
    - API is running
    - Weaviate connection is active
    - Collection exists and is accessible
    """
    try:
        collection = app.state.weaviate_client.collections.get(
            settings.weaviate_collection_name
        )
        collection_info = collection.aggregate.over_all(total_count=True)

        return HealthResponse(
            status="healthy",
            weaviate_connected=True,
            collection_exists=True,
            collection_count=collection_info.total_count,
            timestamp=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Weaviate connection failed: {str(e)}"
        )


@app.post(
    "/api/query",
    response_model=QueryResponse,
    tags=["RAG"],
    dependencies=[Depends(verify_api_key)]
)
async def query_patient(request: QueryRequest):
    """
    Query patient memories and generate empathetic response.

    This endpoint implements the full RAG pipeline:
    1. **Retrieval**: Search patient memories using vector similarity
    2. **Augmentation**: Format retrieved memories as context
    3. **Generation**: Generate empathetic response using Gemini LLM

    **Authentication**: Requires X-API-Key header

    **Example Request**:
    ```json
    {
        "patient_id": "patient_123",
        "question": "Tell me about my granddaughter's birthday",
        "include_sensitive": false,
        "emotion_filter": "positive",
        "limit": 3
    }
    ```
    """
    try:
        logger.info(f"Query received for patient_id={request.patient_id}")

        # Run RAG pipeline
        response_text, retrieved_docs = app.state.rag_pipeline.run(
            patient_id=request.patient_id,
            question=request.question,
            history=request.history,
            limit=request.limit,
            include_sensitive=request.include_sensitive,
            emotion_filter=request.emotion_filter
        )

        # Format source documents
        sources = [
            SourceDocument(
                text=doc.properties["text"],
                topic=doc.properties["topic"],
                emotion=doc.properties["emotion"],
                source=doc.properties["source"],
                score=doc.metadata.score,
                chunk_index=doc.properties["chunk_index"],
                total_chunks=doc.properties["total_chunks"]
            )
            for doc in retrieved_docs
        ]

        logger.info(f"Query successful: {len(sources)} sources, {len(response_text)} char response")

        return QueryResponse(
            response=response_text,
            sources=sources,
            patient_id=request.patient_id,
            metadata={
                "retrieved_count": len(retrieved_docs),
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline failed: {str(e)}"
        )


@app.post(
    "/api/ingest",
    response_model=IngestResponse,
    tags=["Data Management"],
    dependencies=[Depends(verify_api_key)]
)
async def ingest_memory(request: IngestRequest):
    """
    Ingest new patient memory into the system.

    **Authentication**: Requires X-API-Key header (admin access)

    Performs:
    1. Validation of patient record
    2. Text chunking (500 chars, 50 overlap)
    3. Embedding generation
    4. Storage in Weaviate

    **Example Request**:
    ```json
    {
        "patient_id": "patient_123",
        "raw_text": "Jane loves her morning tea ritual...",
        "source": "family_questionnaire",
        "topic": "daily_routine",
        "is_sensitive": false,
        "entities": ["tea", "morning"],
        "emotion": "positive"
    }
    ```
    """
    try:
        logger.info(f"Ingest request received for patient_id={request.patient_id}")

        # Convert request to dict format expected by ingest logic
        patient_record = {
            "patient_id": request.patient_id,
            "raw_text": request.raw_text,
            "source": request.source,
            "topic": request.topic,
            "is_sensitive": request.is_sensitive,
            "entities": request.entities,
            "emotion": request.emotion
        }

        # Validate record
        is_valid, error_msg = validate_patient_record(patient_record)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid patient record: {error_msg}"
            )

        # Process and ingest
        stats = process_and_ingest_data(
            client=app.state.weaviate_client,
            embedding_model=app.state.ingest_embeddings,
            patient_data=[patient_record],
            batch_size=settings.default_batch_size,
            validate_records=False  # Already validated above
        )

        logger.info(f"Ingest successful: {stats}")

        return IngestResponse(
            status=stats.get("status", "success"),
            patient_id=request.patient_id,
            chunks_created=stats.get("chunks_created", 0),
            objects_upserted=stats.get("objects_upserted", 0),
            message=f"Successfully ingested memory for patient {request.patient_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post(
    "/api/transcribe",
    response_model=TranscriptionResponse,
    tags=["Voice"],
    dependencies=[Depends(verify_api_key)]
)
async def transcribe_audio(request: TranscriptionRequest):
    """
    Transcribe audio using Whisper model.
    
    **Authentication**: Requires X-API-Key header (if API_KEY is set in .env)
    
    **Example Request**:
    ```json
    {
        "audio_data": "base64_encoded_audio_string",
        "format": "wav",
        "patient_id": "patient_123"
    }
    ```
    """
    try:
        import base64
        import tempfile
        import os
        import whisper
        
        # Add ffmpeg to PATH if it's installed via winget but not in system PATH
        import shutil
        ffmpeg_exe = shutil.which("ffmpeg")
        if not ffmpeg_exe:
            # Try to find ffmpeg in common winget installation location
            user_profile = os.environ.get("USERPROFILE", "")
            winget_ffmpeg_pattern = os.path.join(
                user_profile,
                "AppData", "Local", "Microsoft", "WinGet", "Packages",
                "Gyan.FFmpeg_*", "*", "bin"
            )
            import glob
            ffmpeg_dirs = glob.glob(winget_ffmpeg_pattern)
            if ffmpeg_dirs and os.path.exists(os.path.join(ffmpeg_dirs[0], "ffmpeg.exe")):
                ffmpeg_path = ffmpeg_dirs[0]
                current_path = os.environ.get("PATH", "")
                if ffmpeg_path not in current_path:
                    os.environ["PATH"] = f"{ffmpeg_path};{current_path}"
                    logger.info(f"Added ffmpeg to PATH: {ffmpeg_path}")
        
        logger.info(f"Transcription request received (format: {request.format}, patient_id: {request.patient_id or 'none'})")
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(request.audio_data)
            logger.info(f"Decoded audio: {len(audio_bytes)} bytes")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 audio data: {str(e)}"
            )
        
        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio data is empty"
            )
        
        # Check minimum file size
        if len(audio_bytes) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file too small. Please record longer audio."
            )
        
        # Create temporary file
        file_ext = request.format.lower()
        if file_ext not in ['wav', 'webm', 'mp3', 'flac', 'ogg', 'm4a']:
            file_ext = 'wav'  # Default to wav
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        transcript_text = ""
        detected_language = None
        
        try:
            logger.info(f"Transcribing audio file: {temp_file_path} ({len(audio_bytes)} bytes)")
            
            # Load Whisper model (using base model for speed, can be changed)
            model_name = "base"  # Options: tiny, base, small, medium, large
            logger.info(f"Loading Whisper model: {model_name}")
            model = whisper.load_model(model_name)
            
            # Transcribe
            logger.info("Transcribing audio...")
            result = model.transcribe(temp_file_path)
            
            transcript_text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            logger.info(f"Transcription successful: {len(transcript_text)} characters, language: {detected_language}")
            
            if not transcript_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transcription returned empty. The audio might be too quiet, too short, or contain no speech."
                )
                
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Whisper not installed. Please run: pip install openai-whisper"
            )
        except FileNotFoundError as e:
            if "ffmpeg" in str(e).lower() or "winerror 2" in str(e).lower():
                logger.error(f"ffmpeg not found: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "ffmpeg is required for audio transcription but was not found. "
                        "Please install ffmpeg:\n"
                        "1. Download from: https://ffmpeg.org/download.html\n"
                        "2. Or use: winget install ffmpeg\n"
                        "3. Or use: choco install ffmpeg\n"
                        "4. After installing, restart the server"
                    )
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"File not found: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "ffmpeg is required for audio transcription. "
                        "Please install ffmpeg and restart the server. "
                        "Use: winget install ffmpeg"
                    )
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {error_msg}"
            )
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
        
        return TranscriptionResponse(
            text=transcript_text,
            language=detected_language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )