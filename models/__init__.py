# models/__init__.py

# カップル用シンプルなモデル
from database import DATABASE_URL, Base
from .user import User
from .message import Message

# エクスポート
__all__ = [
    "Base",
    "User",
    "Message"
]