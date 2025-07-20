#!/usr/bin/env python3
"""
创建公司数据相关表的脚本
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.database import Base

# 导入所有模型以确保它们被注册
from app.models import (
    Stock, StockPrice, TechnicalIndicator,
    User, Watchlist, WatchlistStock, Alert,
    Company, FinancialMetrics, MarketPosition, 
    CorporateAction, ESGMetrics, AnalystRating
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_company_tables():
    """创建公司数据相关的数据库表"""
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True
    )
    
    try:
        logger.info("开始创建公司数据表...")
        
        async with engine.begin() as conn:
            # 创建所有表（只会创建不存在的表）
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("公司数据表创建完成！")
        
        # 显示新创建的表
        new_tables = [
            "companies",
            "financial_metrics", 
            "market_position",
            "corporate_actions",
            "esg_metrics",
            "analyst_ratings"
        ]
        
        logger.info("新增的表包括:")
        for table in new_tables:
            logger.info(f"  - {table}")
            
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_company_tables())