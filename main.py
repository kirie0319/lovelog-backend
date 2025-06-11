from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta, datetime
import uuid
from models import User, Message
import schemas
from database import engine, get_db, Base
from auth import (
    hash_password, authenticate_user, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from config import settings
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from agents.orchestrator import AIOrchestrator
import os

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Couple Chat API", description="カップル専用チャットアプリのAPI")

# CORS設定
print(f"Setting up CORS with origins: {settings.CORS_ALLOW_ORIGINS}")
print(f"CORS credentials: {settings.CORS_ALLOW_CREDENTIALS}")
print(f"CORS methods: {settings.CORS_ALLOW_METHODS}")
print(f"CORS headers: {settings.CORS_ALLOW_HEADERS}")

# より厳密なCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["*"],
    max_age=3600,  # プリフライトキャッシュ時間
)

ai_orchestrator = AIOrchestrator(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    google_cse_id=os.getenv("GOOGLE_CSE_ID")
)

# 明示的なプリフライトリクエストハンドリング
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle preflight OPTIONS requests explicitly"""
    origin = request.headers.get("origin")
    print(f"OPTIONS request from origin: {origin}")
    
    # オリジンが許可リストにあるかチェック
    if origin in settings.CORS_ALLOW_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ",".join(settings.CORS_ALLOW_METHODS),
            "Access-Control-Allow-Headers": ",".join(settings.CORS_ALLOW_HEADERS),
            "Access-Control-Allow-Credentials": "true" if settings.CORS_ALLOW_CREDENTIALS else "false",
            "Access-Control-Max-Age": "3600"
        }
        return JSONResponse(content={"message": "OK"}, headers=headers)
    
    return JSONResponse(content={"message": "CORS not allowed"}, status_code=403)

# リクエストログ用のミドルウェア
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     print(f"Request: {request.method} {request.url}")
#     print(f"Headers: {dict(request.headers)}")
#     response = await call_next(request)
#     print(f"Response status: {response.status_code}")
#     return response

# 認証関連のエンドポイント
@app.post("/auth/register", response_model=schemas.TokenResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """新規ユーザー登録"""
    try:
        print(f"Registration attempt for user: {user.username}, email: {user.email}")
        
        # ユーザー名とメールの重複チェック
        db_user = db.query(User).filter(
            (User.username == user.username) | 
            (User.email == user.email)
        ).first()
        
        if db_user:
            print(f"Duplicate user found: username={db_user.username}, email={db_user.email}")
            raise HTTPException(
                status_code=400, 
                detail="Username or email already registered"
            )
        
        # パスワードをハッシュ化
        hashed_password = hash_password(user.password)
        print("Password hashed successfully")
        
        # 一意の招待コードを生成
        invite_code = str(uuid.uuid4())
        print(f"Generated invite code: {invite_code}")
        
        # ユーザー作成
        db_user = User(
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            profile_image_url=user.profile_image_url,
            password_hash=hashed_password,
            invite_code=invite_code
        )
        
        print("User object created, attempting to save to database...")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"User saved successfully with ID: {db_user.user_id}")
        
        # アクセストークン生成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
        )
        print("Access token created successfully")
        
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
        
    except HTTPException:
        # HTTPExceptionは再発生させる
        raise
    except Exception as e:
        print(f"Unexpected error during registration: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """ログイン"""
    try:
        print(f"Login attempt for user: {user_credentials.username}")
        
        user = authenticate_user(user_credentials.username, user_credentials.password, db)
        if not user:
            print(f"Authentication failed for user: {user_credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"User authenticated successfully: {user.username}")
        
        # アクセストークン生成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.user_id)}, expires_delta=access_token_expires
        )
        print("Access token created successfully")
        
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
        
        print(f"Login successful for user: {user.username}")
        return schemas.TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_with_partner
        )
        
    except HTTPException:
        # HTTPExceptionは再発生させる
        raise
    except Exception as e:
        print(f"Unexpected error during login: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
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

@app.get("/users/my-invite-code", response_model=schemas.InviteCodeResponse)
def get_my_invite_code(current_user: User = Depends(get_current_user)):
    """自分の招待コードを取得"""
    return schemas.InviteCodeResponse(
        invite_code=current_user.invite_code,
        message="Share this invite code with your partner to connect!"
    )

@app.post("/users/regenerate-invite-code", response_model=schemas.InviteCodeResponse)
def regenerate_invite_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """招待コードを再生成（セキュリティ上の理由で変更したい場合）"""
    # 既にパートナーがいる場合は再生成を拒否
    if current_user.partner_id:
        raise HTTPException(
            status_code=400, 
            detail="Cannot regenerate invite code while having a partner"
        )
    
    # 新しい招待コードを生成
    new_invite_code = str(uuid.uuid4())
    current_user.invite_code = new_invite_code
    
    db.commit()
    
    return schemas.InviteCodeResponse(
        invite_code=new_invite_code,
        message="New invite code generated successfully!"
    )

# パートナー関連のエンドポイント
@app.get("/users/search-by-code/{invite_code}", response_model=schemas.PartnerSearchResponse)
def search_user_by_invite_code(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """招待コードでユーザーを検索（パートナー連携用）"""
    # 招待コードの形式を検証
    if not schemas.PartnerConnectByCode.validate_invite_code(invite_code):
        raise HTTPException(status_code=400, detail="Invalid invite code format")
    
    # 検索対象ユーザーの取得
    target_user = db.query(User).filter(User.invite_code == invite_code).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with this invite code")
    
    # 自分自身を検索していないかチェック
    if target_user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot search yourself")
    
    # 連携可能かどうかを判定
    can_connect = True
    if current_user.partner_id or target_user.partner_id:
        can_connect = False
    
    return schemas.PartnerSearchResponse(
        user_id=target_user.user_id,
        username=target_user.username,
        display_name=target_user.display_name,
        profile_image_url=target_user.profile_image_url,
        invite_code=target_user.invite_code,
        can_connect=can_connect
    )

@app.post("/users/partner-connect-by-code", response_model=schemas.PartnerConnectResponse)
def connect_partner_by_invite_code(
    request: schemas.PartnerConnectByCode,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """招待コードで直接連携（即座にチャット開始可能）"""
    # 既にパートナーがいるかチェック
    if current_user.partner_id:
        raise HTTPException(status_code=400, detail="Already have a partner")
    
    # 招待コードの形式を検証
    if not schemas.PartnerConnectByCode.validate_invite_code(request.invite_code):
        raise HTTPException(status_code=400, detail="Invalid invite code format")
    
    # 連携対象のユーザーを取得
    target_user = db.query(User).filter(User.invite_code == request.invite_code).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with this invite code")
    
    # 対象ユーザーが既にパートナーがいるかチェック
    if target_user.partner_id:
        raise HTTPException(status_code=400, detail="Target user already has a partner")
    
    # 自分自身を指定していないかチェック
    if target_user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
    
    # パートナー関係を設定（双方向）
    current_user.partner_id = target_user.user_id
    target_user.partner_id = current_user.user_id
    
    db.commit()
    
    # パートナー情報を返す
    partner_info = schemas.UserPublic(
        user_id=target_user.user_id,
        username=target_user.username,
        display_name=target_user.display_name,
        profile_image_url=target_user.profile_image_url
    )
    
    return schemas.PartnerConnectResponse(
        message="Partner connected successfully! You can now start chatting.",
        partner=partner_info,
        chat_ready=True
    )

@app.get("/users/search/{user_id}", response_model=schemas.PartnerSearchResponse)
def search_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーIDでユーザーを検索（旧バージョン互換性のため残す）"""
    # 検索対象ユーザーの取得
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 自分自身を検索していないかチェック
    if target_user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot search yourself")
    
    # 連携可能かどうかを判定
    can_connect = True
    if current_user.partner_id or target_user.partner_id:
        can_connect = False
    
    return schemas.PartnerSearchResponse(
        user_id=target_user.user_id,
        username=target_user.username,
        display_name=target_user.display_name,
        profile_image_url=target_user.profile_image_url,
        invite_code=target_user.invite_code,
        can_connect=can_connect
    )

