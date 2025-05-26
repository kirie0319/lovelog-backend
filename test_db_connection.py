from database import engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            print("✅ PostgreSQL接続成功！")
            print(f"PostgreSQLバージョン: {version[0]}")
            
            # テーブル一覧を確認
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.fetchall()
            print(f"既存のテーブル数: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        print("以下を確認してください：")
        print("1. .envファイルにDATABASE_URLが正しく設定されているか")
        print("2. RailwayのPostgreSQLサービスが起動しているか")
        print("3. 接続文字列が正しいか")

if __name__ == "__main__":
    test_connection()