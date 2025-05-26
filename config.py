import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # CORS Configuration
    CORS_ALLOW_ORIGINS: List[str] = os.getenv(
        "CORS_ALLOW_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000,https://lovelog-frontend.vercel.app"
    ).split(",")
    
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    CORS_ALLOW_METHODS: List[str] = os.getenv(
        "CORS_ALLOW_METHODS", 
        "GET,POST,PUT,DELETE,OPTIONS"
    ).split(",")
    
    CORS_ALLOW_HEADERS: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
    
    # Application Configuration
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_RELOAD: bool = os.getenv("APP_RELOAD", "true").lower() == "true"

settings = Settings() 