@app.post("/users/partner-connect-by-id", response_model=schemas.PartnerConnectResponse)
def connect_partner_by_id(
    request: schemas.PartnerConnectById,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パートナーIDで直接連携（旧バージョン互換性のため残す）"""
    # 既にパートナーがいるかチェック
    if current_user.partner_id:
        raise HTTPException(status_code=400, detail="Already have a partner")
    
    # 連携対象のユーザーを取得
    target_user = db.query(User).filter(User.user_id == request.partner_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Partner user not found")
    
    # 対象ユーザーが既にパートナーがいるかチェック
    if target_user.partner_id:
        raise HTTPException(status_code=400, detail="Target user already has a partner")
    
    # 自分自身を指定していないかチェック
    if target_user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
    
    # パートナー関係を設定（双方向）
    current_user.partner_id = target_user.user_id
    target_user.partner_id = current_user.user_id
    
    db.commit()
    
    # パートナー情報を返す
    partner_info = schemas.UserPublic(
        user_id=target_user.user_id,
        username=target_user.username,
        display_name=target_user.display_name,
        profile_image_url=target_user.profile_image_url
    )
    
    return schemas.PartnerConnectResponse(
        message="Partner connected successfully! You can now start chatting.",
        partner=partner_info,
        chat_ready=True
    )

@app.post("/users/partner-request")
def send_partner_request(
    request: schemas.PartnerRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パートナー申請を送信（ユーザー名で検索）"""
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

@app.get("/users/partner-status")
def get_partner_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """現在のパートナー状態を取得"""
    if not current_user.partner_id:
        return {
            "has_partner": False,
            "message": "No partner connected",
            "can_chat": False
        }
    
    partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
    if not partner:
        # パートナーが存在しない場合（データ整合性の問題）
        current_user.partner_id = None
        db.commit()
        return {
            "has_partner": False,
            "message": "Partner not found, connection reset",
            "can_chat": False
        }
    
    return {
        "has_partner": True,
        "partner": {
            "user_id": partner.user_id,
            "username": partner.username,
            "display_name": partner.display_name,
            "profile_image_url": partner.profile_image_url
        },
        "can_chat": True,
        "message": "Ready to chat!"
    }

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
    # パートナーがいるかチェック
    if not current_user.partner_id:
        raise HTTPException(status_code=400, detail="No partner found")
    
    # パートナー情報を取得
    partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # メッセージ作成（receiver_idは自動的にパートナーIDに設定）
    db_message = Message(
        sender_id=current_user.user_id,
        receiver_id=current_user.partner_id,  # 自動的にパートナーIDを設定
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

# CORS設定確認用エンドポイント（デバッグ用）
@app.get("/debug/cors")
def debug_cors():
    """CORS設定を確認するためのデバッグエンドポイント"""
    return {
        "cors_origins": settings.CORS_ALLOW_ORIGINS,
        "cors_methods": settings.CORS_ALLOW_METHODS,
        "cors_headers": settings.CORS_ALLOW_HEADERS,
        "cors_credentials": settings.CORS_ALLOW_CREDENTIALS,
        "message": "CORS configuration"
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    print(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())}
    )

@app.post("/ai/suggest-plans")
async def ai_suggest_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AIボタンが押された時の処理"""
    try:
        # パートナーがいるかチェック
        if not current_user.partner_id:
            raise HTTPException(status_code=400, detail="パートナーが見つかりません")
        
        # パートナー情報を取得
        partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
        if not partner:
            raise HTTPException(status_code=400, detail="パートナー情報が見つかりません")
        
        # 直近の会話履歴を取得（最新50件を時系列順で）
        messages = db.query(Message).filter(
            ((Message.sender_id == current_user.user_id) & (Message.receiver_id == current_user.partner_id)) |
            ((Message.sender_id == current_user.partner_id) & (Message.receiver_id == current_user.user_id))
        ).filter(
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).limit(50).all()
        
        # メッセージが少ない場合の警告
        if len(messages) < 5:
            return {
                "success": False,
                "error": "insufficient_messages",
                "message": "AIが提案を作成するには、もう少し会話が必要です。パートナーともっとお話ししてから再度お試しください。",
                "messages_count": len(messages),
                "minimum_required": 5
            }
        
        # メッセージを辞書形式に変換（時系列順に並び替え）
        message_dicts = []
        for msg in reversed(messages):  # 時系列順に並び替え
            # 送信者情報を取得
            if msg.sender_id == current_user.user_id:
                sender_info = current_user
            else:
                sender_info = partner
            
            message_dicts.append({
                "message_id": msg.message_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "message_type": msg.message_type,
                "sender": {
                    "user_id": sender_info.user_id,
                    "display_name": sender_info.display_name,
                    "username": sender_info.username
                }
            })
        
        # AIオーケストレーターで処理（デバッグモード有効）
        result = await ai_orchestrator.process_ai_request(message_dicts)
        
        # 処理結果にメタ情報を追加
        result["processing_info"] = {
            "messages_analyzed": len(message_dicts),
            "conversation_participants": [
                {
                    "user_id": current_user.user_id,
                    "display_name": current_user.display_name,
                    "role": "current_user"
                },
                {
                    "user_id": partner.user_id,
                    "display_name": partner.display_name,
                    "role": "partner"
                }
            ],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"AI処理中にエラーが発生しました: {str(e)}"
        )

# テスト用の簡単なAIエンドポイント
@app.post("/ai/test")
async def ai_test(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AIシステムの基本テスト"""
    try:
        # OpenAI APIキーが設定されているかチェック
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY not configured",
                "message": "OpenAI APIキーが設定されていません"
            }
        
        # Google Search APIの設定確認
        google_key = os.getenv("GOOGLE_API_KEY")
        google_cse = os.getenv("GOOGLE_CSE_ID")
        search_available = bool(google_key and google_cse)
        
        # より詳細なテストメッセージ（検索しやすい内容）
        test_messages = [
            {
                "message_id": 1,
                "content": "今度の週末、渋谷でイタリアンレストランに行きたいね",
                "created_at": "2024-01-01T12:00:00",
                "message_type": "text",
                "sender": {
                    "user_id": 1,
                    "display_name": "太郎",
                    "username": "taro"
                }
            },
            {
                "message_id": 2,
                "content": "いいね！パスタが美味しいところがいいな",
                "created_at": "2024-01-01T12:01:00", 
                "message_type": "text",
                "sender": {
                    "user_id": 2,
                    "display_name": "花子",
                    "username": "hanako"
                }
            },
            {
                "message_id": 3,
                "content": "予算は一人3000円くらいで考えてる",
                "created_at": "2024-01-01T12:02:00",
                "message_type": "text",
                "sender": {
                    "user_id": 1,
                    "display_name": "太郎",
                    "username": "taro"
                }
            },
            {
                "message_id": 4,
                "content": "雰囲気の良いところだと嬉しいな",
                "created_at": "2024-01-01T12:03:00",
                "message_type": "text",
                "sender": {
                    "user_id": 2,
                    "display_name": "花子",
                    "username": "hanako"
                }
            },
            {
                "message_id": 5,
                "content": "渋谷駅から歩いて行けるところがいいね",
                "created_at": "2024-01-01T12:04:00",
                "message_type": "text",
                "sender": {
                    "user_id": 1,
                    "display_name": "太郎",
                    "username": "taro"
                }
            },
            {
                "message_id": 6,
                "content": "土曜日の夜7時頃からでどう？",
                "created_at": "2024-01-01T12:05:00",
                "message_type": "text",
                "sender": {
                    "user_id": 2,
                    "display_name": "花子",
                    "username": "hanako"
                }
            }
        ]
        
        # AIオーケストレーターで処理（デバッグモード有効）
        result = await ai_orchestrator.process_ai_request(test_messages)
        
        # テスト情報を追加
        result["test_info"] = {
            "test_type": "basic_ai_functionality",
            "test_messages_count": len(test_messages),
            "openai_api_configured": bool(openai_key),
            "google_search_configured": search_available,
            "test_timestamp": datetime.now().isoformat(),
            "test_scenario": "カップルの渋谷イタリアンレストラン検索"
        }
        
        return result
        
    except Exception as e:
        print(f"AI テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "AIテスト中にエラーが発生しました",
            "test_info": {
                "test_type": "basic_ai_functionality",
                "test_timestamp": datetime.now().isoformat(),
                "error_occurred": True
            }
        }

