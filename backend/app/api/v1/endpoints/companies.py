from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user, get_db
from app.models import User, Company, FinancialMetrics, MarketPosition, CorporateAction, ESGMetrics, AnalystRating
from app.schemas.company import (
    Company as CompanySchema,
    CompanyCreate,
    CompanyUpdate,
    CompanyDetailResponse,
    CompanySearchResponse,
    FinancialMetrics as FinancialMetricsSchema,
    FinancialMetricsCreate,
    MarketPosition as MarketPositionSchema,
    MarketPositionCreate,
    CorporateAction as CorporateActionSchema,
    CorporateActionCreate,
    ESGMetrics as ESGMetricsSchema,
    ESGMetricsCreate,
    AnalystRating as AnalystRatingSchema,
    AnalystRatingCreate
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=CompanySearchResponse)
async def get_companies(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sector: Optional[str] = Query(None, description="板块筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    country: Optional[str] = Query(None, description="国家筛选"),
    min_market_cap: Optional[float] = Query(None, description="最小市值"),
    max_market_cap: Optional[float] = Query(None, description="最大市值"),
):
    """获取公司列表"""
    
    # 构建查询
    query = select(Company)
    
    # 添加搜索条件
    conditions = []
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Company.company_name.ilike(search_pattern),
                Company.ticker_symbol.ilike(search_pattern),
                Company.business_summary.ilike(search_pattern)
            )
        )
    
    if sector:
        conditions.append(Company.sector == sector)
    
    if industry:
        conditions.append(Company.industry == industry)
        
    if country:
        conditions.append(Company.country == country)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(Company)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset(skip).limit(limit).order_by(Company.company_name)
    result = await db.execute(query)
    companies = result.scalars().all()
    
    # 计算分页信息
    pages = (total + limit - 1) // limit
    
    return CompanySearchResponse(
        items=[CompanySchema.model_validate(company) for company in companies],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=pages
    )


@router.post("/", response_model=CompanySchema)
async def create_company(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_in: CompanyCreate
):
    """创建公司信息"""
    
    # 检查股票是否已经有关联的公司
    existing_query = select(Company).where(Company.stock_id == company_in.stock_id)
    existing_result = await db.execute(existing_query)
    existing_company = existing_result.scalar_one_or_none()
    
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该股票已有关联的公司信息"
        )
    
    # 检查ticker_symbol是否唯一
    ticker_query = select(Company).where(Company.ticker_symbol == company_in.ticker_symbol)
    ticker_result = await db.execute(ticker_query)
    ticker_company = ticker_result.scalar_one_or_none()
    
    if ticker_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该股票代码已存在"
        )
    
    # 创建公司
    company = Company(**company_in.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    return CompanySchema.model_validate(company)


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int
):
    """获取公司详细信息"""
    
    # 获取公司基本信息
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 获取最新财务指标
    financial_query = (
        select(FinancialMetrics)
        .where(FinancialMetrics.company_id == company_id)
        .order_by(desc(FinancialMetrics.report_date))
        .limit(1)
    )
    financial_result = await db.execute(financial_query)
    latest_financial = financial_result.scalar_one_or_none()
    
    # 获取最新市场地位
    market_query = (
        select(MarketPosition)
        .where(MarketPosition.company_id == company_id)
        .order_by(desc(MarketPosition.analysis_date))
        .limit(1)
    )
    market_result = await db.execute(market_query)
    latest_market = market_result.scalar_one_or_none()
    
    # 获取最近的公司行为
    actions_query = (
        select(CorporateAction)
        .where(CorporateAction.company_id == company_id)
        .order_by(desc(CorporateAction.ex_date))
        .limit(5)
    )
    actions_result = await db.execute(actions_query)
    recent_actions = actions_result.scalars().all()
    
    # 获取最新ESG指标
    esg_query = (
        select(ESGMetrics)
        .where(ESGMetrics.company_id == company_id)
        .order_by(desc(ESGMetrics.assessment_date))
        .limit(1)
    )
    esg_result = await db.execute(esg_query)
    latest_esg = esg_result.scalar_one_or_none()
    
    # 获取最近的分析师评级
    rating_query = (
        select(AnalystRating)
        .where(AnalystRating.company_id == company_id)
        .order_by(desc(AnalystRating.rating_date))
        .limit(5)
    )
    rating_result = await db.execute(rating_query)
    recent_ratings = rating_result.scalars().all()
    
    return CompanyDetailResponse(
        **CompanySchema.model_validate(company).model_dump(),
        latest_financial_metrics=FinancialMetricsSchema.model_validate(latest_financial) if latest_financial else None,
        latest_market_position=MarketPositionSchema.model_validate(latest_market) if latest_market else None,
        recent_corporate_actions=[CorporateActionSchema.model_validate(action) for action in recent_actions],
        latest_esg_metrics=ESGMetricsSchema.model_validate(latest_esg) if latest_esg else None,
        recent_analyst_ratings=[AnalystRatingSchema.model_validate(rating) for rating in recent_ratings]
    )


