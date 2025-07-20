from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.user import User
from app.models.stock import Stock, StockPrice
from app.schemas.common import SuccessResponse
from app.api.dependencies import get_current_superuser
from app.services.scheduler_service import scheduler_service
from app.services.stock_data_service import StockDataService
from app.services.providers.yfinance_provider import YFinanceProvider
from app.api.v1.endpoints.data_collection import router as data_collection_router

router = APIRouter()

# 包含数据采集路由
router.include_router(data_collection_router, prefix="/data-collection")


@router.post("/update-stock-data", response_model=Dict[str, Any])
async def trigger_stock_data_update(
    background_tasks: BackgroundTasks,
    stock_ids: Optional[List[int]] = None,
    days: int = 30,
    current_user: User = Depends(get_current_superuser)
):
    """
    手动触发股票数据更新（后台任务）
    
    Args:
        stock_ids: 要更新的股票ID列表，None表示更新所有活跃股票
        days: 更新的天数
    """
    # 启动后台任务
    background_tasks.add_task(
        _background_update_stock_data,
        stock_ids,
        days
    )
    
    return {
        "message": "Stock data update started in background",
        "stock_ids": stock_ids,
        "days": days,
        "triggered_by": current_user.username,
        "triggered_at": datetime.now()
    }


async def _background_update_stock_data(stock_ids: Optional[List[int]], days: int):
    """后台任务：更新股票数据"""
    try:
        result = await scheduler_service.trigger_manual_update(stock_ids, days)
        # 这里可以发送通知或记录结果
        print(f"Background update completed: {result}")
    except Exception as e:
        print(f"Background update failed: {e}")


@router.get("/system-status", response_model=Dict[str, Any])
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    获取系统状态信息
    """
    try:
        # 数据库统计
        stats_queries = {
            "total_stocks": select(func.count()).select_from(Stock),
            "active_stocks": select(func.count()).select_from(Stock).where(Stock.is_active == True),
            "total_users": select(func.count()).select_from(User),
            "active_users": select(func.count()).select_from(User).where(User.is_active == True),
            "total_price_records": select(func.count()).select_from(StockPrice)
        }
        
        stats = {}
        for key, query in stats_queries.items():
            result = await db.execute(query)
            stats[key] = result.scalar()
        
        # 最近数据更新时间
        latest_price_result = await db.execute(
            select(StockPrice.created_at)
            .order_by(StockPrice.created_at.desc())
            .limit(1)
        )
        latest_price_update = latest_price_result.scalar_one_or_none()
        
        # 数据库连接状态
        try:
            await db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        
        return {
            "timestamp": datetime.now(),
            "database": {
                "status": db_status,
                "statistics": stats,
                "latest_data_update": latest_price_update
            },
            "scheduler": {
                "running": scheduler_service.running,
                "active_tasks": len(scheduler_service.tasks)
            },
            "system": {
                "uptime_hours": 0,  # 可以实现真实的运行时间统计
                "memory_usage": "N/A",  # 可以集成系统监控
                "cpu_usage": "N/A"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system status: {str(e)}"
        )


@router.post("/add-stock-from-search", response_model=Dict[str, Any])
async def add_stock_from_search(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    通过搜索添加新股票
    """
    try:
        # 检查股票是否已存在
        existing_stock = await db.execute(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        if existing_stock.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock {symbol} already exists"
            )
        
        # 使用数据提供者获取股票信息
        data_provider = YFinanceProvider()
        stock_info = await data_provider.get_stock_info(symbol.upper())
        
        if not stock_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {symbol} not found"
            )
        
        # 创建新股票
        new_stock = Stock(
            symbol=stock_info['symbol'],
            name=stock_info['name'],
            exchange=stock_info.get('exchange'),
            sector=stock_info.get('sector'),
            industry=stock_info.get('industry'),
            market_cap=stock_info.get('market_cap'),
            is_active=True
        )
        
        db.add(new_stock)
        await db.commit()
        await db.refresh(new_stock)
        
        return {
            "message": f"Stock {symbol} added successfully",
            "stock": {
                "id": new_stock.id,
                "symbol": new_stock.symbol,
                "name": new_stock.name,
                "exchange": new_stock.exchange
            },
            "added_by": current_user.username,
            "added_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding stock: {str(e)}"
        )


