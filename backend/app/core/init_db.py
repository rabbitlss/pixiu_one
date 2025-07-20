import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal, create_db_and_tables
from app.models.user import User
from app.models.stock import Stock
from app.core.security import get_password_hash
from app.core.config import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库"""
    try:
        logger.info("Initializing database...")
        
        # 创建所有表
        await create_db_and_tables()
        logger.info("Database tables created successfully")
        
        # 创建初始数据
        await create_initial_data()
        logger.info("Initial data created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def create_initial_data() -> None:
    """创建初始数据"""
    async with AsyncSessionLocal() as db:
        try:
            # 检查是否已有超级用户
            result = await db.execute(
                select(User).where(User.is_superuser == True)
            )
            superuser = result.scalar_one_or_none()
            
            if not superuser:
                # 创建默认超级用户
                superuser = User(
                    email="admin@quantinfo.com",
                    username="admin",
                    hashed_password=get_password_hash("admin123!@#"),
                    full_name="System Administrator",
                    is_active=True,
                    is_superuser=True
                )
                db.add(superuser)
                logger.info("Created default superuser: admin@quantinfo.com")
            
            # 创建一些示例股票数据
            stock_symbols = [
                ("AAPL", "Apple Inc.", "NASDAQ", "Technology", "Consumer Electronics"),
                ("GOOGL", "Alphabet Inc.", "NASDAQ", "Technology", "Internet Content & Information"),
                ("MSFT", "Microsoft Corporation", "NASDAQ", "Technology", "Software"),
                ("TSLA", "Tesla, Inc.", "NASDAQ", "Consumer Cyclical", "Auto Manufacturers"),
                ("AMZN", "Amazon.com, Inc.", "NASDAQ", "Consumer Cyclical", "Internet Retail"),
            ]
            
            for symbol, name, exchange, sector, industry in stock_symbols:
                # 检查股票是否已存在
                existing_stock = await db.execute(
                    select(Stock).where(Stock.symbol == symbol)
                )
                if not existing_stock.scalar_one_or_none():
                    stock = Stock(
                        symbol=symbol,
                        name=name,
                        exchange=exchange,
                        sector=sector,
                        industry=industry,
                        is_active=True
                    )
                    db.add(stock)
                    logger.info(f"Created stock: {symbol} - {name}")
            
            await db.commit()
            logger.info("Initial data creation completed")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating initial data: {e}")
            raise


async def reset_database() -> None:
    """重置数据库（仅用于开发环境）"""
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        from app.db.database import engine, Base
        
        # 删除所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("All tables dropped")
        
        # 重新初始化
        await init_db()
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise


if __name__ == "__main__":
    # 可以直接运行此脚本来初始化数据库
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        asyncio.run(reset_database())
    else:
        asyncio.run(init_db())