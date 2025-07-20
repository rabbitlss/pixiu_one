from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.api.dependencies import get_current_superuser, get_db
from app.models import User, Stock, Company
from app.services.providers.company_data_provider import CompanyDataProvider
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class DataCollectionRequest(BaseModel):
    """数据采集请求模式"""
    symbols: List[str]
    collect_company_info: bool = True
    collect_financial_data: bool = True
    collect_market_position: bool = True


class DataCollectionResponse(BaseModel):
    """数据采集响应模式"""
    task_id: str
    message: str
    symbols: List[str]
    status: str


class DataCollectionResult(BaseModel):
    """数据采集结果模式"""
    symbol: str
    success: bool
    data: dict
    error: Optional[str] = None


async def collect_company_data_task(symbols: List[str], db: AsyncSession):
    """后台数据采集任务"""
    results = []
    
    async with CompanyDataProvider() as provider:
        for symbol in symbols:
            try:
                logger.info(f"开始采集公司数据: {symbol}")
                result = await provider.collect_company_data(symbol, db)
                
                results.append(DataCollectionResult(
                    symbol=symbol,
                    success="error" not in result,
                    data=result,
                    error=result.get("error")
                ))
                
                logger.info(f"完成采集公司数据: {symbol}")
                
            except Exception as e:
                logger.error(f"采集失败 {symbol}: {e}")
                results.append(DataCollectionResult(
                    symbol=symbol,
                    success=False,
                    data={},
                    error=str(e)
                ))
    
    # 记录结果
    success_count = sum(1 for r in results if r.success)
    logger.info(f"数据采集完成: {success_count}/{len(symbols)} 成功")
    
    return results


@router.post("/collect-company-data", response_model=DataCollectionResponse)
async def trigger_company_data_collection(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    background_tasks: BackgroundTasks,
    request: DataCollectionRequest
):
    """触发公司数据采集任务"""
    
    if not request.symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供至少一个股票代码"
        )
    
    # 验证股票代码是否存在
    existing_stocks = []
    for symbol in request.symbols:
        stock_query = select(Stock).where(Stock.symbol == symbol)
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if stock:
            existing_stocks.append(symbol)
        else:
            logger.warning(f"股票代码不存在: {symbol}")
    
    if not existing_stocks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有找到有效的股票代码"
        )
    
    # 启动后台任务
    task_id = f"company_data_collection_{current_user.id}_{len(existing_stocks)}_symbols"
    background_tasks.add_task(collect_company_data_task, existing_stocks, db)
    
    return DataCollectionResponse(
        task_id=task_id,
        message=f"已启动公司数据采集任务，共 {len(existing_stocks)} 个股票代码",
        symbols=existing_stocks,
        status="started"
    )


@router.post("/collect-all-companies", response_model=DataCollectionResponse)
async def trigger_all_companies_data_collection(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    background_tasks: BackgroundTasks,
    limit: Optional[int] = 10
):
    """采集所有活跃股票的公司数据"""
    
    # 获取所有活跃股票
    stocks_query = select(Stock).where(Stock.is_active == True).limit(limit)
    stocks_result = await db.execute(stocks_query)
    stocks = stocks_result.scalars().all()
    
    if not stocks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到活跃的股票"
        )
    
    symbols = [stock.symbol for stock in stocks]
    
    # 启动后台任务
    task_id = f"all_companies_data_collection_{current_user.id}_{len(symbols)}_symbols"
    background_tasks.add_task(collect_company_data_task, symbols, db)
    
    return DataCollectionResponse(
        task_id=task_id,
        message=f"已启动全量公司数据采集任务，共 {len(symbols)} 个股票代码",
        symbols=symbols,
        status="started"
    )


@router.get("/companies-status")
async def get_companies_data_status(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """获取公司数据采集状态"""
    
    # 统计股票和公司数量
    stocks_query = select(Stock).where(Stock.is_active == True)
    stocks_result = await db.execute(stocks_query)
    total_stocks = len(stocks_result.scalars().all())
    
    companies_query = select(Company)
    companies_result = await db.execute(companies_query)
    total_companies = len(companies_result.scalars().all())
    
    # 统计有财务数据的公司
    from app.models import FinancialMetrics
    financial_companies_query = select(Company.id).join(FinancialMetrics).distinct()
    financial_companies_result = await db.execute(financial_companies_query)
    companies_with_financial = len(financial_companies_result.scalars().all())
    
    # 统计有市场地位数据的公司
    from app.models import MarketPosition
    market_companies_query = select(Company.id).join(MarketPosition).distinct()
    market_companies_result = await db.execute(market_companies_query)
    companies_with_market = len(market_companies_result.scalars().all())
    
    return {
        "total_stocks": total_stocks,
        "total_companies": total_companies,
        "companies_with_financial_data": companies_with_financial,
        "companies_with_market_data": companies_with_market,
        "coverage_percentage": (total_companies / total_stocks * 100) if total_stocks > 0 else 0,
        "financial_data_percentage": (companies_with_financial / total_companies * 100) if total_companies > 0 else 0,
        "market_data_percentage": (companies_with_market / total_companies * 100) if total_companies > 0 else 0
    }


@router.get("/companies-without-data")
async def get_companies_without_data(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    data_type: str = "company",  # company, financial, market
    limit: int = 20
):
    """获取缺少特定数据的股票列表"""
    
    if data_type == "company":
        # 找到没有公司记录的股票
        stocks_without_company_query = (
            select(Stock)
            .outerjoin(Company)
            .where(Company.id.is_(None))
            .where(Stock.is_active == True)
            .limit(limit)
        )
        result = await db.execute(stocks_without_company_query)
        stocks = result.scalars().all()
        return {
            "data_type": data_type,
            "count": len(stocks),
            "symbols": [stock.symbol for stock in stocks]
        }
    
    elif data_type == "financial":
        # 找到没有财务数据的公司
        from app.models import FinancialMetrics
        companies_without_financial_query = (
            select(Company)
            .outerjoin(FinancialMetrics)
            .where(FinancialMetrics.id.is_(None))
            .limit(limit)
        )
        result = await db.execute(companies_without_financial_query)
        companies = result.scalars().all()
        return {
            "data_type": data_type,
            "count": len(companies),
            "symbols": [company.ticker_symbol for company in companies]
        }
    
    elif data_type == "market":
        # 找到没有市场地位数据的公司
        from app.models import MarketPosition
        companies_without_market_query = (
            select(Company)
            .outerjoin(MarketPosition)
            .where(MarketPosition.id.is_(None))
            .limit(limit)
        )
        result = await db.execute(companies_without_market_query)
        companies = result.scalars().all()
        return {
            "data_type": data_type,
            "count": len(companies),
            "symbols": [company.ticker_symbol for company in companies]
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的数据类型，支持: company, financial, market"
        )