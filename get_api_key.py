import os
from dotenv import load_dotenv

load_dotenv("rag/.env")
print(f"API_KEY={os.getenv('API_KEY')}")
