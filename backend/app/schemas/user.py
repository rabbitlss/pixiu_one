from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from datetime import datetime
from typing import Optional, List
import re


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator("username")
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores and hyphens")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator("username")
    def validate_username(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores and hyphens")
        return v
    
    @validator("password")
    def validate_password(cls, v):
        if v:
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one digit")
            if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
                raise ValueError("Password must contain at least one special character")
        return v


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    hashed_password: str


class WatchlistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="监控列表名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    is_public: bool = Field(False, description="是否公开")


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class Watchlist(WatchlistBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    stock_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)


class WatchlistStockBase(BaseModel):
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class WatchlistStockAdd(WatchlistStockBase):
    stock_id: int


class WatchlistStock(WatchlistStockBase):
    id: int
    watchlist_id: int
    stock_id: int
    added_at: datetime
    stock: Optional["Stock"] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    stock_id: int
    alert_type: str = Field(..., description="预警类型: price_above, price_below, volume_spike等")
    condition_value: float = Field(..., description="触发条件值")
    
    @validator("alert_type")
    def validate_alert_type(cls, v):
        allowed_types = ["price_above", "price_below", "volume_spike", "price_change_percent", "rsi_above", "rsi_below"]
        if v not in allowed_types:
            raise ValueError(f"Alert type must be one of: {', '.join(allowed_types)}")
        return v


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    condition_value: Optional[float] = None
    is_active: Optional[bool] = None


class Alert(AlertBase):
    id: int
    user_id: int
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime
    stock: Optional["Stock"] = None
    
    model_config = ConfigDict(from_attributes=True)


from app.schemas.stock import Stock