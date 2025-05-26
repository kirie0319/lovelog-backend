#!/usr/bin/env python3
"""
Railway本番環境でのマイグレーション修正スクリプト
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError

# 現在の設定を読み込み
from config import settings

def check_and_fix_database():
    """データベースの状態をチェックして修正する"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("Checking database state...")
    
    with engine.connect() as conn:
        try:
            # invite_codeカラムが存在するかチェック
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'invite_code'
            """))
            
            invite_code_exists = result.fetchone() is not None
            
            if not invite_code_exists:
                print("invite_code column does not exist. Adding it...")
                
                # invite_codeカラムを追加
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN invite_code VARCHAR(36)
                """))
                
                # 既存ユーザーにUUIDを生成
                import uuid
                conn.execute(text("""
                    UPDATE users 
                    SET invite_code = gen_random_uuid()::text 
                    WHERE invite_code IS NULL
                """))
                
                # NOT NULL制約を追加
                conn.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN invite_code SET NOT NULL
                """))
                
                # ユニークインデックスを追加
                conn.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_invite_code 
                    ON users (invite_code)
                """))
                
                conn.commit()
                print("✅ invite_code column added successfully!")
            else:
                print("✅ invite_code column already exists!")
            
            # alembic_versionテーブルが存在するかチェック
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            """))
            
            alembic_table_exists = result.fetchone() is not None
            
            if not alembic_table_exists:
                print("Creating alembic_version table...")
                conn.execute(text("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    )
                """))
                
                # 最新のリビジョンをマーク
                conn.execute(text("""
                    INSERT INTO alembic_version (version_num) 
                    VALUES ('f6e5732c8de9')
                """))
                
                conn.commit()
                print("✅ alembic_version table created!")
            else:
                print("✅ alembic_version table already exists!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    check_and_fix_database() 