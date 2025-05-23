# models/message.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, image, file
    file_url = Column(String(255))  # ファイルや画像のURL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_read = Column(Boolean, default=False)  # 既読フラグ
    is_deleted = Column(Boolean, default=False)
    
    # リレーション
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")