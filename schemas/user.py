# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    display_name: str = Field(..., min_length=1, max_length=100, description="表示名")
    profile_image_url: Optional[str] = Field(None, description="プロフィール画像URL")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="パスワード（8文字以上）")

class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_image_url: Optional[str] = None

class UserResponse(UserBase):
    user_id: int
    partner_id: Optional[int] = None
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True

class UserPublic(BaseModel):
    """公開用のユーザー情報"""
    user_id: int
    username: str
    display_name: str
    profile_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserWithPartner(UserResponse):
    """パートナー情報を含むユーザー情報"""
    partner: Optional[UserPublic] = None
    has_partner: bool = False
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str = Field(..., description="ユーザー名またはメールアドレス")
    password: str = Field(..., description="パスワード")

class TokenResponse(BaseModel):
    """ログイン成功時のレスポンス"""
    access_token: str
    token_type: str
    user: UserWithPartner

class PartnerRequest(BaseModel):
    """パートナー申請"""
    partner_username: str = Field(..., description="パートナーのユーザー名")

class PartnerResponse(BaseModel):
    """パートナー申請への回答"""
    accept: bool = Field(..., description="承認するかどうか")