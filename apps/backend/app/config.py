from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Nexora AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://nexora:nexora123@localhost:5432/nexora_ai"
    SECRET_KEY: str = "CHANGE_THIS_LATER_IN_ENV"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI Service Configuration
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = "CHANGE_THIS_LATER_IN_ENV"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3-8b-instruct:free"

    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Local Nexora Model Configuration
    NEXORA_MODEL_ID: str = "vishvam26/nexora-qwen3.5-4b-lora-v1"
    NEXORA_BASE_MODEL_ID: str = "Qwen/Qwen2.5-1.5B-Instruct"
    NEXORA_DEVICE: str = "auto"
    NEXORA_MAX_NEW_TOKENS: int = 512
    NEXORA_TEMPERATURE: float = 0.7
    NEXORA_TOP_P: float = 0.9
    HF_TOKEN: str = ""
    HF_HOME: str = ""

    # Memory Configuration
    MAX_HISTORY_MESSAGES: int = 10
    SUMMARY_TRIGGER: int = 20

    # Prompt Configuration
    SYSTEM_PROMPT_PATH: str = "app/prompts/system_prompt.txt"
    DEVELOPER_PROMPT_PATH: str = "app/prompts/developer_prompt.txt"

    # RAG Configuration
    RAG_TOP_K: int = 10
    MAX_CONTEXT_TOKENS: int = 4000
    SIMILARITY_THRESHOLD: float = 0.1
    ENABLE_RERANKING: bool = True
    HYBRID_VECTOR_WEIGHT: float = 0.70
    HYBRID_KEYWORD_WEIGHT: float = 0.30
    GRAPH_MAX_DEPTH: int = 2
    CONFIDENCE_THRESHOLD: float = 0.50

    # Qdrant & Embedding Configuration
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "nexora_chunks"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")





settings = Settings()

import os
if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN

if settings.HF_HOME:
    os.environ["HF_HOME"] = settings.HF_HOME
    # Also set HF_HUB_CACHE to ensure the sub-directories map directly
    os.environ["HF_HUB_CACHE"] = os.path.join(settings.HF_HOME, "hub")



