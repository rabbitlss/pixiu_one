#!/usr/bin/env python3
"""
使用Alpha Vantage真实数据更新数据库
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.services.providers.alphavantage_provider import AlphaVantageProvider
from app.db.database import AsyncSessionLocal
from app.models.stock import Stock, StockPrice
from sqlalchemy import select, delete, text

async def update_stock_with_real_data(symbol: str, provider: AlphaVantageProvider):
    """更新单只股票的真实数据"""
    print(f"📊 更新 {symbol} 的真实数据...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取股票信息
            stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = stock_result.scalar_one_or_none()
            
            if not stock:
                print(f"  ❌ 未找到股票 {symbol}")
                return False
            
            # 获取真实数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 获取30天数据
            
            real_data = await provider.fetch_stock_data(symbol, start_date, end_date)
            
            if not real_data:
                print(f"  ❌ 无法获取 {symbol} 的真实数据")
                return False
            
            print(f"  📈 获取到 {len(real_data)} 条真实记录")
            
            # 删除现有数据
            await db.execute(
                delete(StockPrice).where(StockPrice.stock_id == stock.id)
            )
            
            # 插入新的真实数据
            added_count = 0
            for data_point in real_data:
                # 检查是否已存在
                existing = await db.execute(
                    select(StockPrice).where(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date == data_point['date']
                    )
                )
                
                if not existing.scalar_one_or_none():
                    new_price = StockPrice(
                        stock_id=stock.id,
                        date=data_point['date'],
                        open=data_point['open'],
                        high=data_point['high'],
                        low=data_point['low'],
                        close=data_point['close'],
                        volume=data_point['volume'],
                        adjusted_close=data_point['adjusted_close']
                    )
                    db.add(new_price)
                    added_count += 1
            
            await db.commit()
            print(f"  ✅ {symbol} 成功添加 {added_count} 条真实记录")
            
            # 显示最新价格
            if real_data:
                latest = real_data[-1]
                print(f"     最新价格: {latest['date'].strftime('%Y-%m-%d')} ${latest['close']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 更新 {symbol} 时出错: {e}")
            await db.rollback()
            return False

async def main():
    """主函数"""
    print("🚀 使用Alpha Vantage真实数据更新数据库")
    print("=" * 50)
    
    provider = AlphaVantageProvider()
    
    # 要更新的股票列表
    symbols = ["AAPL", "GOOGL", "MSFT"]
    
    success_count = 0
    
    for i, symbol in enumerate(symbols):
        if i > 0:
            print(f"  ⏱️ 等待API限制间隔...")
            await asyncio.sleep(12)  # Alpha Vantage免费版限制
        
        success = await update_stock_with_real_data(symbol, provider)
        if success:
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ 更新完成！成功更新 {success_count}/{len(symbols)} 只股票")
    print("\n🌐 可以通过以下方式查看更新的数据:")
    print("   • API: http://localhost:8000/api/v1/stocks")
    print("   • 演示: python demo_data.py")

if __name__ == "__main__":
    asyncio.run(main())