# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import re

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
    invite_code: str = Field(..., description="招待コード（UUID形式）")
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
    """パートナー申請（ユーザー名で検索）"""
    partner_username: str = Field(..., description="パートナーのユーザー名")

class PartnerConnectByCode(BaseModel):
    """パートナー連携（招待コードで連携）"""
    invite_code: str = Field(..., min_length=36, max_length=36, description="パートナーの招待コード（UUID形式）")
    
    @classmethod
    def validate_invite_code(cls, code: str) -> bool:
        """UUID形式の招待コードかどうかを検証"""
        uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        return bool(uuid_pattern.match(code))

class PartnerConnectById(BaseModel):
    """パートナー連携（IDで直接連携）- 旧バージョン互換性のため残す"""
    partner_id: int = Field(..., description="パートナーのユーザーID")

class PartnerSearchResponse(BaseModel):
    """パートナー検索結果"""
    user_id: int
    username: str
    display_name: str
    profile_image_url: Optional[str] = None
    invite_code: str
    can_connect: bool = True  # 連携可能かどうか
    
class PartnerConnectResponse(BaseModel):
    """パートナー連携成功時のレスポンス"""
    message: str
    partner: UserPublic
    chat_ready: bool = True

class InviteCodeResponse(BaseModel):
    """自分の招待コード情報"""
    invite_code: str
    qr_code_url: Optional[str] = None  # 将来的にQRコード機能追加時用
    message: str

class PartnerResponse(BaseModel):
    """パートナー申請への回答"""
    accept: bool = Field(..., description="承認するかどうか")