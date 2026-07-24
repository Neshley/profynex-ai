"""Configuration management for Profynex AI."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Profynex AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # AI Models
    WHISPER_MODEL: str = "base"
    LLM_MODEL: str = "gpt-3.5-turbo"
    VISION_MODEL: str = "yolov8m"
    TTS_ENGINE: str = "edge-tts"

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None

    # Paths
    DATA_DIR: Path = Path("./user_data")
    MODELS_DIR: Path = Path("./models")
    CACHE_DIR: Path = Path("./cache")
    LOGS_DIR: Path = Path("./logs")

    # Database
    DATABASE_URL: str = "sqlite:///./user_data/profynex.db"
    CHROMA_PATH: str = "./user_data/chroma"

    # Performance
    USE_GPU: bool = True
    CUDA_DEVICE: int = 0
    MAX_WORKERS: int = 4
    CACHE_SIZE: int = 1000

    # Features
    ENABLE_VISION: bool = True
    ENABLE_DESKTOP_CONTROL: bool = True
    ENABLE_VOICE: bool = True
    ENABLE_MEMORY: bool = True
    PRIVACY_MODE: bool = False

    # Character
    CHARACTER_NAME: str = "Aurora"
    CHARACTER_PERSONALITY: str = "friendly"
    CHARACTER_VOICE: str = "female"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()


def get_config() -> Settings:
    """Get global configuration."""
    return settings
