#!/usr/bin/env python3
"""
简单的数据获取测试脚本
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.models.stock import Stock, StockPrice
from app.services.providers.yfinance_provider import YFinanceProvider
from app.services.stock_data_service import StockDataService
from sqlalchemy import select


async def test_basic_data_fetch():
    """测试基本数据获取"""
    print("🔄 测试基本数据获取...")
    
    # 使用requests库直接获取数据
    import requests
    
    try:
        # 测试简单的HTTP请求
        response = requests.get("https://httpbin.org/get", timeout=10)
        print(f"✅ 网络连接正常: {response.status_code}")
    except Exception as e:
        print(f"❌ 网络连接问题: {e}")
        return False
    
    return True


async def add_manual_sample_data():
    """手动添加示例数据"""
    print("📊 添加示例股票价格数据...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取AAPL股票
            result = await db.execute(select(Stock).where(Stock.symbol == "AAPL"))
            aapl_stock = result.scalar_one_or_none()
            
            if not aapl_stock:
                print("❌ 找不到AAPL股票")
                return False
            
            # 检查是否已有价格数据
            existing_prices = await db.execute(
                select(StockPrice).where(StockPrice.stock_id == aapl_stock.id)
            )
            if existing_prices.scalar_one_or_none():
                print("✅ 已存在价格数据")
                return True
            
            # 添加最近5天的示例数据
            base_date = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
            sample_prices = []
            
            for i in range(5):
                date = base_date - timedelta(days=i)
                
                # 模拟价格数据（基于真实的大致范围）
                base_price = 180.0 + (i * 2)  # 模拟价格变动
                
                price = StockPrice(
                    stock_id=aapl_stock.id,
                    date=date,
                    open=base_price + 1.0,
                    high=base_price + 3.0,
                    low=base_price - 1.0,
                    close=base_price,
                    volume=50000000 + (i * 1000000),
                    adjusted_close=base_price
                )
                sample_prices.append(price)
            
            # 批量添加
            db.add_all(sample_prices)
            await db.commit()
            
            print(f"✅ 成功添加 {len(sample_prices)} 条价格记录")
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 添加数据失败: {e}")
            return False


async def try_alternative_data_source():
    """尝试替代数据源"""
    print("🔄 尝试替代数据源...")
    
    try:
        import requests
        import json
        
        # 使用Alpha Vantage的免费API（demo key）
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": "AAPL",
            "apikey": "demo",
            "outputsize": "compact"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "Time Series (Daily)" in data:
                print("✅ Alpha Vantage API 连接成功")
                time_series = data["Time Series (Daily)"]
                recent_date = list(time_series.keys())[0]
                recent_data = time_series[recent_date]
                print(f"📊 最新数据: {recent_date} - 收盘价: {recent_data['4. close']}")
                return True
            else:
                print(f"⚠️ API返回格式异常: {data}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 替代数据源测试失败: {e}")
    
    return False


async def test_database_operations():
    """测试数据库操作"""
    print("🗄️ 测试数据库操作...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 查询股票数量
            stock_count = await db.execute(select(Stock))
            stocks = stock_count.scalars().all()
            print(f"📊 数据库中有 {len(stocks)} 只股票")
            
            # 查询价格数据
            price_count = await db.execute(select(StockPrice))
            prices = price_count.scalars().all()
            print(f"📊 数据库中有 {len(prices)} 条价格记录")
            
            # 显示最新的价格数据
            if prices:
                latest_prices = await db.execute(
                    select(StockPrice, Stock.symbol)
                    .join(Stock)
                    .order_by(StockPrice.date.desc())
                    .limit(5)
                )
                
                print("📈 最新价格数据:")
                for price, symbol in latest_prices:
                    print(f"  {symbol}: {price.date.strftime('%Y-%m-%d')} - "
                          f"收盘价: ${price.close:.2f}, 成交量: {price.volume:,}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 开始数据获取测试\n")
    
    # 1. 测试网络连接
    if not await test_basic_data_fetch():
        print("❌ 网络连接测试失败")
        return
    
    # 2. 测试数据库操作
    if not await test_database_operations():
        print("❌ 数据库操作测试失败")
        return
    
    # 3. 尝试添加示例数据
    await add_manual_sample_data()
    
    # 4. 尝试替代数据源
    await try_alternative_data_source()
    
    # 5. 再次查看数据库状态
    await test_database_operations()
    
    print("\n✅ 数据获取测试完成！")


if __name__ == "__main__":
    asyncio.run(main())