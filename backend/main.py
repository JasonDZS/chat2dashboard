import uvicorn
import os
from app.main import app
from app.config import settings


if __name__ == "__main__":
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY}")
    print(f"OpenAI API Base: {settings.OPENAI_API_BASE}")
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT, 
        log_level=settings.LOG_LEVEL
    )