#!/usr/bin/env python3
"""
简单测试Alpha Vantage API
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.services.providers.alphavantage_provider import AlphaVantageProvider

async def test_simple_fetch():
    """简单测试获取数据"""
    print("🔍 测试 Alpha Vantage 数据获取...")
    
    provider = AlphaVantageProvider()
    
    # 测试获取AAPL的历史数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 获取 AAPL 数据: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    data = await provider.fetch_stock_data("AAPL", start_date, end_date)
    
    if data:
        print(f"✅ 成功获取 {len(data)} 条记录")
        for record in data[-3:]:  # 显示最后3条
            print(f"   {record['date'].strftime('%Y-%m-%d')}: "
                  f"开盘${record['open']:.2f} 收盘${record['close']:.2f} "
                  f"成交量{record['volume']:,}")
    else:
        print("❌ 未获取到数据")
    
    return len(data) if data else 0

if __name__ == "__main__":
    asyncio.run(test_simple_fetch())