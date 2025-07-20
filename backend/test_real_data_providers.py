#!/usr/bin/env python3
"""
测试真实数据提供者
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.services.providers.iex_provider import IEXProvider
from app.services.providers.alphavantage_provider import AlphaVantageProvider
from app.services.stock_data_service import StockDataService
from app.db.database import AsyncSessionLocal
from app.models.stock import Stock, StockPrice
from sqlalchemy import select


async def test_iex_provider():
    """测试IEX数据提供者"""
    print("🔍 测试 IEX Exchange 数据提供者...")
    
    iex = IEXProvider()
    
    # 1. 测试连接
    print("  测试连接...")
    connection_ok = iex.test_connection()
    print(f"  连接状态: {'✅ 成功' if connection_ok else '❌ 失败'}")
    
    if not connection_ok:
        print("  IEX连接失败，跳过后续测试")
        return False
    
    # 2. 测试获取股票信息
    print("  测试获取股票信息...")
    try:
        stock_info = await iex.get_stock_info("AAPL")
        if stock_info:
            print(f"  ✅ 股票信息: {stock_info['name']} ({stock_info['symbol']})")
            print(f"     交易所: {stock_info['exchange']}")
            print(f"     行业: {stock_info['sector']}")
        else:
            print("  ❌ 无法获取股票信息")
            return False
    except Exception as e:
        print(f"  ❌ 获取股票信息失败: {e}")
        return False
    
    # 3. 测试获取历史数据
    print("  测试获取历史数据...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        historical_data = await iex.fetch_stock_data("AAPL", start_date, end_date)
        if historical_data:
            print(f"  ✅ 获取到 {len(historical_data)} 条历史记录")
            latest = historical_data[-1]
            print(f"     最新: {latest['date'].strftime('%Y-%m-%d')} 收盘价: ${latest['close']:.2f}")
        else:
            print("  ❌ 无法获取历史数据")
            return False
    except Exception as e:
        print(f"  ❌ 获取历史数据失败: {e}")
        return False
    
    # 4. 测试搜索功能
    print("  测试搜索功能...")
    try:
        search_results = await iex.search_stocks("Apple")
        if search_results:
            print(f"  ✅ 搜索到 {len(search_results)} 个结果")
            for result in search_results[:3]:
                print(f"     {result['symbol']}: {result['name']}")
        else:
            print("  ⚠️ 搜索无结果")
    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
    
    print("  🎉 IEX测试完成\n")
    return True


async def test_alphavantage_provider():
    """测试Alpha Vantage数据提供者"""
    print("🔍 测试 Alpha Vantage 数据提供者...")
    
    av = AlphaVantageProvider()
    
    # 1. 测试连接
    print("  测试连接...")
    connection_ok = av.test_connection()
    print(f"  连接状态: {'✅ 成功' if connection_ok else '❌ 失败'}")
    
    if not connection_ok:
        print("  Alpha Vantage连接失败，可能是API密钥问题")
        return False
    
    # 2. 测试获取股票信息
    print("  测试获取股票信息...")
    try:
        stock_info = await av.get_stock_info("AAPL")
        if stock_info:
            print(f"  ✅ 股票信息: {stock_info['name']} ({stock_info['symbol']})")
            print(f"     交易所: {stock_info['exchange']}")
            print(f"     行业: {stock_info['sector']}")
            if stock_info['market_cap']:
                print(f"     市值: ${stock_info['market_cap']:,}")
        else:
            print("  ❌ 无法获取股票信息")
            return False
    except Exception as e:
        print(f"  ❌ 获取股票信息失败: {e}")
        return False
    
    # 3. 测试获取历史数据
    print("  测试获取历史数据...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        historical_data = await av.fetch_stock_data("AAPL", start_date, end_date)
        if historical_data:
            print(f"  ✅ 获取到 {len(historical_data)} 条历史记录")
            latest = historical_data[-1]
            print(f"     最新: {latest['date'].strftime('%Y-%m-%d')} 收盘价: ${latest['close']:.2f}")
        else:
            print("  ❌ 无法获取历史数据")
            return False
    except Exception as e:
        print(f"  ❌ 获取历史数据失败: {e}")
        return False
    
    print("  🎉 Alpha Vantage测试完成\n")
    return True


async def update_real_data_to_database(provider_name, provider):
    """使用真实数据更新数据库"""
    print(f"📊 使用 {provider_name} 更新数据库...")
    
    service = StockDataService(provider)
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取数据库中的股票
            result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = result.scalars().all()
            
            updated_count = 0
            
            for stock in stocks[:3]:  # 只更新前3只股票以避免API限制
                print(f"  更新 {stock.symbol}...")
                
                try:
                    success = await service.update_stock_data(stock.id, days=7)
                    if success:
                        updated_count += 1
                        print(f"    ✅ {stock.symbol} 更新成功")
                    else:
                        print(f"    ❌ {stock.symbol} 更新失败")
                except Exception as e:
                    print(f"    ❌ {stock.symbol} 更新异常: {e}")
            
            print(f"  📈 成功更新 {updated_count}/{min(len(stocks), 3)} 只股票")
            
            # 显示更新后的数据
            if updated_count > 0:
                print("  最新数据预览:")
                for stock in stocks[:updated_count]:
                    latest_price_result = await db.execute(
                        select(StockPrice)
                        .where(StockPrice.stock_id == stock.id)
                        .order_by(StockPrice.date.desc())
                        .limit(1)
                    )
                    latest_price = latest_price_result.scalar_one_or_none()
                    
                    if latest_price:
                        print(f"    {stock.symbol}: {latest_price.date.strftime('%Y-%m-%d')} "
                              f"${latest_price.close:.2f} (Vol: {latest_price.volume:,})")
            
            return updated_count > 0
            
        except Exception as e:
            print(f"  ❌ 数据库更新失败: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 真实数据提供者测试\n")
    
    # 测试IEX
    iex_success = await test_iex_provider()
    
    # 测试Alpha Vantage
    av_success = await test_alphavantage_provider()
    
    # 根据测试结果决定使用哪个提供者更新数据库
    if iex_success:
        print("🔄 使用 IEX 更新数据库...")
        iex = IEXProvider()
        await update_real_data_to_database("IEX Exchange", iex)
    elif av_success:
        print("🔄 使用 Alpha Vantage 更新数据库...")
        av = AlphaVantageProvider()
        await update_real_data_to_database("Alpha Vantage", av)
    else:
        print("❌ 所有数据提供者都无法正常工作")
        return
    
    print("\n✅ 真实数据测试完成！")
    print("🌐 可以通过以下方式查看更新的数据:")
    print("   - API: http://localhost:8000/api/v1/stocks")
    print("   - 详情: GET /api/v1/stocks/{id}")


if __name__ == "__main__":
    asyncio.run(main())