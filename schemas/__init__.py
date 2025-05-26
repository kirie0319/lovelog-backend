# schemas/__init__.py

# カップル用シンプルなスキーマ
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, 
    UserPublic, UserWithPartner, UserLogin, TokenResponse,
    PartnerRequest, PartnerConnectById, PartnerConnectByCode, 
    PartnerSearchResponse, PartnerConnectResponse, InviteCodeResponse,
    PartnerResponse
)

from .message import (
    MessageBase, MessageCreate, MessageResponse,
    MessageWithSender, MessageReadUpdate, ConversationResponse
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", 
    "UserPublic", "UserWithPartner", "UserLogin", "TokenResponse",
    "PartnerRequest", "PartnerConnectById", "PartnerConnectByCode", 
    "PartnerSearchResponse", "PartnerConnectResponse", "InviteCodeResponse",
    "PartnerResponse",
    
    # Message schemas
    "MessageBase", "MessageCreate", "MessageResponse",
    "MessageWithSender", "MessageReadUpdate", "ConversationResponse"
]