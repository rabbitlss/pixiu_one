from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.ranking_service import StockRankingService
from pydantic import BaseModel

router = APIRouter()


class RankingResponse(BaseModel):
    """排名响应模型"""
    rank: int
    symbol: str
    name: str
    sector: str
    ranking_type: str
    
    class Config:
        from_attributes = True


class ActivityRankingResponse(RankingResponse):
    """活跃度排名响应"""
    current_price: float
    volume: int
    turnover: float
    activity_score: float


class VolatilityRankingResponse(RankingResponse):
    """波动性排名响应"""
    current_price: float
    daily_range: float
    volatility_percent: float
    volatility_score: float


class PerformanceRankingResponse(RankingResponse):
    """涨跌排名响应"""
    current_price: float
    price_change: float
    percent_change: float
    direction: str
    trend_emoji: str


class MarketCapRankingResponse(RankingResponse):
    """市值排名响应"""
    market_cap: float
    market_cap_billions: float
    current_price: float


class PriceRankingResponse(RankingResponse):
    """价格排名响应"""
    current_price: float
    high: float
    low: float
    daily_change_percent: float


class ComprehensiveRankingResponse(RankingResponse):
    """综合排名响应"""
    current_price: float
    comprehensive_score: float
    dimension_scores: dict


@router.get("/activity", response_model=List[ActivityRankingResponse])
async def get_activity_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取活跃度排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_activity_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/volatility", response_model=List[VolatilityRankingResponse])
async def get_volatility_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取波动性排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_volatility_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/performance", response_model=List[PerformanceRankingResponse])
async def get_performance_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取涨跌排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_performance_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/market-cap", response_model=List[MarketCapRankingResponse])
async def get_market_cap_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取市值排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_market_cap_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/price", response_model=List[PriceRankingResponse])
async def get_price_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取价格排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_price_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/comprehensive", response_model=List[ComprehensiveRankingResponse])
async def get_comprehensive_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取综合排名"""
    ranking_service = StockRankingService(db)
    rankings = await ranking_service.get_comprehensive_ranking(limit)
    
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data found")
    
    return rankings


@router.get("/all")
async def get_all_rankings(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取所有排名数据"""
    ranking_service = StockRankingService(db)
    
    try:
        results = {
            "activity": await ranking_service.get_activity_ranking(limit),
            "volatility": await ranking_service.get_volatility_ranking(limit),
            "performance": await ranking_service.get_performance_ranking(limit),
            "market_cap": await ranking_service.get_market_cap_ranking(limit),
            "price": await ranking_service.get_price_ranking(limit),
            "comprehensive": await ranking_service.get_comprehensive_ranking(limit)
        }
        
        return {
            "success": True,
            "data": results,
            "message": f"Successfully retrieved all rankings with limit {limit}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rankings: {str(e)}")


@router.get("/stats")
async def get_ranking_stats(db: AsyncSession = Depends(get_db)):
    """获取排名统计信息"""
    try:
        from sqlalchemy import text
        
        # 统计基本信息
        stocks_result = await db.execute(text("SELECT COUNT(*) FROM stocks"))
        total_stocks = stocks_result.scalar()
        
        prices_result = await db.execute(text("SELECT COUNT(*) FROM stock_prices"))
        total_prices = prices_result.scalar()
        
        # 获取最新更新时间
        latest_result = await db.execute(text("""
            SELECT MAX(sp.date) as latest_date,
                   COUNT(DISTINCT s.symbol) as active_stocks
            FROM stocks s 
            INNER JOIN stock_prices sp ON s.id = sp.stock_id
            WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
        """))
        latest_row = latest_result.fetchone()
        
        return {
            "total_stocks": total_stocks,
            "total_price_records": total_prices,
            "active_stocks": latest_row[1] if latest_row else 0,
            "latest_update": latest_row[0] if latest_row else None,
            "ranking_types": [
                {"key": "activity", "name": "活跃度排名", "priority": 1},
                {"key": "volatility", "name": "波动性排名", "priority": 2},
                {"key": "performance", "name": "涨跌排名", "priority": 3},
                {"key": "market_cap", "name": "市值排名", "priority": 4},
                {"key": "price", "name": "价格排名", "priority": 5},
                {"key": "comprehensive", "name": "综合排名", "priority": 0}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")