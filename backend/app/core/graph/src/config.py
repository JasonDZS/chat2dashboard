import os
from typing import List
from dotenv import load_dotenv

load_dotenv(".env")

class Settings:
    # API settings
    APP_TITLE: str = "Data Visualization Agent"
    APP_VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "debug"  # Options: "debug", "info", "warning", "error", "critical"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = False
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # Database settings
    DATABASES_DIR: str = "databases"
    LOGS_DIR: str = "logs"
    TEMPLATES_DIR: str = "templates"
    
    # Model settings
    LLM_MODEL: str = "deepseek-ai/DeepSeek-V3"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 2048
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # Options: "openai", "hf", "ollama", "custom"
    
    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "Pro/BAAI/bge-m3")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")  # Options: "openai", "hf", "ollama"
    EMBEDDING_DIM: int = 1024  # Default dimension for BGE models
    EMBEDDING_MAX_TOKEN_SIZE: int = 8192  # Default max token size for BGE models