# Google検索専用テストエンドポイント
@app.post("/ai/test-search")
async def test_google_search(
    current_user: User = Depends(get_current_user)
):
    """Google検索機能の単体テスト"""
    try:
        # Google Search APIの設定確認
        google_key = os.getenv("GOOGLE_API_KEY")
        google_cse = os.getenv("GOOGLE_CSE_ID")
        
        if not google_key or not google_cse:
            return {
                "success": False,
                "error": "google_search_not_configured",
                "message": "Google Search APIが設定されていません。GOOGLE_API_KEYとGOOGLE_CSE_IDを設定してください。",
                "configuration": {
                    "google_api_key_set": bool(google_key),
                    "google_cse_id_set": bool(google_cse)
                }
            }
        
        # Google検索エージェントを初期化
        search_agent = ai_orchestrator.search_agent
        if not search_agent:
            return {
                "success": False,
                "error": "search_agent_not_available",
                "message": "検索エージェントが初期化されていません"
            }
        
        # テスト用検索キーワード
        test_keywords = [
            "渋谷 イタリアン 3000円 おすすめ",
            "新宿 カフェ デート 人気",
            "東京 レストラン ランチ 評価"
        ]
        
        print(f"\n{'🔍'*20} Google検索テスト開始 {'🔍'*20}")
        print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"テストキーワード数: {len(test_keywords)}個")
        print(f"{'🔍'*50}")
        
        # 検索実行
        search_results = await search_agent.search_information(test_keywords)
        
        # 結果の分析
        total_results = 0
        successful_searches = 0
        failed_searches = 0
        
        for keyword, result in search_results.items():
            if isinstance(result, list) and len(result) > 0:
                successful_searches += 1
                total_results += len(result)
            else:
                failed_searches += 1
        
        print(f"\n{'✅'*20} Google検索テスト完了 {'✅'*20}")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"成功: {successful_searches}件, 失敗: {failed_searches}件")
        print(f"総取得結果: {total_results}件")
        print(f"{'✅'*50}")
        
        return {
            "success": True,
            "search_results": search_results,
            "test_summary": {
                "total_keywords": len(test_keywords),
                "successful_searches": successful_searches,
                "failed_searches": failed_searches,
                "total_results": total_results,
                "test_timestamp": datetime.now().isoformat()
            },
            "test_keywords": test_keywords,
            "message": f"Google検索テストが完了しました。{total_results}件の結果を取得しました。"
        }
        
    except Exception as e:
        print(f"Google検索テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Google検索テスト中にエラーが発生しました",
            "test_timestamp": datetime.now().isoformat()
        }

