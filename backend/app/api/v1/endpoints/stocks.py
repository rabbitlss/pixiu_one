from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.stock import Stock, StockPrice, TechnicalIndicator
from app.models.user import User
from app.schemas.stock import (
    Stock as StockSchema,
    StockCreate,
    StockUpdate,
    StockWithPrices,
    StockPrice as StockPriceSchema,
    StockPriceCreate,
    StockPriceBulkCreate,
    TechnicalIndicator as TechnicalIndicatorSchema,
    TechnicalIndicatorCreate,
    StockSearchParams
)
from app.schemas.common import PaginatedResponse, SuccessResponse, DateRangeParams
from app.api.dependencies import get_current_active_user, get_current_superuser, get_pagination

router = APIRouter()


@router.post("/", response_model=StockSchema, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_in: StockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    创建新股票（仅超级用户可用）
    """
    # 检查股票代码是否已存在
    existing_stock = await db.execute(
        select(Stock).where(Stock.symbol == stock_in.symbol.upper())
    )
    if existing_stock.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock with symbol {stock_in.symbol} already exists"
        )
    
    # 创建新股票
    db_stock = Stock(
        symbol=stock_in.symbol.upper(),
        name=stock_in.name,
        exchange=stock_in.exchange,
        sector=stock_in.sector,
        industry=stock_in.industry,
        market_cap=stock_in.market_cap,
        is_active=True
    )
    
    db.add(db_stock)
    await db.commit()
    await db.refresh(db_stock)
    
    return db_stock


@router.get("/", response_model=PaginatedResponse[StockSchema])
async def list_stocks(
    search: Optional[str] = Query(None, description="搜索股票代码或名称"),
    exchange: Optional[str] = Query(None, description="交易所筛选"),
    sector: Optional[str] = Query(None, description="行业板块筛选"),
    is_active: Optional[bool] = Query(True, description="是否活跃"),
    min_market_cap: Optional[float] = Query(None, ge=0, description="最小市值"),
    max_market_cap: Optional[float] = Query(None, ge=0, description="最大市值"),
    sort_by: Optional[str] = Query("symbol", description="排序字段"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="排序方向"),
    pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取股票列表
    """
    query = select(Stock)
    count_query = select(func.count()).select_from(Stock)
    
    # 构建过滤条件
    filters = []
    
    if search:
        search_filter = or_(
            Stock.symbol.ilike(f"%{search.upper()}%"),
            Stock.name.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if exchange:
        filters.append(Stock.exchange == exchange)
    
    if sector:
        filters.append(Stock.sector == sector)
    
    if is_active is not None:
        filters.append(Stock.is_active == is_active)
    
    if min_market_cap is not None:
        filters.append(Stock.market_cap >= min_market_cap)
    
    if max_market_cap is not None:
        filters.append(Stock.market_cap <= max_market_cap)
    
    # 应用过滤条件
    if filters:
        filter_condition = and_(*filters)
        query = query.where(filter_condition)
        count_query = count_query.where(filter_condition)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 排序
    sort_column = getattr(Stock, sort_by, Stock.symbol)
    if sort_order == "desc":
        sort_column = desc(sort_column)
    
    # 分页查询
    query = query.offset(pagination.skip).limit(pagination.limit).order_by(sort_column)
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return PaginatedResponse(
        items=stocks,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.get("/{stock_id}", response_model=StockWithPrices)
async def get_stock(
    stock_id: int,
    include_latest_price: bool = Query(True, description="是否包含最新价格"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取股票详细信息
    """
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    stock_data = StockWithPrices.model_validate(stock)
    
    if include_latest_price:
        # 获取最新价格
        latest_price_result = await db.execute(
            select(StockPrice)
            .where(StockPrice.stock_id == stock_id)
            .order_by(desc(StockPrice.date))
            .limit(1)
        )
        latest_price = latest_price_result.scalar_one_or_none()
        
        if latest_price:
            stock_data.latest_price = latest_price
            
            # 计算24小时价格变化
            yesterday = latest_price.date - timedelta(days=1)
            prev_price_result = await db.execute(
                select(StockPrice)
                .where(
                    and_(
                        StockPrice.stock_id == stock_id,
                        StockPrice.date <= yesterday
                    )
                )
                .order_by(desc(StockPrice.date))
                .limit(1)
            )
            prev_price = prev_price_result.scalar_one_or_none()
            
            if prev_price:
                price_change = latest_price.close - prev_price.close
                price_change_pct = (price_change / prev_price.close) * 100
                stock_data.price_change_24h = price_change
                stock_data.price_change_percentage_24h = price_change_pct
    
    return stock_data


@router.put("/{stock_id}", response_model=StockSchema)
async def update_stock(
    stock_id: int,
    stock_update: StockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    更新股票信息（仅超级用户可用）
    """
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # 更新股票信息
    update_data = stock_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stock, field, value)
    
    await db.commit()
    await db.refresh(stock)
    
    return stock


@router.delete("/{stock_id}", response_model=SuccessResponse)
async def delete_stock(
    stock_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    删除股票（仅超级用户可用）
    """
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    await db.delete(stock)
    await db.commit()
    
    return SuccessResponse(message="Stock deleted successfully")


@router.get("/{stock_id}/prices", response_model=PaginatedResponse[StockPriceSchema])
async def get_stock_prices(
    stock_id: int,
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取股票价格历史
    """
    # 验证股票是否存在
    stock_result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = stock_result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    query = select(StockPrice).where(StockPrice.stock_id == stock_id)
    count_query = select(func.count()).select_from(StockPrice).where(StockPrice.stock_id == stock_id)
    
    # 日期范围过滤
    if start_date:
        query = query.where(StockPrice.date >= start_date)
        count_query = count_query.where(StockPrice.date >= start_date)
    
    if end_date:
        query = query.where(StockPrice.date <= end_date)
        count_query = count_query.where(StockPrice.date <= end_date)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询（按日期倒序）
    query = query.offset(pagination.skip).limit(pagination.limit).order_by(desc(StockPrice.date))
    result = await db.execute(query)
    prices = result.scalars().all()
    
    return PaginatedResponse(
        items=prices,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.post("/{stock_id}/prices", response_model=StockPriceSchema, status_code=status.HTTP_201_CREATED)
async def add_stock_price(
    stock_id: int,
    price_data: StockPriceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    添加股票价格数据（仅超级用户可用）
    """
    # 验证股票是否存在
    stock_result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = stock_result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # 检查该日期的价格数据是否已存在
    existing_price = await db.execute(
        select(StockPrice).where(
            and_(
                StockPrice.stock_id == stock_id,
                StockPrice.date == price_data.date
            )
        )
    )
    if existing_price.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price data for this date already exists"
        )
    
    # 验证价格数据的合理性
    if not (price_data.low <= price_data.open <= price_data.high and
            price_data.low <= price_data.close <= price_data.high):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid price data: open and close must be between low and high"
        )
    
    # 创建价格记录
    db_price = StockPrice(
        stock_id=stock_id,
        date=price_data.date,
        open=price_data.open,
        high=price_data.high,
        low=price_data.low,
        close=price_data.close,
        volume=price_data.volume,
        adjusted_close=price_data.adjusted_close or price_data.close
    )
    
    db.add(db_price)
    await db.commit()
    await db.refresh(db_price)
    
    return db_price


@router.post("/{stock_id}/prices/bulk", response_model=SuccessResponse)
async def add_bulk_stock_prices(
    stock_id: int,
    bulk_data: StockPriceBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    批量添加股票价格数据（仅超级用户可用）
    """
    # 验证股票是否存在
    stock_result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = stock_result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    if not bulk_data.prices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No price data provided"
        )
    
    # 验证并准备数据
    price_objects = []
    dates_seen = set()
    
    for price_data in bulk_data.prices:
        # 检查重复日期
        if price_data.date in dates_seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate date in bulk data: {price_data.date}"
            )
        dates_seen.add(price_data.date)
        
        # 验证价格数据的合理性
        if not (price_data.low <= price_data.open <= price_data.high and
                price_data.low <= price_data.close <= price_data.high):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid price data for date {price_data.date}: open and close must be between low and high"
            )
        
        price_objects.append(StockPrice(
            stock_id=stock_id,
            date=price_data.date,
            open=price_data.open,
            high=price_data.high,
            low=price_data.low,
            close=price_data.close,
            volume=price_data.volume,
            adjusted_close=price_data.adjusted_close or price_data.close
        ))
    
    # 批量插入
    db.add_all(price_objects)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to insert price data. Some dates may already exist."
        )
    
    return SuccessResponse(message=f"Successfully added {len(price_objects)} price records")


@router.get("/{stock_id}/indicators", response_model=PaginatedResponse[TechnicalIndicatorSchema])
async def get_technical_indicators(
    stock_id: int,
    indicator_type: Optional[str] = Query(None, description="指标类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取技术指标数据
    """
    # 验证股票是否存在
    stock_result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = stock_result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    query = select(TechnicalIndicator).where(TechnicalIndicator.stock_id == stock_id)
    count_query = select(func.count()).select_from(TechnicalIndicator).where(TechnicalIndicator.stock_id == stock_id)
    
    # 过滤条件
    if indicator_type:
        query = query.where(TechnicalIndicator.indicator_type == indicator_type)
        count_query = count_query.where(TechnicalIndicator.indicator_type == indicator_type)
    
    if start_date:
        query = query.where(TechnicalIndicator.date >= start_date)
        count_query = count_query.where(TechnicalIndicator.date >= start_date)
    
    if end_date:
        query = query.where(TechnicalIndicator.date <= end_date)
        count_query = count_query.where(TechnicalIndicator.date <= end_date)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset(pagination.skip).limit(pagination.limit).order_by(desc(TechnicalIndicator.date))
    result = await db.execute(query)
    indicators = result.scalars().all()
    
    return PaginatedResponse(
        items=indicators,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )