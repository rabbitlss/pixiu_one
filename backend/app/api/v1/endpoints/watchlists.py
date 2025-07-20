from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.user import User, Watchlist, WatchlistStock
from app.models.stock import Stock
from app.schemas.user import (
    Watchlist as WatchlistSchema,
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistStock as WatchlistStockSchema,
    WatchlistStockAdd
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.api.dependencies import get_current_active_user, get_pagination

router = APIRouter()


@router.post("/", response_model=WatchlistSchema, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_in: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的监控列表
    """
    # 检查用户是否已有同名监控列表
    existing_watchlist = await db.execute(
        select(Watchlist).where(
            and_(
                Watchlist.user_id == current_user.id,
                Watchlist.name == watchlist_in.name
            )
        )
    )
    if existing_watchlist.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watchlist with this name already exists"
        )
    
    # 创建监控列表
    db_watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_in.name,
        description=watchlist_in.description,
        is_public=watchlist_in.is_public
    )
    
    db.add(db_watchlist)
    await db.commit()
    await db.refresh(db_watchlist)
    
    return db_watchlist


@router.get("/", response_model=PaginatedResponse[WatchlistSchema])
async def list_watchlists(
    include_public: bool = Query(False, description="是否包含公开的监控列表"),
    search: Optional[str] = Query(None, description="搜索监控列表名称"),
    pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取监控列表
    """
    if include_public:
        # 包含用户自己的和公开的监控列表
        query = select(Watchlist).where(
            or_(
                Watchlist.user_id == current_user.id,
                Watchlist.is_public == True
            )
        )
        count_query = select(func.count()).select_from(Watchlist).where(
            or_(
                Watchlist.user_id == current_user.id,
                Watchlist.is_public == True
            )
        )
    else:
        # 只包含用户自己的监控列表
        query = select(Watchlist).where(Watchlist.user_id == current_user.id)
        count_query = select(func.count()).select_from(Watchlist).where(Watchlist.user_id == current_user.id)
    
    # 搜索过滤
    if search:
        search_filter = Watchlist.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询并包含股票数量
    query = (query
             .offset(pagination.skip)
             .limit(pagination.limit)
             .order_by(desc(Watchlist.created_at)))
    
    result = await db.execute(query)
    watchlists = result.scalars().all()
    
    # 为每个监控列表添加股票数量
    watchlist_data = []
    for watchlist in watchlists:
        stock_count_result = await db.execute(
            select(func.count()).select_from(WatchlistStock)
            .where(WatchlistStock.watchlist_id == watchlist.id)
        )
        stock_count = stock_count_result.scalar()
        
        watchlist_dict = WatchlistSchema.model_validate(watchlist).dict()
        watchlist_dict['stock_count'] = stock_count
        watchlist_data.append(WatchlistSchema(**watchlist_dict))
    
    return PaginatedResponse(
        items=watchlist_data,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.get("/{watchlist_id}", response_model=WatchlistSchema)
async def get_watchlist(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定监控列表
    """
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者或公开列表可以查看
    if watchlist.user_id != current_user.id and not watchlist.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取股票数量
    stock_count_result = await db.execute(
        select(func.count()).select_from(WatchlistStock)
        .where(WatchlistStock.watchlist_id == watchlist_id)
    )
    stock_count = stock_count_result.scalar()
    
    watchlist_dict = WatchlistSchema.model_validate(watchlist).dict()
    watchlist_dict['stock_count'] = stock_count
    
    return WatchlistSchema(**watchlist_dict)


@router.put("/{watchlist_id}", response_model=WatchlistSchema)
async def update_watchlist(
    watchlist_id: int,
    watchlist_update: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新监控列表
    """
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者可以修改
    if watchlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 检查新名称是否与其他监控列表重复
    if watchlist_update.name and watchlist_update.name != watchlist.name:
        existing_watchlist = await db.execute(
            select(Watchlist).where(
                and_(
                    Watchlist.user_id == current_user.id,
                    Watchlist.name == watchlist_update.name,
                    Watchlist.id != watchlist_id
                )
            )
        )
        if existing_watchlist.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Watchlist with this name already exists"
            )
    
    # 更新监控列表
    update_data = watchlist_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(watchlist, field, value)
    
    await db.commit()
    await db.refresh(watchlist)
    
    return watchlist


@router.delete("/{watchlist_id}", response_model=SuccessResponse)
async def delete_watchlist(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除监控列表
    """
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者可以删除
    if watchlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await db.delete(watchlist)
    await db.commit()
    
    return SuccessResponse(message="Watchlist deleted successfully")


@router.get("/{watchlist_id}/stocks", response_model=PaginatedResponse[WatchlistStockSchema])
async def get_watchlist_stocks(
    watchlist_id: int,
    pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取监控列表中的股票
    """
    # 验证监控列表存在并检查权限
    watchlist_result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者或公开列表可以查看
    if watchlist.user_id != current_user.id and not watchlist.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取监控列表中的股票
    query = (select(WatchlistStock)
             .where(WatchlistStock.watchlist_id == watchlist_id)
             .options(selectinload(WatchlistStock.stock)))
    
    count_query = (select(func.count())
                   .select_from(WatchlistStock)
                   .where(WatchlistStock.watchlist_id == watchlist_id))
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset(pagination.skip).limit(pagination.limit).order_by(desc(WatchlistStock.added_at))
    result = await db.execute(query)
    watchlist_stocks = result.scalars().all()
    
    return PaginatedResponse(
        items=watchlist_stocks,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.post("/{watchlist_id}/stocks", response_model=WatchlistStockSchema, status_code=status.HTTP_201_CREATED)
async def add_stock_to_watchlist(
    watchlist_id: int,
    stock_data: WatchlistStockAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    向监控列表添加股票
    """
    # 验证监控列表存在并检查权限
    watchlist_result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者可以添加股票
    if watchlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 验证股票存在
    stock_result = await db.execute(select(Stock).where(Stock.id == stock_data.stock_id))
    stock = stock_result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # 检查股票是否已在监控列表中
    existing_stock = await db.execute(
        select(WatchlistStock).where(
            and_(
                WatchlistStock.watchlist_id == watchlist_id,
                WatchlistStock.stock_id == stock_data.stock_id
            )
        )
    )
    if existing_stock.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already in watchlist"
        )
    
    # 添加股票到监控列表
    db_watchlist_stock = WatchlistStock(
        watchlist_id=watchlist_id,
        stock_id=stock_data.stock_id,
        notes=stock_data.notes
    )
    
    db.add(db_watchlist_stock)
    await db.commit()
    await db.refresh(db_watchlist_stock)
    
    # 加载股票信息
    result = await db.execute(
        select(WatchlistStock)
        .where(WatchlistStock.id == db_watchlist_stock.id)
        .options(selectinload(WatchlistStock.stock))
    )
    watchlist_stock = result.scalar_one()
    
    return watchlist_stock


@router.delete("/{watchlist_id}/stocks/{stock_id}", response_model=SuccessResponse)
async def remove_stock_from_watchlist(
    watchlist_id: int,
    stock_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    从监控列表移除股票
    """
    # 验证监控列表存在并检查权限
    watchlist_result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
    
    # 权限检查：只有创建者可以移除股票
    if watchlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 查找监控列表中的股票
    watchlist_stock_result = await db.execute(
        select(WatchlistStock).where(
            and_(
                WatchlistStock.watchlist_id == watchlist_id,
                WatchlistStock.stock_id == stock_id
            )
        )
    )
    watchlist_stock = watchlist_stock_result.scalar_one_or_none()
    
    if not watchlist_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in watchlist"
        )
    
    await db.delete(watchlist_stock)
    await db.commit()
    
    return SuccessResponse(message="Stock removed from watchlist successfully")