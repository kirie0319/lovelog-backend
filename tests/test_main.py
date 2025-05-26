import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import logging

# テスト用のSQLiteデータベースを使用
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テスト用のDBセッション
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# テストクライアント
client = TestClient(app)

# ログレベルを設定（テスト中のログを見やすくする）
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope="function")
def setup_database():
    """各テスト前にテーブルを作成し、テスト後に削除"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_read_root():
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Couple Chat API" in response.json()["message"]

def test_register_user(setup_database):
    """ユーザー登録のテスト"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "display_name": "Test User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"

def test_register_duplicate_user(setup_database):
    """重複ユーザー登録のテスト"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "display_name": "Test User"
    }
    
    # 最初の登録
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    # 重複登録（エラーになるはず）
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_user(setup_database):
    """ユーザーログインのテスト"""
    # まずユーザーを登録
    user_data = {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "testpassword123",
        "display_name": "Test User"
    }
    client.post("/auth/register", json=user_data)
    
    # ログインテスト
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"

def test_login_invalid_credentials(setup_database):
    """無効な認証情報でのログインテスト"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"] 