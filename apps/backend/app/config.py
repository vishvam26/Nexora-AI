from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Nexora AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://nexora:nexora123@localhost:5432/nexora_ai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
