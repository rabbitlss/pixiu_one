from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, TokenWithUser, LoginRequest, ChangePasswordRequest
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.common import SuccessResponse
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    """
    # 检查用户名和邮箱是否已存在
    existing_user = await db.execute(
        select(User).where(
            or_(
                User.username == user_in.username,
                User.email == user_in.email
            )
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # 创建新用户
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenWithUser)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    """
    # 支持用户名或邮箱登录
    result = await db.execute(
        select(User).where(
            or_(
                User.username == login_data.username,
                User.email == login_data.username
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 返回秒数
        user=UserSchema.model_validate(user)
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    """
    # TODO: 实现刷新令牌逻辑
    # 这里需要验证refresh_token并生成新的access_token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented yet"
    )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    修改密码
    """
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return SuccessResponse(message="Password changed successfully")


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出
    
    注意：这是一个占位端点。在实际应用中，你可能需要：
    1. 将令牌加入黑名单
    2. 清除服务器端会话
    3. 记录登出事件
    """
    # TODO: 实现令牌黑名单机制
    return SuccessResponse(message="Logged out successfully")