from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from models import User, Message
import schemas
from database import engine, get_db, Base
from auth import (
    hash_password, authenticate_user, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Couple Chat API", description="カップル専用チャットアプリのAPI")

# 認証関連のエンドポイント
@app.post("/auth/register", response_model=schemas.TokenResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """新規ユーザー登録"""
    # ユーザー名とメールの重複チェック
    db_user = db.query(User).filter(
        (User.username == user.username) | 
        (User.email == user.email)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Username or email already registered"
        )
    
    # パスワードをハッシュ化
    hashed_password = hash_password(user.password)
    
    # ユーザー作成
    db_user = User(
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        profile_image_url=user.profile_image_url,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # アクセストークン生成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
    )
    
    # ユーザー情報を返す
    user_with_partner = schemas.UserWithPartner(
        **db_user.__dict__,
        partner=None,
        has_partner=False
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_with_partner
    )

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """ログイン"""
    user = authenticate_user(user_credentials.username, user_credentials.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクセストークン生成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    
    # パートナー情報を取得
    partner = None
    has_partner = False
    if user.partner_id:
        partner_user = db.query(User).filter(User.user_id == user.partner_id).first()
        if partner_user:
            partner = schemas.UserPublic(
                user_id=partner_user.user_id,
                username=partner_user.username,
                display_name=partner_user.display_name,
                profile_image_url=partner_user.profile_image_url
            )
            has_partner = True
    
    user_with_partner = schemas.UserWithPartner(
        **user.__dict__,
        partner=partner,
        has_partner=has_partner
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_with_partner
    )

# ユーザー関連のエンドポイント
@app.get("/users/me", response_model=schemas.UserWithPartner)
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """現在のユーザー情報とパートナー情報を取得"""
    # パートナー情報も含めて返す
    partner = None
    has_partner = False
    if current_user.partner_id:
        partner_user = db.query(User).filter(User.user_id == current_user.partner_id).first()
        if partner_user:
            partner = schemas.UserPublic(
                user_id=partner_user.user_id,
                username=partner_user.username,
                display_name=partner_user.display_name,
                profile_image_url=partner_user.profile_image_url
            )
            has_partner = True
    
    return schemas.UserWithPartner(
        **current_user.__dict__,
        partner=partner,
        has_partner=has_partner
    )

@app.post("/users/partner-request")
def send_partner_request(
    request: schemas.PartnerRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パートナー申請を送信"""
    # 既にパートナーがいるかチェック
    if current_user.partner_id:
        raise HTTPException(status_code=400, detail="Already have a partner")
    
    # 申請対象のユーザーを検索
    target_user = db.query(User).filter(User.username == request.partner_username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Partner user not found")
    
    # 対象ユーザーが既にパートナーがいるかチェック
    if target_user.partner_id:
        raise HTTPException(status_code=400, detail="Target user already has a partner")
    
    # 自分自身を指定していないかチェック
    if target_user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot send partner request to yourself")
    
    # パートナー関係を設定
    current_user.partner_id = target_user.user_id
    target_user.partner_id = current_user.user_id
    
    db.commit()
    
    return {"message": "Partner connected successfully"}

@app.delete("/users/partner")
def remove_partner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パートナー関係を解除"""
    if not current_user.partner_id:
        raise HTTPException(status_code=400, detail="No partner to remove")
    
    # パートナーも取得
    partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
    
    # パートナー関係を解除
    current_user.partner_id = None
    if partner:
        partner.partner_id = None
    
    db.commit()
    
    return {"message": "Partner relationship removed"}

# メッセージ関連のエンドポイント
@app.post("/messages/", response_model=schemas.MessageWithSender)
def send_message(
    message: schemas.MessageCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メッセージを送信"""
    # 受信者の確認
    receiver = db.query(User).filter(User.user_id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    # パートナー関係の確認
    if current_user.partner_id != receiver.user_id:
        raise HTTPException(status_code=403, detail="Can only send messages to your partner")
    
    # メッセージ作成
    db_message = Message(
        sender_id=current_user.user_id,
        receiver_id=message.receiver_id,
        content=message.content,
        message_type=message.message_type,
        file_url=message.file_url
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # 送信者情報を含めて返す
    return schemas.MessageWithSender(
        **db_message.__dict__,
        sender=schemas.UserPublic(
            user_id=current_user.user_id,
            username=current_user.username,
            display_name=current_user.display_name,
            profile_image_url=current_user.profile_image_url
        )
    )

@app.get("/messages/conversation", response_model=schemas.ConversationResponse)
def get_conversation(
    skip: int = 0, 
    limit: int = 50, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パートナーとの会話履歴を取得"""
    if not current_user.partner_id:
        raise HTTPException(status_code=400, detail="No partner found")
    
    # パートナー情報を取得
    partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # メッセージを取得（双方向）
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.user_id) & (Message.receiver_id == current_user.partner_id)) |
        ((Message.sender_id == current_user.partner_id) & (Message.receiver_id == current_user.user_id))
    ).filter(
        Message.is_deleted == False
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # 未読メッセージ数を取得
    unread_count = db.query(Message).filter(
        Message.sender_id == current_user.partner_id,
        Message.receiver_id == current_user.user_id,
        Message.is_read == False,
        Message.is_deleted == False
    ).count()
    
    # メッセージに送信者情報を追加
    messages_with_sender = []
    for msg in messages:
        sender_info = current_user if msg.sender_id == current_user.user_id else partner
        messages_with_sender.append(
            schemas.MessageWithSender(
                **msg.__dict__,
                sender=schemas.UserPublic(
                    user_id=sender_info.user_id,
                    username=sender_info.username,
                    display_name=sender_info.display_name,
                    profile_image_url=sender_info.profile_image_url
                )
            )
        )
    
    return schemas.ConversationResponse(
        messages=messages_with_sender,
        unread_count=unread_count,
        partner=schemas.UserPublic(
            user_id=partner.user_id,
            username=partner.username,
            display_name=partner.display_name,
            profile_image_url=partner.profile_image_url
        )
    )

@app.put("/messages/read")
def mark_messages_as_read(
    read_update: schemas.MessageReadUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メッセージを既読にする"""
    # 指定されたメッセージを既読にする（自分が受信者のもののみ）
    updated_count = db.query(Message).filter(
        Message.message_id.in_(read_update.message_ids),
        Message.receiver_id == current_user.user_id,
        Message.is_read == False
    ).update({Message.is_read: True}, synchronize_session=False)
    
    db.commit()
    
    return {"message": f"{updated_count} messages marked as read"}

# ヘルスチェック
@app.get("/")
def read_root():
    return {"message": "Couple Chat API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)