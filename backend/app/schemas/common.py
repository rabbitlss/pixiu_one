from pydantic import BaseModel, Field, validator
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(20, ge=1, le=100, description="每页记录数")
    
    @property
    def offset(self) -> int:
        return self.skip


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    
    @property
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit if self.limit > 0 else 0
    
    @property
    def has_next(self) -> bool:
        return self.skip + len(self.items) < self.total
    
    @property
    def has_previous(self) -> bool:
        return self.skip > 0


class SortParams(BaseModel):
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class DateRangeParams(BaseModel):
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    
    @validator("end_date")
    def validate_date_range(cls, v, values):
        if v and "start_date" in values and values["start_date"]:
            if v < values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)