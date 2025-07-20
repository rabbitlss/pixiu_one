from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import User


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: list[str] = []


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=1)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="密码重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128)


class EmailRequest(BaseModel):
    email: str = Field(..., description="用户邮箱")