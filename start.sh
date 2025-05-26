#!/bin/bash
set -e

echo "Starting Lovelog Backend..."

# データベースの状態をチェック・修正
echo "Checking and fixing database state..."
python database_migration_fix.py

# データベースマイグレーションを実行
echo "Running database migrations..."
alembic upgrade head

# マイグレーションが成功したらアプリケーションを起動
echo "Starting application..."
uvicorn main:app --host 0.0.0.0 --port $PORT 