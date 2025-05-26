from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URLの設定（Railwayでの本番環境とローカル開発環境に対応）
DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASE_URLが設定されていない場合のフォールバック
if not DATABASE_URL:
    # ローカル開発環境用のSQLite設定
    DATABASE_URL = "sqlite:///./lovelog.db"

# PostgreSQLのURLがpostgresql://で始まる場合、SQLAlchemyが期待するpostgresql+psycopg2://に変換
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# SQLiteの場合は特別な設定を追加
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()