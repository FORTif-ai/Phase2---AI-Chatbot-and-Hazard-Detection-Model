from simple_llm.agents.delegator import DelegatorClient
from simple_llm.embeddings.openai import openai_embedding
import dotenv

from qdrant_client import QdrantClient, models

dotenv.load_dotenv("keys.env")

client = QdrantClient(path="prompt_db-qdrant")

client.create_collection(
    collection_name="persona-delegation",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
)

db = DelegatorClient(client, "persona-delegation", openai_embedding)

db.build_collection(
    prompts=[
        "diabetes",
        "high blood pressure",
        "high cholesterol",
        "86 years old",
        
        "Stage 2 lung cancer",
        "81 years old",
        "Kidney stones",
        "epilepsy",
    ],
    categories=["1", "1", "1", "1", "2", "2", "2", "2"],
)