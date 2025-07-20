#!/usr/bin/env python3
"""
测试公司数据采集功能
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.models import Company, Stock, FinancialMetrics, MarketPosition
from app.services.providers.company_data_provider import CompanyDataProvider
from app.db.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_company_data_collection():
    """测试公司数据采集"""
    
    logger.info("🚀 开始测试公司数据采集功能")
    
    # 获取数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 创建数据提供者
            provider = CompanyDataProvider()
            
            # 测试采集AAPL公司数据
            symbol = "AAPL"
            logger.info(f"📊 开始采集 {symbol} 公司数据...")
            
            async with provider:
                result = await provider.collect_company_data(symbol, db)
            
            logger.info(f"✅ 数据采集完成！结果:")
            for key, value in result.items():
                if key != 'company':
                    logger.info(f"   {key}: {value}")
            
            # 查询数据库中的结果
            logger.info("\n📋 查询数据库中的公司数据:")
            
            # 查询公司信息
            from sqlalchemy import select
            company_query = select(Company).where(Company.ticker_symbol == symbol)
            company_result = await db.execute(company_query)
            company = company_result.scalar_one_or_none()
            
            if company:
                logger.info(f"   公司名称: {company.company_name}")
                logger.info(f"   行业: {company.industry}")
                logger.info(f"   板块: {company.sector}")
                logger.info(f"   员工数: {company.full_time_employees}")
                
                # 查询财务指标
                financial_query = select(FinancialMetrics).where(
                    FinancialMetrics.company_id == company.id
                ).limit(3)
                financial_result = await db.execute(financial_query)
                financial_metrics = financial_result.scalars().all()
                
                logger.info(f"   财务指标记录数: {len(financial_metrics)}")
                for metrics in financial_metrics:
                    logger.info(f"     {metrics.period_type} {metrics.fiscal_year}Q{metrics.fiscal_quarter or 'A'}: "
                              f"收入=${metrics.revenue:,.0f}" if metrics.revenue else "收入=N/A")
                
                # 查询市场地位
                market_query = select(MarketPosition).where(
                    MarketPosition.company_id == company.id
                ).limit(1)
                market_result = await db.execute(market_query)
                market_position = market_result.scalar_one_or_none()
                
                if market_position:
                    logger.info(f"   市值: ${market_position.market_cap:,.0f}" if market_position.market_cap else "市值=N/A")
                    logger.info(f"   多元化评分: {market_position.revenue_diversification_score}" if market_position.revenue_diversification_score else "多元化评分=N/A")
            else:
                logger.warning(f"   未找到 {symbol} 的公司记录")
            
            logger.info("🎉 测试完成！")
            
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


async def show_database_status():
    """显示数据库状态"""
    
    logger.info("📊 数据库状态统计:")
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        
        # 统计各表的记录数
        tables = [
            (Stock, "股票"),
            (Company, "公司"),
            (FinancialMetrics, "财务指标"),
            (MarketPosition, "市场地位")
        ]
        
        for model, name in tables:
            count_query = select(func.count()).select_from(model)
            count_result = await db.execute(count_query)
            count = count_result.scalar()
            logger.info(f"   {name}: {count} 条记录")


if __name__ == "__main__":
    asyncio.run(show_database_status())
    asyncio.run(test_company_data_collection())
    asyncio.run(show_database_status())