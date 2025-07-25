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
    LOG_LEVEL: str = "debug"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = False
    
    # OpenAI settings
    # os.environ['OPENAI_API_BASE'] = 'https://one-api.s.metames.cn:38443/v1'
    # os.environ['OPENAI_API_KEY'] = 'sk-NOwyBUae2bveENbN6d00D57612D349498057Df84CbAeA158'
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    
    # Database settings
    DATABASES_DIR: str = "databases"
    LOGS_DIR: str = "logs"
    TEMPLATES_DIR: str = "templates"
    
    # Model settings
    LLM_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 2048
    
    @property
    def database_path(self) -> str:
        return os.path.abspath(self.DATABASES_DIR)
    
    @property
    def logs_path(self) -> str:
        return os.path.abspath(self.LOGS_DIR)
    
    @property
    def templates_path(self) -> str:
        return os.path.abspath(self.TEMPLATES_DIR)

settings = Settings()