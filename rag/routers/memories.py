"""
Memory management endpoints for Fortif.ai Memory Dashboard.
Provides CRUD operations for patient memories stored in Weaviate.
Simplified version without authentication.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field

from services.memory_service import MemoryService, MemoryItem

router = APIRouter(prefix="/api/dashboard", tags=["Memory Dashboard"])


# === Pydantic Models ===

class MemoryResponse(BaseModel):
    """Response model for a single memory."""
    uuid: str
    text: str
    patient_id: str
    topic: str
    emotion: str
    source: str
    is_sensitive: bool
    entities: List[str]
    chunk_index: int
    total_chunks: int
    ingested_at: str

    @classmethod
    def from_memory_item(cls, item: MemoryItem) -> "MemoryResponse":
        return cls(
            uuid=item.uuid,
            text=item.text,
            patient_id=item.patient_id,
            topic=item.topic,
            emotion=item.emotion,
            source=item.source,
            is_sensitive=item.is_sensitive,
            entities=item.entities,
            chunk_index=item.chunk_index,
            total_chunks=item.total_chunks,
            ingested_at=item.ingested_at
        )


class MemoryListResponse(BaseModel):
    """Response model for memory list."""
    memories: List[MemoryResponse]
    total_count: int
    page: int
    per_page: int
    has_more: bool


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    topic: Optional[str] = None
    emotion: Optional[str] = Field(None, pattern="^(positive|negative|neutral|mixed|unknown)$")
    is_sensitive: Optional[bool] = None
    entities: Optional[List[str]] = None


class MemoryStatsResponse(BaseModel):
    """Response model for memory statistics."""
    total_memories: int
    topics: dict
    emotions: dict


class TopicsResponse(BaseModel):
    """Response model for available topics."""
    topics: List[str]


class EmotionsResponse(BaseModel):
    """Response model for available emotions."""
    emotions: List[str]


class SourcesResponse(BaseModel):
    """Response model for available sources."""
    sources: List[str]


# === Helper Functions ===

def get_memory_service(request: Request) -> MemoryService:
    """Get memory service from app state."""
    return MemoryService(request.app.state.weaviate_client)


# === Memory Endpoints ===

@router.get("/patients/{patient_id}/memories", response_model=MemoryListResponse)
async def list_patient_memories(
    patient_id: str,
    page: int = 1,
    per_page: int = 20,
    topic: Optional[str] = None,
    emotion: Optional[str] = None,
    source: Optional[str] = None,
    include_sensitive: bool = False,
    search: Optional[str] = None,
    request: Request = None
):
    """
    List memories for a patient with filtering and pagination.
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    if per_page > 100:
        per_page = 100

    memory_service = get_memory_service(request)

    result = memory_service.list_memories(
        patient_id=patient_id,
        page=page,
        per_page=per_page,
        topic_filter=topic,
        emotion_filter=emotion,
        source_filter=source,
        include_sensitive=include_sensitive,
        search_query=search
    )

    return MemoryListResponse(
        memories=[MemoryResponse.from_memory_item(m) for m in result.memories],
        total_count=result.total_count,
        page=result.page,
        per_page=result.per_page,
        has_more=result.has_more
    )


@router.get("/memories/{uuid}", response_model=MemoryResponse)
async def get_memory(uuid: str, request: Request = None):
    """Get a single memory by UUID."""
    memory_service = get_memory_service(request)
    memory = memory_service.get_memory(uuid)

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    return MemoryResponse.from_memory_item(memory)


@router.put("/memories/{uuid}", response_model=MemoryResponse)
async def update_memory(uuid: str, updates: MemoryUpdate, request: Request = None):
    """Update a memory's properties."""
    memory_service = get_memory_service(request)

    existing = memory_service.get_memory(uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    update_dict = updates.model_dump(exclude_none=True)
    updated = memory_service.update_memory(uuid, update_dict)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )

    return MemoryResponse.from_memory_item(updated)


@router.delete("/memories/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(uuid: str, hard_delete: bool = False, request: Request = None):
    """Delete a memory."""
    memory_service = get_memory_service(request)

    existing = memory_service.get_memory(uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    success = memory_service.delete_memory(uuid, hard_delete=hard_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )


@router.get("/patients/{patient_id}/stats", response_model=MemoryStatsResponse)
async def get_patient_memory_stats(patient_id: str, request: Request = None):
    """Get memory statistics for a patient."""
    memory_service = get_memory_service(request)
    stats = memory_service.get_memory_stats(patient_id)

    return MemoryStatsResponse(
        total_memories=stats["total_memories"],
        topics=stats["topics"],
        emotions=stats["emotions"]
    )


# === Metadata Endpoints ===

@router.get("/metadata/topics", response_model=TopicsResponse)
async def get_topics(request: Request = None):
    """Get list of available memory topics."""
    memory_service = get_memory_service(request)
    return TopicsResponse(topics=memory_service.get_topics())


@router.get("/metadata/emotions", response_model=EmotionsResponse)
async def get_emotions(request: Request = None):
    """Get list of available memory emotions."""
    memory_service = get_memory_service(request)
    return EmotionsResponse(emotions=memory_service.get_emotions())


@router.get("/metadata/sources", response_model=SourcesResponse)
async def get_sources(request: Request = None):
    """Get list of available memory sources."""
    memory_service = get_memory_service(request)
    return SourcesResponse(sources=memory_service.get_sources())
