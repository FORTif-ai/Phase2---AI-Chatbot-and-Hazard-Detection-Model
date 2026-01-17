"""
Memory Service for Fortif.ai Memory Dashboard.
Provides CRUD operations for memories stored in Weaviate.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import weaviate
from weaviate.classes.query import Filter, MetadataQuery, Sort

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents a memory item from Weaviate."""
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


@dataclass
class MemoryListResponse:
    """Response for memory list queries."""
    memories: List[MemoryItem]
    total_count: int
    page: int
    per_page: int
    has_more: bool


class MemoryService:
    """
    Service for managing memories in Weaviate.

    Provides:
    - List memories with filtering and pagination
    - Get single memory by UUID
    - Update memory properties
    - Delete memory (soft delete by marking as hidden, or hard delete)
    """

    def __init__(self, weaviate_client: weaviate.WeaviateClient):
        """
        Initialize memory service.

        Args:
            weaviate_client: Connected Weaviate client
        """
        self.client = weaviate_client
        self.collection_name = settings.weaviate_collection_name

    def _get_collection(self):
        """Get Weaviate collection."""
        return self.client.collections.get(self.collection_name)

    def list_memories(
        self,
        patient_id: str,
        page: int = 1,
        per_page: int = 20,
        topic_filter: Optional[str] = None,
        emotion_filter: Optional[str] = None,
        source_filter: Optional[str] = None,
        include_sensitive: bool = True,
        search_query: Optional[str] = None,
        sort_by: str = "ingested_at",
        sort_order: str = "desc"
    ) -> MemoryListResponse:
        """
        List memories for a patient with filtering and pagination.

        Args:
            patient_id: Patient identifier
            page: Page number (1-indexed)
            per_page: Number of items per page
            topic_filter: Filter by topic
            emotion_filter: Filter by emotion
            source_filter: Filter by source
            include_sensitive: Include sensitive memories
            search_query: Optional text search query
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            MemoryListResponse with memories and pagination info
        """
        try:
            collection = self._get_collection()

            # Build filter
            query_filter = Filter.by_property("patient_id").equal(patient_id)

            if not include_sensitive:
                query_filter = query_filter & Filter.by_property("is_sensitive").equal(False)

            if topic_filter:
                query_filter = query_filter & Filter.by_property("topic").equal(topic_filter)

            if emotion_filter:
                query_filter = query_filter & Filter.by_property("emotion").equal(emotion_filter)

            if source_filter:
                query_filter = query_filter & Filter.by_property("source").equal(source_filter)

            # Calculate offset
            offset = (page - 1) * per_page

            # Query with filters
            if search_query:
                # Use BM25 search with filters
                response = collection.query.bm25(
                    query=search_query,
                    filters=query_filter,
                    limit=per_page,
                    offset=offset,
                    return_metadata=MetadataQuery(score=True)
                )
            else:
                # Use fetch_objects with filters
                response = collection.query.fetch_objects(
                    filters=query_filter,
                    limit=per_page,
                    offset=offset,
                    return_metadata=MetadataQuery(creation_time=True)
                )

            # Convert to MemoryItem objects
            memories = []
            for obj in response.objects:
                props = obj.properties
                memories.append(MemoryItem(
                    uuid=str(obj.uuid),
                    text=props.get("text", ""),
                    patient_id=props.get("patient_id", ""),
                    topic=props.get("topic", ""),
                    emotion=props.get("emotion", ""),
                    source=props.get("source", ""),
                    is_sensitive=props.get("is_sensitive", False),
                    entities=props.get("entities", []),
                    chunk_index=props.get("chunk_index", 0),
                    total_chunks=props.get("total_chunks", 1),
                    ingested_at=props.get("ingested_at", "")
                ))

            # Get total count for pagination (only if we need it)
            # If we got fewer results than requested, we know there are no more
            if len(memories) < per_page:
                total_count = offset + len(memories)
                has_more = False
            else:
                # Only query total count if we might have more pages
                count_response = collection.aggregate.over_all(
                    filters=query_filter,
                    total_count=True
                )
                total_count = count_response.total_count or 0
                has_more = offset + len(memories) < total_count

            logger.info(
                f"Listed {len(memories)} memories for patient {patient_id} "
                f"(page {page}, total {total_count})"
            )

            return MemoryListResponse(
                memories=memories,
                total_count=total_count,
                page=page,
                per_page=per_page,
                has_more=has_more
            )

        except Exception as e:
            logger.error(f"Failed to list memories: {e}", exc_info=True)
            raise

    def get_memory(self, uuid: str) -> Optional[MemoryItem]:
        """
        Get a single memory by UUID.

        Args:
            uuid: Memory UUID

        Returns:
            MemoryItem or None if not found
        """
        try:
            collection = self._get_collection()
            obj = collection.query.fetch_object_by_id(uuid)

            if not obj:
                return None

            props = obj.properties
            return MemoryItem(
                uuid=str(obj.uuid),
                text=props.get("text", ""),
                patient_id=props.get("patient_id", ""),
                topic=props.get("topic", ""),
                emotion=props.get("emotion", ""),
                source=props.get("source", ""),
                is_sensitive=props.get("is_sensitive", False),
                entities=props.get("entities", []),
                chunk_index=props.get("chunk_index", 0),
                total_chunks=props.get("total_chunks", 1),
                ingested_at=props.get("ingested_at", "")
            )

        except Exception as e:
            logger.error(f"Failed to get memory {uuid}: {e}", exc_info=True)
            raise

    def update_memory(
        self,
        uuid: str,
        updates: Dict[str, Any]
    ) -> Optional[MemoryItem]:
        """
        Update memory properties.

        Args:
            uuid: Memory UUID
            updates: Dictionary of properties to update

        Returns:
            Updated MemoryItem or None if not found
        """
        try:
            collection = self._get_collection()

            # Verify memory exists
            existing = self.get_memory(uuid)
            if not existing:
                return None

            # Filter allowed update fields
            allowed_fields = {"text", "topic", "emotion", "is_sensitive", "entities"}
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

            if not filtered_updates:
                return existing

            # Update in Weaviate
            collection.data.update(
                uuid=uuid,
                properties=filtered_updates
            )

            logger.info(f"Updated memory {uuid}: {list(filtered_updates.keys())}")

            # Return updated memory
            return self.get_memory(uuid)

        except Exception as e:
            logger.error(f"Failed to update memory {uuid}: {e}", exc_info=True)
            raise

    def delete_memory(self, uuid: str, hard_delete: bool = False) -> bool:
        """
        Delete a memory.

        Args:
            uuid: Memory UUID
            hard_delete: If True, permanently delete. If False, mark as sensitive/hidden.

        Returns:
            True if deleted successfully, False if not found
        """
        try:
            collection = self._get_collection()

            # Verify memory exists
            existing = self.get_memory(uuid)
            if not existing:
                return False

            if hard_delete:
                # Permanently delete from Weaviate
                collection.data.delete_by_id(uuid)
                logger.info(f"Hard deleted memory {uuid}")
            else:
                # Soft delete by marking as sensitive (hidden from normal queries)
                collection.data.update(
                    uuid=uuid,
                    properties={"is_sensitive": True}
                )
                logger.info(f"Soft deleted memory {uuid} (marked as sensitive)")

            return True

        except Exception as e:
            logger.error(f"Failed to delete memory {uuid}: {e}", exc_info=True)
            raise

    def get_memory_stats(self, patient_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a patient.
        Optimized to fetch all memories once and calculate stats in-memory.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with memory statistics
        """
        try:
            collection = self._get_collection()

            # Build filter
            query_filter = Filter.by_property("patient_id").equal(patient_id)

            # Fetch all memories for this patient (with reasonable limit for stats)
            # We'll sample up to 1000 memories for stats calculation
            response = collection.query.fetch_objects(
                filters=query_filter,
                limit=1000,  # Reasonable limit for stats
                return_metadata=MetadataQuery(creation_time=True)
            )

            # Calculate stats from fetched objects
            total_count = len(response.objects)
            topic_counts = {}
            emotion_counts = {}

            for obj in response.objects:
                props = obj.properties
                
                # Count topics
                topic = props.get("topic", "other")
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
                # Count emotions
                emotion = props.get("emotion", "unknown")
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            # If we hit the limit, get actual total count (but only if needed)
            if total_count >= 1000:
                total_response = collection.aggregate.over_all(
                    filters=query_filter,
                    total_count=True
                )
                total_count = total_response.total_count or total_count

            logger.info(f"Calculated stats for patient {patient_id}: {total_count} total memories")

            return {
                "total_memories": total_count,
                "topics": topic_counts,
                "emotions": emotion_counts
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats for {patient_id}: {e}", exc_info=True)
            raise

    def get_topics(self) -> List[str]:
        """Get list of available topics."""
        return [
            "daily_routine",
            "positive_memory",
            "family_history",
            "health_info",
            "preferences",
            "life_events",
            "hobbies",
            "relationships",
            "career",
            "other"
        ]

    def get_emotions(self) -> List[str]:
        """Get list of available emotions."""
        return ["positive", "negative", "neutral", "mixed", "unknown"]

    def get_sources(self) -> List[str]:
        """Get list of available sources."""
        return [
            "family_questionnaire",
            "ehr_note",
            "caregiver_input",
            "patient_conversation",
            "medical_record",
            "other"
        ]