# デバッグ専用エンドポイント
@app.post("/ai/debug/conversation-analysis")
async def debug_conversation_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """会話分析エージェントのデバッグ用エンドポイント"""
    try:
        if not current_user.partner_id:
            raise HTTPException(status_code=400, detail="パートナーが見つかりません")
        
        partner = db.query(User).filter(User.user_id == current_user.partner_id).first()
        if not partner:
            raise HTTPException(status_code=400, detail="パートナー情報が見つかりません")
        
        # 会話履歴を取得
        messages = db.query(Message).filter(
            ((Message.sender_id == current_user.user_id) & (Message.receiver_id == current_user.partner_id)) |
            ((Message.sender_id == current_user.partner_id) & (Message.receiver_id == current_user.user_id))
        ).filter(
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).limit(50).all()
        
        # メッセージを辞書形式に変換
        message_dicts = []
        for msg in reversed(messages):
            sender_info = current_user if msg.sender_id == current_user.user_id else partner
            message_dicts.append({
                "message_id": msg.message_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "message_type": msg.message_type,
                "sender": {
                    "user_id": sender_info.user_id,
                    "display_name": sender_info.display_name,
                    "username": sender_info.username
                }
            })
        
        # 会話分析エージェントのみを実行
        analyzer = ai_orchestrator.conversation_analyzer
        analysis_result = await analyzer.analyze_conversation(message_dicts)
        
        return {
            "success": True,
            "agent": "ConversationAnalyzer",
            "input_messages_count": len(message_dicts),
            "analysis_result": analysis_result,
            "debug_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "agent": "ConversationAnalyzer"
        }

