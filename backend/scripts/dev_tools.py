#!/usr/bin/env python3
"""
开发工具脚本
用于数据库管理、数据导入等开发任务
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.init_db import init_db, reset_database
from app.services.stock_data_service import StockDataService
from app.services.providers.yfinance_provider import YFinanceProvider


async def create_sample_user():
    """创建示例用户"""
    from app.db.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        # 检查用户是否已存在
        result = await db.execute(
            select(User).where(User.username == "demo")
        )
        if result.scalar_one_or_none():
            print("Demo user already exists")
            return
        
        # 创建示例用户
        demo_user = User(
            email="demo@example.com",
            username="demo",
            hashed_password=get_password_hash("demo123!"),
            full_name="Demo User",
            is_active=True,
            is_superuser=False
        )
        
        db.add(demo_user)
        await db.commit()
        print("Demo user created: demo@example.com / demo123!")


async def update_sample_data():
    """更新示例股票数据"""
    data_provider = YFinanceProvider()
    service = StockDataService(data_provider)
    
    print("Updating sample stock data...")
    result = await service.update_all_active_stocks(days=30)
    print(f"Update completed: {result}")


async def test_data_provider():
    """测试数据提供者"""
    from datetime import datetime, timedelta
    
    provider = YFinanceProvider()
    
    # 测试获取股票数据
    print("Testing stock data fetch...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    data = await provider.fetch_stock_data("AAPL", start_date, end_date)
    print(f"Fetched {len(data)} records for AAPL")
    
    # 测试搜索功能
    print("Testing stock search...")
    results = await provider.search_stocks("AAPL")
    print(f"Search results: {results}")
    
    # 测试实时数据
    print("Testing realtime data...")
    realtime = await provider.fetch_realtime_data(["AAPL", "GOOGL"])
    print(f"Realtime data: {realtime}")


async def show_database_stats():
    """显示数据库统计"""
    from app.db.database import AsyncSessionLocal
    from app.models.stock import Stock, StockPrice
    from app.models.user import User
    from sqlalchemy import select, func
    
    async with AsyncSessionLocal() as db:
        # 股票统计
        stock_count = await db.execute(select(func.count()).select_from(Stock))
        active_stocks = await db.execute(
            select(func.count()).select_from(Stock).where(Stock.is_active == True)
        )
        
        # 价格数据统计
        price_count = await db.execute(select(func.count()).select_from(StockPrice))
        
        # 用户统计
        user_count = await db.execute(select(func.count()).select_from(User))
        
        print("\n📊 Database Statistics")
        print(f"Total stocks: {stock_count.scalar()}")
        print(f"Active stocks: {active_stocks.scalar()}")
        print(f"Price records: {price_count.scalar()}")
        print(f"Users: {user_count.scalar()}")
        
        # 最近的价格数据
        latest_price = await db.execute(
            select(StockPrice.date, Stock.symbol)
            .join(Stock)
            .order_by(StockPrice.date.desc())
            .limit(5)
        )
        
        print("\n📅 Latest price data:")
        for date, symbol in latest_price.fetchall():
            print(f"  {symbol}: {date}")


def main():
    parser = argparse.ArgumentParser(description="Stock Info System Development Tools")
    parser.add_argument(
        "command",
        choices=[
            "init-db", "reset-db", "create-demo-user", 
            "update-data", "test-provider", "stats"
        ],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "init-db":
        print("Initializing database...")
        asyncio.run(init_db())
        print("✅ Database initialized")
        
    elif args.command == "reset-db":
        print("⚠️  Resetting database (all data will be lost)...")
        response = input("Are you sure? (yes/no): ")
        if response.lower() == "yes":
            asyncio.run(reset_database())
            print("✅ Database reset completed")
        else:
            print("❌ Operation cancelled")
            
    elif args.command == "create-demo-user":
        print("Creating demo user...")
        asyncio.run(create_sample_user())
        print("✅ Demo user created")
        
    elif args.command == "update-data":
        print("Updating sample data...")
        asyncio.run(update_sample_data())
        print("✅ Data update completed")
        
    elif args.command == "test-provider":
        print("Testing data provider...")
        asyncio.run(test_data_provider())
        print("✅ Provider test completed")
        
    elif args.command == "stats":
        asyncio.run(show_database_stats())


if __name__ == "__main__":
    main()