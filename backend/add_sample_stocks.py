#!/usr/bin/env python3
"""
添加10只纳斯达克样本股票到数据库
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.stock import Stock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 10只纳斯达克代表性股票
SAMPLE_STOCKS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3000000000000,  # 约3万亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "MSFT", 
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 2800000000000,  # 约2.8万亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation", 
        "sector": "Technology",
        "industry": "Semiconductors",
        "market_cap": 1800000000000,  # 约1.8万亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "META",
        "name": "Meta Platforms Inc.",
        "sector": "Communication Services", 
        "industry": "Social Media",
        "market_cap": 800000000000,   # 约8000亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "NFLX",
        "name": "Netflix Inc.",
        "sector": "Communication Services",
        "industry": "Entertainment",
        "market_cap": 200000000000,   # 约2000亿美元
 
        "exchange": "NASDAQ"
    },
    {
        "symbol": "PYPL",
        "name": "PayPal Holdings Inc.",
        "sector": "Financial Services",
        "industry": "Financial Technology",
        "market_cap": 70000000000,    # 约700亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "INTC",
        "name": "Intel Corporation",
        "sector": "Technology", 
        "industry": "Semiconductors",
        "market_cap": 150000000000,   # 约1500亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "CSCO",
        "name": "Cisco Systems Inc.",
        "sector": "Technology",
        "industry": "Network Equipment", 
        "market_cap": 200000000000,   # 约2000亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "ADBE",
        "name": "Adobe Inc.",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 240000000000,   # 约2400亿美元
        "exchange": "NASDAQ"
    },
    {
        "symbol": "QCOM", 
        "name": "QUALCOMM Incorporated",
        "sector": "Technology",
        "industry": "Semiconductors",
        "market_cap": 180000000000,   # 约1800亿美元
        "exchange": "NASDAQ"
    }
]


async def add_sample_stocks():
    """添加样本股票到数据库"""
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True
    )
    
    # 创建异步会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            logger.info("开始添加样本股票...")
            
            added_count = 0
            updated_count = 0
            
            for stock_data in SAMPLE_STOCKS:
                # 检查股票是否已存在 (通过symbol查询)
                from sqlalchemy import select
                result = await session.execute(
                    select(Stock).where(Stock.symbol == stock_data["symbol"])
                )
                existing_stock = result.scalar_one_or_none()
                
                if existing_stock:
                    # 更新现有股票信息
                    for key, value in stock_data.items():
                        if key != "symbol":  # 不更新主键
                            setattr(existing_stock, key, value)
                    logger.info(f"更新股票: {stock_data['symbol']} - {stock_data['name']}")
                    updated_count += 1
                else:
                    # 添加新股票
                    new_stock = Stock(**stock_data)
                    session.add(new_stock)
                    logger.info(f"添加股票: {stock_data['symbol']} - {stock_data['name']}")
                    added_count += 1
            
            await session.commit()
            
            logger.info(f"股票数据处理完成! 新增: {added_count}, 更新: {updated_count}")
            
            # 验证结果
            result = await session.execute("SELECT COUNT(*) FROM stocks")
            total_stocks = result.scalar()
            logger.info(f"数据库中总股票数量: {total_stocks}")
            
    except Exception as e:
        logger.error(f"添加股票失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_sample_stocks())