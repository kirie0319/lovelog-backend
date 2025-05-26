import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # CORS Configuration - 環境変数必須
    _cors_origins = os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("CORS_ORIGINS")
    if not _cors_origins:
        raise ValueError("CORS_ALLOW_ORIGINS or CORS_ORIGINS environment variable is required")
    
    CORS_ALLOW_ORIGINS: List[str] = [
        origin.strip() for origin in _cors_origins.split(",") if origin.strip()
    ]
    
    _cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS")
    if _cors_credentials is None:
        raise ValueError("CORS_ALLOW_CREDENTIALS environment variable is required")
    CORS_ALLOW_CREDENTIALS: bool = _cors_credentials.lower() == "true"
    
    _cors_methods = os.getenv("CORS_ALLOW_METHODS")
    if not _cors_methods:
        raise ValueError("CORS_ALLOW_METHODS environment variable is required")
    CORS_ALLOW_METHODS: List[str] = [
        method.strip() for method in _cors_methods.split(",") if method.strip()
    ]
    
    _cors_headers = os.getenv("CORS_ALLOW_HEADERS")
    if not _cors_headers:
        raise ValueError("CORS_ALLOW_HEADERS environment variable is required")
    CORS_ALLOW_HEADERS: List[str] = [
        header.strip() for header in _cors_headers.split(",") if header.strip()
    ]
    
    # Application Configuration - 環境変数必須
    APP_HOST: str = os.getenv("APP_HOST")
    if not APP_HOST:
        raise ValueError("APP_HOST environment variable is required")
    
    _app_port = os.getenv("APP_PORT")
    if not _app_port:
        raise ValueError("APP_PORT environment variable is required")
    APP_PORT: int = int(_app_port)
    
    _app_reload = os.getenv("APP_RELOAD")
    if _app_reload is None:
        raise ValueError("APP_RELOAD environment variable is required")
    APP_RELOAD: bool = _app_reload.lower() == "true"
    
    # Database Configuration - 環境変数必須
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # JWT Configuration - 環境変数必須
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    
    ALGORITHM: str = os.getenv("ALGORITHM")
    if not ALGORITHM:
        raise ValueError("ALGORITHM environment variable is required")
    
    _access_token_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    if not _access_token_expire:
        raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES environment variable is required")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_access_token_expire)

settings = Settings()

# デバッグ用：設定値を出力
print(f"Loaded CORS settings:")
print(f"  Origins: {settings.CORS_ALLOW_ORIGINS}")
print(f"  Methods: {settings.CORS_ALLOW_METHODS}")
print(f"  Headers: {settings.CORS_ALLOW_HEADERS}")
print(f"  Credentials: {settings.CORS_ALLOW_CREDENTIALS}") 