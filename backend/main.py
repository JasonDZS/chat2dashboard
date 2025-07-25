import uvicorn
from app.main import app
from app.config import settings
import os
#####OPEAI_API_SETTING######
os.environ['OPENAI_BASE_URL'] = 'https://one-api.s.metames.cn:38443/v1'
os.environ['OPENAI_API_KEY'] = 'sk-NOwyBUae2bveENbN6d00D57612D349498057Df84CbAeA158'
############################

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT, 
        log_level=settings.LOG_LEVEL
    )