@router.post("/calculate-indicators/{stock_id}", response_model=SuccessResponse)
async def calculate_technical_indicators(
    stock_id: int,
    background_tasks: BackgroundTasks,
    indicator_types: List[str] = ["MA", "RSI"],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    计算指定股票的技术指标
    """
    # 验证股票存在
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # 启动后台任务计算技术指标
    background_tasks.add_task(
        _background_calculate_indicators,
        stock_id,
        indicator_types
    )
    
    return SuccessResponse(
        message=f"Technical indicators calculation started for {stock.symbol}"
    )


async def _background_calculate_indicators(stock_id: int, indicator_types: List[str]):
    """后台任务：计算技术指标"""
    try:
        data_provider = YFinanceProvider()
        service = StockDataService(data_provider)
        
        result = await service.calculate_technical_indicators(stock_id, indicator_types)
        print(f"Indicators calculation for stock {stock_id}: {'success' if result else 'failed'}")
    except Exception as e:
        print(f"Indicators calculation failed for stock {stock_id}: {e}")


@router.get("/data-quality-report", response_model=Dict[str, Any])
async def get_data_quality_report(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    获取数据质量报告
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 检查数据完整性
        stocks_with_recent_data = await db.execute(
            select(func.count(func.distinct(StockPrice.stock_id)))
            .where(StockPrice.date >= cutoff_date)
        )
        stocks_with_data = stocks_with_recent_data.scalar()
        
        total_active_stocks = await db.execute(
            select(func.count()).select_from(Stock).where(Stock.is_active == True)
        )
        total_stocks = total_active_stocks.scalar()
        
        # 检查数据缺失
        missing_data_stocks = await db.execute(
            select(Stock.id, Stock.symbol, Stock.name)
            .outerjoin(
                StockPrice,
                (Stock.id == StockPrice.stock_id) & (StockPrice.date >= cutoff_date)
            )
            .where(Stock.is_active == True)
            .where(StockPrice.id.is_(None))
            .group_by(Stock.id, Stock.symbol, Stock.name)
        )
        missing_stocks = missing_data_stocks.fetchall()
        
        # 数据新鲜度
        latest_updates = await db.execute(
            select(
                Stock.symbol,
                func.max(StockPrice.date).label('latest_date'),
                func.max(StockPrice.created_at).label('latest_update')
            )
            .join(StockPrice)
            .where(Stock.is_active == True)
            .group_by(Stock.symbol)
            .order_by(func.max(StockPrice.date).desc())
            .limit(10)
        )
        recent_updates = latest_updates.fetchall()
        
        return {
            "report_generated_at": datetime.now(),
            "period_days": days,
            "data_coverage": {
                "total_active_stocks": total_stocks,
                "stocks_with_recent_data": stocks_with_data,
                "coverage_percentage": round((stocks_with_data / total_stocks * 100) if total_stocks > 0 else 0, 2)
            },
            "missing_data": {
                "count": len(missing_stocks),
                "stocks": [{"id": row[0], "symbol": row[1], "name": row[2]} for row in missing_stocks]
            },
            "recent_updates": [
                {
                    "symbol": row[0],
                    "latest_date": row[1],
                    "latest_update": row[2]
                }
                for row in recent_updates
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating data quality report: {str(e)}"
        )


@router.post("/scheduler/start", response_model=SuccessResponse)
async def start_scheduler(
    current_user: User = Depends(get_current_superuser)
):
    """
    启动调度器
    """
    if scheduler_service.running:
        return SuccessResponse(message="Scheduler is already running")
    
    await scheduler_service.start()
    return SuccessResponse(message="Scheduler started successfully")


@router.post("/scheduler/stop", response_model=SuccessResponse)
async def stop_scheduler(
    current_user: User = Depends(get_current_superuser)
):
    """
    停止调度器
    """
    if not scheduler_service.running:
        return SuccessResponse(message="Scheduler is not running")
    
    await scheduler_service.stop()
    return SuccessResponse(message="Scheduler stopped successfully")


@router.get("/scheduler/status", response_model=Dict[str, Any])
async def get_scheduler_status(
    current_user: User = Depends(get_current_superuser)
):
    """
    获取调度器状态
    """
    return {
        "running": scheduler_service.running,
        "active_tasks": len(scheduler_service.tasks),
        "tasks": list(scheduler_service.tasks.keys()) if scheduler_service.tasks else []
    }