@router.put("/{company_id}", response_model=CompanySchema)
async def update_company(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    company_in: CompanyUpdate
):
    """更新公司信息"""
    
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 更新字段
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    
    return CompanySchema.model_validate(company)


@router.delete("/{company_id}")
async def delete_company(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int
):
    """删除公司信息"""
    
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    await db.delete(company)
    await db.commit()
    
    return {"message": "公司信息已删除"}


# 财务指标相关端点
@router.get("/{company_id}/financial-metrics", response_model=List[FinancialMetricsSchema])
async def get_financial_metrics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    period_type: Optional[str] = Query(None, description="报告期类型"),
    fiscal_year: Optional[int] = Query(None, description="财年"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数")
):
    """获取公司财务指标"""
    
    query = select(FinancialMetrics).where(FinancialMetrics.company_id == company_id)
    
    if period_type:
        query = query.where(FinancialMetrics.period_type == period_type)
    
    if fiscal_year:
        query = query.where(FinancialMetrics.fiscal_year == fiscal_year)
    
    query = query.order_by(desc(FinancialMetrics.report_date)).limit(limit)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return [FinancialMetricsSchema.model_validate(metric) for metric in metrics]


@router.post("/{company_id}/financial-metrics", response_model=FinancialMetricsSchema)
async def create_financial_metrics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    metrics_in: FinancialMetricsCreate
):
    """创建财务指标"""
    
    # 验证公司存在
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 检查是否已存在相同期间的财务指标
    existing_query = select(FinancialMetrics).where(
        and_(
            FinancialMetrics.company_id == company_id,
            FinancialMetrics.fiscal_year == metrics_in.fiscal_year,
            FinancialMetrics.period_type == metrics_in.period_type,
            FinancialMetrics.fiscal_quarter == metrics_in.fiscal_quarter
        )
    )
    existing_result = await db.execute(existing_query)
    existing_metrics = existing_result.scalar_one_or_none()
    
    if existing_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该期间的财务指标已存在"
        )
    
    # 创建财务指标
    metrics_data = metrics_in.model_dump()
    metrics_data["company_id"] = company_id
    metrics = FinancialMetrics(**metrics_data)
    
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    
    return FinancialMetricsSchema.model_validate(metrics)


# 市场地位相关端点
@router.get("/{company_id}/market-position", response_model=List[MarketPositionSchema])
async def get_market_position(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    limit: int = Query(10, ge=1, le=100, description="返回记录数")
):
    """获取公司市场地位"""
    
    query = (
        select(MarketPosition)
        .where(MarketPosition.company_id == company_id)
        .order_by(desc(MarketPosition.analysis_date))
        .limit(limit)
    )
    
    result = await db.execute(query)
    positions = result.scalars().all()
    
    return [MarketPositionSchema.model_validate(position) for position in positions]


@router.post("/{company_id}/market-position", response_model=MarketPositionSchema)
async def create_market_position(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    position_in: MarketPositionCreate
):
    """创建市场地位数据"""
    
    # 验证公司存在
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 创建市场地位数据
    position_data = position_in.model_dump()
    position_data["company_id"] = company_id
    position = MarketPosition(**position_data)
    
    db.add(position)
    await db.commit()
    await db.refresh(position)
    
    return MarketPositionSchema.model_validate(position)


