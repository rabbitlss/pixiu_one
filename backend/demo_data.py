#!/usr/bin/env python3
"""
数据演示脚本 - 展示成功存储的数据
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.models.stock import Stock, StockPrice
from app.models.user import User
from sqlalchemy import select, func, desc


async def show_comprehensive_demo():
    """显示完整的数据演示"""
    print("🎉 股票信息采集系统 - 数据演示")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 系统统计
            print("\n📊 系统统计:")
            
            stock_count = await db.execute(select(func.count()).select_from(Stock))
            price_count = await db.execute(select(func.count()).select_from(StockPrice))
            user_count = await db.execute(select(func.count()).select_from(User))
            
            print(f"   股票数量: {stock_count.scalar()}")
            print(f"   价格记录: {price_count.scalar()}")
            print(f"   用户数量: {user_count.scalar()}")
            
            # 2. 股票列表
            print("\n📈 股票列表:")
            stocks_result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = stocks_result.scalars().all()
            
            for stock in stocks:
                print(f"   {stock.symbol:6} - {stock.name} ({stock.exchange})")
            
            # 3. 每只股票的最新价格
            print("\n💰 最新价格 (前5只股票):")
            
            for stock in stocks[:5]:
                latest_price_result = await db.execute(
                    select(StockPrice)
                    .where(StockPrice.stock_id == stock.id)
                    .order_by(desc(StockPrice.date))
                    .limit(1)
                )
                latest_price = latest_price_result.scalar_one_or_none()
                
                if latest_price:
                    # 获取前一日价格计算涨跌
                    prev_price_result = await db.execute(
                        select(StockPrice)
                        .where(StockPrice.stock_id == stock.id)
                        .order_by(desc(StockPrice.date))
                        .offset(1)
                        .limit(1)
                    )
                    prev_price = prev_price_result.scalar_one_or_none()
                    
                    change_str = ""
                    if prev_price:
                        change = latest_price.close - prev_price.close
                        change_pct = (change / prev_price.close) * 100
                        change_str = f" ({change:+.2f}, {change_pct:+.1f}%)"
                    
                    print(f"   {stock.symbol:6} ${latest_price.close:8.2f}{change_str:15} "
                          f"Vol: {latest_price.volume:,}")
            
            # 4. 历史数据范围
            print("\n📅 数据覆盖范围:")
            
            for stock in stocks[:3]:  # 只显示前3只
                date_range_result = await db.execute(
                    select(
                        func.min(StockPrice.date),
                        func.max(StockPrice.date),
                        func.count(StockPrice.id)
                    )
                    .where(StockPrice.stock_id == stock.id)
                )
                min_date, max_date, count = date_range_result.fetchone()
                
                if min_date and max_date:
                    print(f"   {stock.symbol:6} {min_date.strftime('%Y-%m-%d')} 至 "
                          f"{max_date.strftime('%Y-%m-%d')} ({count}条记录)")
            
            # 5. 价格统计
            print("\n📊 价格统计 (AAPL 示例):")
            
            aapl_stats = await db.execute(
                select(
                    func.min(StockPrice.close),
                    func.max(StockPrice.close),
                    func.avg(StockPrice.close),
                    func.sum(StockPrice.volume)
                )
                .join(Stock)
                .where(Stock.symbol == "AAPL")
            )
            min_price, max_price, avg_price, total_volume = aapl_stats.fetchone()
            
            if min_price:
                print(f"   最低价: ${min_price:.2f}")
                print(f"   最高价: ${max_price:.2f}")
                print(f"   平均价: ${avg_price:.2f}")
                print(f"   总成交量: {int(total_volume):,}")
            
            # 6. 最近交易日
            print("\n📋 最近5个交易日 (AAPL):")
            
            recent_prices = await db.execute(
                select(StockPrice)
                .join(Stock)
                .where(Stock.symbol == "AAPL")
                .order_by(desc(StockPrice.date))
                .limit(5)
            )
            
            print("   日期       开盘    最高    最低    收盘    成交量")
            print("   " + "-" * 55)
            
            for price in recent_prices.scalars():
                print(f"   {price.date.strftime('%m-%d')}   "
                      f"{price.open:7.2f} {price.high:7.2f} {price.low:7.2f} "
                      f"{price.close:7.2f} {price.volume/1000000:8.1f}M")
            
            print("\n" + "=" * 60)
            print("✅ 数据演示完成！")
            print("\n🌐 API服务运行中:")
            print("   • 健康检查: http://localhost:8000/health")
            print("   • API文档:  http://localhost:8000/docs")
            print("   • 股票列表: GET /api/v1/stocks")
            print("   • 默认管理员: admin / admin123!@#")
            
        except Exception as e:
            print(f"❌ 演示过程中出现错误: {e}")


if __name__ == "__main__":
    asyncio.run(show_comprehensive_demo())