#!/usr/bin/env python3
"""
为所有股票添加更多示例数据
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.models.stock import Stock, StockPrice
from sqlalchemy import select


async def add_historical_data():
    """为所有股票添加30天的历史数据"""
    print("📊 开始为所有股票添加历史数据...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取所有股票
            result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = result.scalars().all()
            
            print(f"📈 发现 {len(stocks)} 只活跃股票")
            
            # 定义不同股票的基础价格
            base_prices = {
                "AAPL": 180.0,
                "GOOGL": 140.0,
                "MSFT": 420.0,
                "TSLA": 250.0,
                "AMZN": 150.0
            }
            
            total_records = 0
            
            for stock in stocks:
                print(f"处理股票: {stock.symbol} - {stock.name}")
                
                # 检查是否已有数据
                existing_count = await db.execute(
                    select(StockPrice).where(StockPrice.stock_id == stock.id)
                )
                existing_prices = existing_count.scalars().all()
                
                if len(existing_prices) >= 20:
                    print(f"  ✅ {stock.symbol} 已有足够数据 ({len(existing_prices)} 条)")
                    continue
                
                # 清除现有数据（重新生成）
                if existing_prices:
                    for price in existing_prices:
                        await db.delete(price)
                    await db.flush()
                
                # 生成30天的历史数据
                base_price = base_prices.get(stock.symbol, 100.0)
                prices_to_add = []
                
                current_price = base_price
                base_date = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
                
                for i in range(30):
                    date = base_date - timedelta(days=i)
                    
                    # 跳过周末（简化处理）
                    if date.weekday() >= 5:
                        continue
                    
                    # 模拟价格波动 (-2% 到 +2%)
                    price_change = random.uniform(-0.02, 0.02)
                    current_price *= (1 + price_change)
                    
                    # 确保价格合理性
                    current_price = max(current_price, base_price * 0.8)
                    current_price = min(current_price, base_price * 1.2)
                    
                    # 生成当日OHLC数据
                    daily_volatility = random.uniform(0.005, 0.025)
                    
                    open_price = current_price * (1 + random.uniform(-daily_volatility, daily_volatility))
                    close_price = current_price
                    high_price = max(open_price, close_price) * (1 + random.uniform(0, daily_volatility))
                    low_price = min(open_price, close_price) * (1 - random.uniform(0, daily_volatility))
                    
                    # 生成成交量（基于股票类型）
                    base_volume = {
                        "AAPL": 50000000,
                        "GOOGL": 25000000, 
                        "MSFT": 35000000,
                        "TSLA": 80000000,
                        "AMZN": 40000000
                    }.get(stock.symbol, 30000000)
                    
                    volume = int(base_volume * random.uniform(0.5, 2.0))
                    
                    price_record = StockPrice(
                        stock_id=stock.id,
                        date=date,
                        open=round(open_price, 2),
                        high=round(high_price, 2),
                        low=round(low_price, 2),
                        close=round(close_price, 2),
                        volume=volume,
                        adjusted_close=round(close_price, 2)
                    )
                    
                    prices_to_add.append(price_record)
                
                # 批量添加价格数据
                if prices_to_add:
                    db.add_all(prices_to_add)
                    await db.flush()
                    total_records += len(prices_to_add)
                    print(f"  ✅ 为 {stock.symbol} 添加了 {len(prices_to_add)} 条价格记录")
            
            # 提交所有更改
            await db.commit()
            print(f"\n🎉 成功添加了 {total_records} 条历史价格记录！")
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 添加历史数据失败: {e}")
            return False


async def show_data_summary():
    """显示数据摘要"""
    print("\n📊 数据库摘要:")
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取每只股票的价格数据统计
            stocks_result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = stocks_result.scalars().all()
            
            total_prices = 0
            
            for stock in stocks:
                prices_result = await db.execute(
                    select(StockPrice)
                    .where(StockPrice.stock_id == stock.id)
                    .order_by(StockPrice.date.desc())
                )
                prices = prices_result.scalars().all()
                
                if prices:
                    latest_price = prices[0]
                    oldest_price = prices[-1]
                    
                    price_change = latest_price.close - oldest_price.close
                    price_change_pct = (price_change / oldest_price.close) * 100
                    
                    print(f"  📈 {stock.symbol}: {len(prices)} 条记录")
                    print(f"     最新: ${latest_price.close:.2f} ({latest_price.date.strftime('%Y-%m-%d')})")
                    print(f"     最早: ${oldest_price.close:.2f} ({oldest_price.date.strftime('%Y-%m-%d')})")
                    print(f"     变化: {price_change:+.2f} ({price_change_pct:+.1f}%)")
                    print()
                
                total_prices += len(prices)
            
            print(f"📊 总计: {len(stocks)} 只股票, {total_prices} 条价格记录")
            
        except Exception as e:
            print(f"❌ 获取数据摘要失败: {e}")


async def main():
    """主函数"""
    print("🚀 股票历史数据填充工具\n")
    
    # 1. 添加历史数据
    success = await add_historical_data()
    
    if success:
        # 2. 显示数据摘要
        await show_data_summary()
        
        print("\n✅ 数据填充完成！")
        print("🌐 现在可以通过以下方式查看数据:")
        print("   - API文档: http://localhost:8000/docs")
        print("   - 股票列表: GET /api/v1/stocks")
        print("   - 价格历史: GET /api/v1/stocks/{id}/prices")
    else:
        print("\n❌ 数据填充失败")


if __name__ == "__main__":
    asyncio.run(main())