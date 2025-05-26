# models/user.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    profile_image_url = Column(String(255))
    partner_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # 特殊な招待コード（UUID形式）
    invite_code = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    
    # パートナー関係（自己参照）
    partner = relationship("User", remote_side=[user_id], post_update=True)
