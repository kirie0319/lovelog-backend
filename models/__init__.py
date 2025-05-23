# models/__init__.py

# カップル用シンプルなモデル
from .user import User
from .message import Message

# エクスポート
__all__ = [
    "User",
    "Message"
]