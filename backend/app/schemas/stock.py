from pydantic import BaseModel, Field, ConfigDict, validator
from datetime import datetime
from typing import Optional, List


class StockBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    name: str = Field(..., min_length=1, max_length=100, description="股票名称")
    exchange: Optional[str] = Field(None, max_length=50, description="交易所")
    sector: Optional[str] = Field(None, max_length=100, description="行业板块")
    industry: Optional[str] = Field(None, max_length=100, description="细分行业")
    market_cap: Optional[float] = Field(None, gt=0, description="市值")


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    exchange: Optional[str] = Field(None, max_length=50)
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    market_cap: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class Stock(StockBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class StockWithPrices(Stock):
    latest_price: Optional["StockPrice"] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None


class StockPriceBase(BaseModel):
    date: datetime
    open: float = Field(..., gt=0, description="开盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    close: float = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    adjusted_close: Optional[float] = Field(None, gt=0, description="调整后收盘价")


class StockPriceCreate(StockPriceBase):
    stock_id: int


class StockPrice(StockPriceBase):
    id: int
    stock_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockPriceBulkCreate(BaseModel):
    stock_id: int
    prices: List[StockPriceBase]


class TechnicalIndicatorBase(BaseModel):
    date: datetime
    indicator_type: str = Field(..., description="指标类型: MA, EMA, RSI, MACD等")
    period: Optional[int] = Field(None, gt=0, description="计算周期")
    value: float = Field(..., description="指标值")
    signal_value: Optional[float] = Field(None, description="信号值（如MACD信号线）")


class TechnicalIndicatorCreate(TechnicalIndicatorBase):
    stock_id: int


class TechnicalIndicator(TechnicalIndicatorBase):
    id: int
    stock_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockSearchParams(BaseModel):
    symbol: Optional[str] = Field(None, description="股票代码（支持模糊搜索）")
    name: Optional[str] = Field(None, description="股票名称（支持模糊搜索）")
    exchange: Optional[str] = Field(None, description="交易所")
    sector: Optional[str] = Field(None, description="行业板块")
    min_market_cap: Optional[float] = Field(None, gt=0, description="最小市值")
    max_market_cap: Optional[float] = Field(None, gt=0, description="最大市值")
    is_active: Optional[bool] = Field(True, description="是否活跃")
    
    @validator("max_market_cap")
    def validate_market_cap_range(cls, v, values):
        if v and "min_market_cap" in values and values["min_market_cap"]:
            if v < values["min_market_cap"]:
                raise ValueError("max_market_cap must be greater than min_market_cap")
        return v