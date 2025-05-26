# 環境設定とデバッグガイド

## 環境変数の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を設定してください：

```
# API Keys (実際のキーに置き換えてください)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# CORS Configuration
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
APP_RELOAD=true

# Database Configuration
DATABASE_URL=sqlite:///./lovelog.db

# JWT Configuration
SECRET_KEY=your_secret_key_here_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## デバッグ設定

### VS Code でのデバッグ

1. VS Code で F5 キーを押すか、デバッグパネルから以下の設定を選択：
   - **FastAPI Debug**: 直接 main.py を実行
   - **FastAPI with Uvicorn Debug**: Uvicorn サーバーでデバッグ
   - **Alembic Debug**: データベースマイグレーション用

2. ブレークポイントを設定して、コードの実行を止めることができます

### ログファイル

- `logs/app_YYYY-MM-DD.log`: 全般的なログ
- `logs/error_YYYY-MM-DD.log`: エラーログのみ

### 開発用パッケージのインストール

```bash
pip install -r requirements-dev.txt
```

### テストの実行

```bash
# 全テストの実行
pytest

# 詳細な出力でテスト実行
pytest -v

# カバレッジレポート付きでテスト実行
pytest --cov=.

# 特定のテストファイルのみ実行
pytest tests/test_main.py
```

### コードフォーマット

```bash
# Black でコードフォーマット
black .

# isort でインポート文の整理
isort .

# flake8 でコードスタイルチェック
flake8 .
```

## デバッグのコツ

1. **ログの活用**: logger.debug(), logger.info(), logger.error() を使用
2. **ブレークポイント**: VS Code でブレークポイントを設定
3. **テスト駆動開発**: 新機能を追加する前にテストを書く
4. **例外ハンドリング**: try-except ブロックでエラーを適切にキャッチ

## トラブルシューティング

### データベースの問題
```bash
# データベースを再作成
rm lovelog.db
python main.py
```

### マイグレーションの問題
```bash
# Alembic のリビジョンを作成
alembic revision --autogenerate -m "description"

# マイグレーション実行
alembic upgrade head
```

### 依存関係の問題
```bash
# 仮想環境を再作成
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
``` 