@app.post("/ai/debug/intent-understanding")
async def debug_intent_understanding():
    """意図理解エージェントのデバッグ用エンドポイント"""
    try:
        # サンプル分析結果
        sample_analysis = {
            "topics": ["レストラン", "デート", "週末の予定"],
            "locations": ["渋谷", "新宿"],
            "preferences": ["イタリアン", "パスタ"],
            "budget": "一人3000円程度",
            "mood": "楽しそう、積極的"
        }
        
        # 意図理解エージェントのみを実行
        intent_agent = ai_orchestrator.intent_agent
        intent_result = await intent_agent.understand_intent(sample_analysis)
        
        return {
            "success": True,
            "agent": "IntentUnderstandingAgent",
            "input_analysis": sample_analysis,
            "intent_result": intent_result,
            "debug_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "agent": "IntentUnderstandingAgent"
        }

@app.post("/ai/debug/thinking")
async def debug_thinking():
    """思考エージェントのデバッグ用エンドポイント"""
    try:
        # サンプル意図理解結果
        sample_intent = {
            "support_type": "レストラン・食事の提案",
            "budget_range": "一人3000円程度",
            "location_constraints": ["渋谷", "新宿"],
            "preferences": ["イタリアン", "パスタ", "雰囲気の良い店"]
        }
        
        # 思考エージェントのみを実行
        thinking_agent = ai_orchestrator.thinking_agent
        thinking_result = await thinking_agent.think_and_plan(sample_intent)
        
        return {
            "success": True,
            "agent": "ThinkingAgent",
            "input_intent": sample_intent,
            "thinking_result": thinking_result,
            "debug_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "agent": "ThinkingAgent"
        }

@app.post("/ai/debug/plan-suggestion")
async def debug_plan_suggestion():
    """プラン提案エージェントのデバッグ用エンドポイント"""
    try:
        # サンプル思考結果
        sample_thinking = {
            "search_keywords": ["渋谷 イタリアン 3000円", "新宿 パスタ おすすめ"],
            "proposal_direction": "雰囲気の良いイタリアンレストラン",
            "constraints": ["予算3000円以内", "渋谷・新宿エリア"]
        }
        
        # サンプル検索結果
        sample_search = {
            "渋谷 イタリアン 3000円": [
                {"title": "イタリアンレストランA", "snippet": "渋谷の人気イタリアン"}
            ]
        }
        
        # プラン提案エージェントのみを実行
        plan_agent = ai_orchestrator.plan_agent
        plan_result = await plan_agent.suggest_plans(sample_thinking, sample_search)
        
        return {
            "success": True,
            "agent": "PlanSuggestionAgent",
            "input_thinking": sample_thinking,
            "input_search": sample_search,
            "plan_result": plan_result,
            "debug_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "agent": "PlanSuggestionAgent"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="warning",  # エラーレベルを warning に設定してアクセスログを減らす
        access_log=False      # アクセスログを完全に無効化
    )