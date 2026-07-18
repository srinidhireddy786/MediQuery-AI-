import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# Base directories
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

POLICIES_DIR = os.path.join(
    BASE_DIR,
    "policies"
)

VECTOR_STORE_DIR = os.path.join(
    BASE_DIR,
    "vector_store"
)



# File paths
DB_PATH = os.path.join(
    DATA_DIR,
    "healthcare.db"
)


# FAISS index directory
VECTOR_STORE_PATH = os.path.join(
    VECTOR_STORE_DIR,
    "faiss_policy_index"
)



# API Configuration
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)



# Ollama Configuration
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

OLLAMA_LLM_MODEL = "qwen2.5:3b"



# Ensure directories exist
os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    POLICIES_DIR,
    exist_ok=True
)

os.makedirs(
    VECTOR_STORE_DIR,
    exist_ok=True
)