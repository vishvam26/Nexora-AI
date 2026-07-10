from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# Auto-resolve relative SQLite paths to absolute to prevent directory-mismatch issues on Colab/runtimes
db_url = os.environ.get("DATABASE_URL", "")
if db_url == "sqlite:///./nexora_ai.db" or db_url == "sqlite:///nexora_ai.db":
    config_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.dirname(config_dir) # apps/backend/app/ -> apps/backend
    db_file = os.path.join(backend_root, "nexora_ai.db").replace("\\", "/")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    print(f"[Nexora Config] Auto-resolved relative SQLite DATABASE_URL to absolute: {os.environ['DATABASE_URL']}")

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
    GEMINI_MODEL: str = "gemini-2.0-flash"

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

    # Observability Configuration
    SENTRY_DSN: str = ""
    ENABLE_PROMETHEUS: bool = True

    # SMTP Mail Server Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@nexora.ai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN

if settings.HF_HOME:
    os.environ["HF_HOME"] = settings.HF_HOME
    os.environ["HF_HUB_CACHE"] = os.path.join(settings.HF_HOME, "hub")

# Initialize Sentry if DSN is set
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment="production" if not settings.DEBUG else "development",
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        print("[System] Sentry SDK initialized successfully.")
    except ImportError:
        print("[System] Sentry integration skipped: sentry-sdk package not installed.")
    except Exception as e:
        print(f"[System] Failed to initialize Sentry SDK: {e}")