# 公司行为相关端点
@router.get("/{company_id}/corporate-actions", response_model=List[CorporateActionSchema])
async def get_corporate_actions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    action_type: Optional[str] = Query(None, description="行为类型"),
    from_date: Optional[datetime] = Query(None, description="开始日期"),
    to_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数")
):
    """获取公司行为记录"""
    
    query = select(CorporateAction).where(CorporateAction.company_id == company_id)
    
    if action_type:
        query = query.where(CorporateAction.action_type == action_type)
    
    if from_date:
        query = query.where(CorporateAction.ex_date >= from_date)
    
    if to_date:
        query = query.where(CorporateAction.ex_date <= to_date)
    
    query = query.order_by(desc(CorporateAction.ex_date)).limit(limit)
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    return [CorporateActionSchema.model_validate(action) for action in actions]


@router.post("/{company_id}/corporate-actions", response_model=CorporateActionSchema)
async def create_corporate_action(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    action_in: CorporateActionCreate
):
    """创建公司行为记录"""
    
    # 验证公司存在
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 创建公司行为记录
    action_data = action_in.model_dump()
    action_data["company_id"] = company_id
    action = CorporateAction(**action_data)
    
    db.add(action)
    await db.commit()
    await db.refresh(action)
    
    return CorporateActionSchema.model_validate(action)


# ESG指标相关端点
@router.get("/{company_id}/esg-metrics", response_model=List[ESGMetricsSchema])
async def get_esg_metrics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    limit: int = Query(10, ge=1, le=100, description="返回记录数")
):
    """获取ESG指标"""
    
    query = (
        select(ESGMetrics)
        .where(ESGMetrics.company_id == company_id)
        .order_by(desc(ESGMetrics.assessment_date))
        .limit(limit)
    )
    
    result = await db.execute(query)
    esg_metrics = result.scalars().all()
    
    return [ESGMetricsSchema.model_validate(metric) for metric in esg_metrics]


@router.post("/{company_id}/esg-metrics", response_model=ESGMetricsSchema)
async def create_esg_metrics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    esg_in: ESGMetricsCreate
):
    """创建ESG指标"""
    
    # 验证公司存在
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 创建ESG指标
    esg_data = esg_in.model_dump()
    esg_data["company_id"] = company_id
    esg_metrics = ESGMetrics(**esg_data)
    
    db.add(esg_metrics)
    await db.commit()
    await db.refresh(esg_metrics)
    
    return ESGMetricsSchema.model_validate(esg_metrics)


# 分析师评级相关端点
@router.get("/{company_id}/analyst-ratings", response_model=List[AnalystRatingSchema])
async def get_analyst_ratings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    analyst_firm: Optional[str] = Query(None, description="分析师公司"),
    from_date: Optional[datetime] = Query(None, description="开始日期"),
    to_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数")
):
    """获取分析师评级"""
    
    query = select(AnalystRating).where(AnalystRating.company_id == company_id)
    
    if analyst_firm:
        query = query.where(AnalystRating.analyst_firm == analyst_firm)
    
    if from_date:
        query = query.where(AnalystRating.rating_date >= from_date)
    
    if to_date:
        query = query.where(AnalystRating.rating_date <= to_date)
    
    query = query.order_by(desc(AnalystRating.rating_date)).limit(limit)
    
    result = await db.execute(query)
    ratings = result.scalars().all()
    
    return [AnalystRatingSchema.model_validate(rating) for rating in ratings]


@router.post("/{company_id}/analyst-ratings", response_model=AnalystRatingSchema)
async def create_analyst_rating(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int,
    rating_in: AnalystRatingCreate
):
    """创建分析师评级"""
    
    # 验证公司存在
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公司不存在"
        )
    
    # 创建分析师评级
    rating_data = rating_in.model_dump()
    rating_data["company_id"] = company_id
    rating = AnalystRating(**rating_data)
    
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    
    return AnalystRatingSchema.model_validate(rating)