"""
Script to add sample memories for patient_123 to test the dashboard.
Run this from the rag directory with the venv activated.
"""

import weaviate
from datetime import datetime, timezone
import uuid
import hashlib

# Connect to Weaviate
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051
)

# Sample memories for patient_123
sample_memories = [
    {
        "patient_id": "patient_123",
        "text": "Eleanor loves her morning routine. She wakes up at 7 AM, makes a cup of Earl Grey tea with one sugar, and sits by the window watching the birds in the garden. She has done this every morning for the past 40 years since moving to this house with her late husband Robert.",
        "source": "family_questionnaire",
        "topic": "daily_routine",
        "is_sensitive": False,
        "entities": ["Eleanor", "Earl Grey tea", "Robert", "garden", "birds"],
        "emotion": "positive"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor was a schoolteacher for 35 years at Meadowbrook Elementary. She taught third grade and was beloved by her students. She still receives Christmas cards from former students, some now in their 50s. Teaching was her calling and she often says it was the best decision she ever made.",
        "source": "family_questionnaire",
        "topic": "career",
        "is_sensitive": False,
        "entities": ["Eleanor", "Meadowbrook Elementary", "third grade"],
        "emotion": "positive"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor met Robert at a dance in 1962. He asked her to dance to 'Moon River' and she said yes. They were married for 52 years until Robert passed away in 2015. She keeps his photo on her nightstand and talks to it every night before bed.",
        "source": "family_questionnaire",
        "topic": "family_history",
        "is_sensitive": False,
        "entities": ["Eleanor", "Robert", "Moon River", "1962", "2015"],
        "emotion": "mixed"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor has two children: Margaret (Maggie), 58, who lives in Boston and visits monthly, and Thomas (Tom), 55, who lives nearby and helps with groceries every Wednesday. She has four grandchildren: Sarah, Michael, Emma, and little James who just turned 3.",
        "source": "family_questionnaire",
        "topic": "family_history",
        "is_sensitive": False,
        "entities": ["Margaret", "Maggie", "Thomas", "Tom", "Sarah", "Michael", "Emma", "James", "Boston"],
        "emotion": "positive"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor takes her medications at 8 AM and 8 PM. Morning: Lisinopril for blood pressure, Metformin for diabetes. Evening: Donepezil for memory. She uses a pill organizer that Tom refills every Sunday. She sometimes forgets if she has taken her pills and needs gentle reminders.",
        "source": "caregiver_input",
        "topic": "health_info",
        "is_sensitive": True,
        "entities": ["Lisinopril", "Metformin", "Donepezil", "Tom"],
        "emotion": "neutral"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor loves gardening, especially her rose bushes. The yellow roses were planted by Robert on their 25th anniversary. She spends warm afternoons in the garden, though she now needs help with heavier tasks. The garden brings her peace and connection to Robert's memory.",
        "source": "family_questionnaire",
        "topic": "hobbies",
        "is_sensitive": False,
        "entities": ["roses", "yellow roses", "Robert", "garden"],
        "emotion": "positive"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor prefers to be called 'Ellie' by close family. She dislikes being called 'Mrs. Thompson' as it feels too formal. She responds best to calm, unhurried conversation and becomes anxious when people speak too quickly or there is too much noise.",
        "source": "caregiver_input",
        "topic": "preferences",
        "is_sensitive": False,
        "entities": ["Ellie", "Mrs. Thompson"],
        "emotion": "neutral"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor's happiest memory is the summer of 1985 when the whole family went to Cape Cod. Robert rented a cottage near the beach. The children were young and they built sandcastles every day. She can describe the smell of the salt air and the sound of the waves in vivid detail.",
        "source": "patient_conversation",
        "topic": "positive_memory",
        "is_sensitive": False,
        "entities": ["Cape Cod", "Robert", "1985", "beach", "sandcastles"],
        "emotion": "positive"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor becomes upset when she cannot find her reading glasses. She has multiple pairs but frequently misplaces them. Having a designated spot (the blue bowl on the entry table) helps reduce her anxiety. She also gets distressed in unfamiliar environments.",
        "source": "caregiver_input",
        "topic": "daily_routine",
        "is_sensitive": False,
        "entities": ["reading glasses", "blue bowl", "entry table"],
        "emotion": "negative"
    },
    {
        "patient_id": "patient_123",
        "text": "Eleanor was diagnosed with mild cognitive impairment in 2022, progressing to early-stage Alzheimer's in 2024. She remains largely independent with supervision. She has good days and bad days. Music from the 1950s and 60s often helps her feel calm and connected.",
        "source": "medical_record",
        "topic": "health_info",
        "is_sensitive": True,
        "entities": ["cognitive impairment", "Alzheimer's", "2022", "2024"],
        "emotion": "neutral"
    },
]

def generate_uuid(content: str, patient_id: str) -> str:
    """Generate deterministic UUID from content."""
    hash_input = f"{patient_id}:{content}"
    hash_bytes = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    return str(uuid.UUID(hash_bytes))

try:
    collection = client.collections.get("FortifAiMasterMemory")

    print(f"Adding {len(sample_memories)} sample memories for patient_123...")

    for i, memory in enumerate(sample_memories):
        memory_uuid = generate_uuid(memory["text"], memory["patient_id"])

        properties = {
            "patient_id": memory["patient_id"],
            "text": memory["text"],
            "source": memory["source"],
            "topic": memory["topic"],
            "is_sensitive": memory["is_sensitive"],
            "entities": memory["entities"],
            "emotion": memory["emotion"],
            "chunk_index": 0,
            "total_chunks": 1,
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            collection.data.insert(
                properties=properties,
                uuid=memory_uuid
            )
            print(f"  [{i+1}/{len(sample_memories)}] Added: {memory['topic']} - {memory['text'][:50]}...")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  [{i+1}/{len(sample_memories)}] Already exists: {memory['topic']}")
            else:
                print(f"  [{i+1}/{len(sample_memories)}] Error: {e}")

    # Verify
    count = collection.aggregate.over_all(total_count=True)
    print(f"\nTotal memories in collection: {count.total_count}")

finally:
    client.close()

print("\nDone! You can now test the dashboard with patient_123")
