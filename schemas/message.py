# schemas/message.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .user import UserPublic

class MessageBase(BaseModel):
    content: str = Field(..., max_length=2000, description="メッセージ内容")
    message_type: str = Field(default="text", description="メッセージタイプ (text/image/file)")
    file_url: Optional[str] = Field(None, description="ファイルURL")

class MessageCreate(MessageBase):
    receiver_id: int = Field(..., description="受信者ユーザーID")

class MessageResponse(MessageBase):
    message_id: int
    sender_id: int
    receiver_id: int
    created_at: datetime
    is_read: bool
    is_deleted: bool
    
    class Config:
        from_attributes = True

class MessageWithSender(MessageResponse):
    """送信者情報を含むメッセージ"""
    sender: UserPublic
    
    class Config:
        from_attributes = True

class MessageReadUpdate(BaseModel):
    """既読状態更新用"""
    message_ids: List[int] = Field(..., min_items=1, description="既読にするメッセージID")

class ConversationResponse(BaseModel):
    """会話履歴のレスポンス"""
    messages: List[MessageWithSender]
    unread_count: int
    partner: UserPublic