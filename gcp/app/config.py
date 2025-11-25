from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "GCP AI Education API"
    DEBUG: bool = False
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "serviceAccountKey.json"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"  # or llama3, mistral, etc.
    
    # Paths
    OUTPUT_DIR: str = "outputs"
    QUESTION_PAPERS_DIR: str = "outputs/question_papers"
    TEMP_DATA_DIR: str = "temp_data"
    
    # Settings
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

# Create directories
for dir_path in [settings.OUTPUT_DIR, settings.QUESTION_PAPERS_DIR, settings.TEMP_DATA_DIR]:
    os.makedirs(dir_path, exist_ok=True)