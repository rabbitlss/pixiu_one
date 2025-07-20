#!/usr/bin/env python3
"""
使用Twelve Data API采集样本股票的财务数据
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.stock import Stock
from app.models.company import Company, FinancialMetrics
from app.services.providers.twelvedata_provider import TwelveDataProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 目标股票（选择几只进行测试）
TARGET_SYMBOLS = [
    "AAPL",   # Apple Inc. (应该有数据)
    "MSFT",   # Microsoft (应该有数据) 
    "NVDA",   # NVIDIA Corporation
    "META",   # Meta Platforms Inc.
]


async def collect_sample_data():
    """采集样本财务数据"""
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            logger.info("开始使用 Twelve Data 采集财务数据...")
            
            success_count = 0
            fail_count = 0
            
            provider = TwelveDataProvider()
            
            for symbol in TARGET_SYMBOLS:
                try:
                    logger.info(f"正在采集 {symbol} 的数据...")
                    
                    # 1. 获取公司概况
                    profile_data = await provider.get_company_profile(symbol)
                    if not profile_data:
                        logger.warning(f"❌ {symbol} 无法获取公司概况")
                        fail_count += 1
                        continue
                    
                    # 2. 获取财务报表
                    financial_data = await provider.get_financial_statements(symbol)
                    if not financial_data.get('income_statement'):
                        logger.warning(f"❌ {symbol} 无法获取财务报表")
                        fail_count += 1
                        continue
                    
                    # 3. 保存到数据库
                    await save_company_data(session, symbol, profile_data, financial_data)
                    
                    logger.info(f"✅ {symbol} 数据采集成功")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ {symbol} 采集异常: {e}")
                    fail_count += 1
                
                # 添加延迟避免API限制
                await asyncio.sleep(3)
            
            await session.commit()
            
            logger.info(f"数据采集完成! 成功: {success_count}, 失败: {fail_count}")
            
            # 验证结果
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM companies"))
            total_companies = result.scalar()
            logger.info(f"数据库中总公司数量: {total_companies}")
            
            provider.cleanup()
            
    except Exception as e:
        logger.error(f"数据采集失败: {e}")
        raise
    finally:
        await engine.dispose()


async def save_company_data(session: AsyncSession, symbol: str, profile_data: dict, financial_data: dict):
    """保存公司数据到数据库"""
    
    # 获取对应的股票记录
    result = await session.execute(
        select(Stock).where(Stock.symbol == symbol)
    )
    stock = result.scalar_one_or_none()
    
    if not stock:
        logger.warning(f"Stock {symbol} not found in database")
        return
    
    # 检查公司是否已存在
    result = await session.execute(
        select(Company).where(Company.stock_id == stock.id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        # 创建公司记录
        company = Company(
            stock_id=stock.id,
            name=profile_data.get('name', stock.name),
            description=profile_data.get('description', ''),
            sector=profile_data.get('sector', stock.sector),
            industry=profile_data.get('industry', stock.industry),
            website=profile_data.get('website', ''),
            employees=profile_data.get('employees'),
            ceo=profile_data.get('CEO', ''),
            headquarters=f"{profile_data.get('city', '')}, {profile_data.get('state', '')}, {profile_data.get('country', '')}".strip(', ')
        )
        session.add(company)
        await session.flush()  # 获取公司ID
    
    # 处理财务指标
    income_statement = financial_data.get('income_statement', {})
    if 'income_statement' in income_statement and income_statement['income_statement']:
        latest_financials = income_statement['income_statement'][0]  # 最新年度数据
        
        # 检查财务指标是否已存在
        result = await session.execute(
            select(FinancialMetrics).where(
                FinancialMetrics.company_id == company.id,
                FinancialMetrics.fiscal_year == latest_financials.get('year', 2024)
            )
        )
        existing_metrics = result.scalar_one_or_none()
        
        if not existing_metrics:
            # 创建财务指标记录
            financial_metrics = FinancialMetrics(
                company_id=company.id,
                fiscal_year=latest_financials.get('year', 2024),
                period='Annual',
                
                # 收入指标
                total_revenue=latest_financials.get('sales'),
                gross_profit=latest_financials.get('gross_profit'),
                operating_income=latest_financials.get('operating_income'),
                net_income=latest_financials.get('net_income'),
                ebitda=latest_financials.get('ebitda'),
                
                # 每股指标  
                earnings_per_share=latest_financials.get('eps_diluted'),
                earnings_per_share_diluted=latest_financials.get('eps_diluted'),
                
                # 计算一些基本比率
                gross_margin=calculate_ratio(latest_financials.get('gross_profit'), latest_financials.get('sales')),
                operating_margin=calculate_ratio(latest_financials.get('operating_income'), latest_financials.get('sales')),
                net_margin=calculate_ratio(latest_financials.get('net_income'), latest_financials.get('sales')),
            )
            session.add(financial_metrics)
    
    logger.info(f"Saved company data for {symbol}")


def calculate_ratio(numerator, denominator):
    """计算比率，处理除零情况"""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return (numerator / denominator) * 100


if __name__ == "__main__":
    asyncio.run(collect_sample_data())