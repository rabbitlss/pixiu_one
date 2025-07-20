#!/usr/bin/env python3
"""
使用Twelve Data API采集纳斯达克10只样本股票的市场数据
"""
import asyncio
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.core.config import settings
from app.models.stock import Stock, StockPrice
from app.services.providers.twelvedata_provider import TwelveDataProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 你的真实 API key
TWELVE_DATA_API_KEY = "a92596e10e8443d49279b011830f08d2"

# 10只纳斯达克代表性股票
NASDAQ_SAMPLE_STOCKS = [
    "AAPL",   # Apple Inc.
    "MSFT",   # Microsoft Corp.
    "NVDA",   # NVIDIA Corporation
    "META",   # Meta Platforms Inc.
    "NFLX",   # Netflix Inc.
    "PYPL",   # PayPal Holdings Inc.
    "INTC",   # Intel Corporation
    "CSCO",   # Cisco Systems Inc.
    "ADBE",   # Adobe Inc.
    "QCOM"    # QUALCOMM Incorporated
]


async def collect_nasdaq_sample_data():
    """采集纳斯达克样本股票的市场数据"""
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            logger.info("开始采集纳斯达克10只样本股票数据...")
            
            # 使用真实 API key 创建 provider
            provider = TwelveDataProvider(api_key=TWELVE_DATA_API_KEY)
            
            success_count = 0
            fail_count = 0
            
            # 批量获取股票数据（更高效）
            logger.info("批量获取股票实时数据...")
            realtime_data = await provider.fetch_realtime_data(NASDAQ_SAMPLE_STOCKS)
            
            if not realtime_data:
                logger.error("无法获取实时数据")
                return
            
            # 处理每只股票的数据
            for symbol in NASDAQ_SAMPLE_STOCKS:
                try:
                    if symbol not in realtime_data:
                        logger.warning(f"❌ {symbol} 数据缺失")
                        fail_count += 1
                        continue
                    
                    stock_data = realtime_data[symbol]
                    logger.info(f"正在处理 {symbol} - {stock_data.get('name', 'Unknown')}")
                    
                    # 更新股票基础信息
                    await update_stock_info(session, symbol, stock_data)
                    
                    # 保存最新价格数据
                    await save_price_data(session, symbol, stock_data)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ {symbol} 处理异常: {e}")
                    fail_count += 1
            
            await session.commit()
            
            logger.info(f"数据采集完成! 成功: {success_count}, 失败: {fail_count}")
            
            # 显示采集结果统计
            await show_collection_summary(session)
            
            provider.cleanup()
            
    except Exception as e:
        logger.error(f"数据采集失败: {e}")
        raise
    finally:
        await engine.dispose()


async def update_stock_info(session: AsyncSession, symbol: str, stock_data: dict):
    """更新股票基础信息"""
    
    result = await session.execute(
        select(Stock).where(Stock.symbol == symbol)
    )
    stock = result.scalar_one_or_none()
    
    if stock:
        # 更新现有股票信息
        stock.name = stock_data.get('name', stock.name)
        stock.exchange = stock_data.get('exchange', stock.exchange)
        
        # 计算市值（如果有价格和流通股数）
        close_price = float(stock_data.get('close', 0))
        if close_price > 0:
            # 估算市值 (这里使用简化计算，实际需要流通股数)
            estimated_shares = stock.market_cap / close_price if stock.market_cap else None
            if estimated_shares:
                stock.market_cap = close_price * estimated_shares
        
        logger.info(f"Updated stock info for {symbol}")
    else:
        logger.warning(f"Stock {symbol} not found in database")


async def save_price_data(session: AsyncSession, symbol: str, stock_data: dict):
    """保存股票价格数据"""
    
    # 获取股票记录
    result = await session.execute(
        select(Stock).where(Stock.symbol == symbol)
    )
    stock = result.scalar_one_or_none()
    
    if not stock:
        logger.warning(f"Stock {symbol} not found for price data")
        return
    
    # 解析价格数据
    try:
        from datetime import datetime
        import pytz
        
        # 使用收盘时间或当前时间
        price_date = datetime.now(pytz.UTC)
        if 'datetime' in stock_data:
            try:
                price_date = datetime.strptime(stock_data['datetime'], '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            except:
                pass
        
        # 检查是否已存在相同日期的价格记录
        existing_result = await session.execute(
            select(StockPrice).where(
                StockPrice.stock_id == stock.id,
                StockPrice.date >= price_date.replace(hour=0, minute=0, second=0),
                StockPrice.date < price_date.replace(hour=23, minute=59, second=59)
            )
        )
        existing_price = existing_result.scalar_one_or_none()
        
        if existing_price:
            # 更新现有记录
            existing_price.open = float(stock_data.get('open', existing_price.open))
            existing_price.high = float(stock_data.get('high', existing_price.high))
            existing_price.low = float(stock_data.get('low', existing_price.low))
            existing_price.close = float(stock_data.get('close', existing_price.close))
            existing_price.volume = int(stock_data.get('volume', existing_price.volume or 0))
            existing_price.adjusted_close = float(stock_data.get('close', existing_price.close))
        else:
            # 创建新记录
            price_record = StockPrice(
                stock_id=stock.id,
                date=price_date,
                open=float(stock_data.get('open', 0)),
                high=float(stock_data.get('high', 0)),
                low=float(stock_data.get('low', 0)),
                close=float(stock_data.get('close', 0)),
                volume=int(stock_data.get('volume', 0)),
                adjusted_close=float(stock_data.get('close', 0))
            )
            session.add(price_record)
        
        logger.info(f"Saved price data for {symbol}: ${stock_data.get('close', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error saving price data for {symbol}: {e}")


async def show_collection_summary(session: AsyncSession):
    """显示采集结果摘要"""
    
    # 统计股票数量
    result = await session.execute(text("SELECT COUNT(*) FROM stocks"))
    total_stocks = result.scalar()
    
    # 统计价格记录数量
    result = await session.execute(text("SELECT COUNT(*) FROM stock_prices"))
    total_prices = result.scalar()
    
    # 显示最新的股票数据样本
    result = await session.execute(text("""
        SELECT s.symbol, s.name, s.sector, s.market_cap,
               sp.close as latest_price, sp.volume, sp.date
        FROM stocks s 
        LEFT JOIN stock_prices sp ON s.id = sp.stock_id 
        WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
        GROUP BY s.id 
        HAVING sp.date = MAX(sp.date)
        ORDER BY s.market_cap DESC
        LIMIT 10
    """))
    
    stocks_data = result.fetchall()
    
    logger.info("="*80)
    logger.info("📊 纳斯达克样本股票采集结果")
    logger.info("="*80)
    logger.info(f"总股票数量: {total_stocks}")
    logger.info(f"价格记录数量: {total_prices}")
    logger.info("-"*80)
    logger.info(f"{'股票代码':<8} {'公司名称':<25} {'最新价格':<10} {'市值(亿美元)':<12}")
    logger.info("-"*80)
    
    for row in stocks_data:
        symbol, name, sector, market_cap, price, volume, date = row
        market_cap_billion = (market_cap / 1e9) if market_cap else 0
        price_str = f"${price:.2f}" if price else "N/A"
        market_cap_str = f"{market_cap_billion:.0f}" if market_cap_billion > 0 else "N/A"
        
        # 截断过长的公司名称
        display_name = name[:22] + "..." if len(name) > 25 else name
        
        logger.info(f"{symbol:<8} {display_name:<25} {price_str:<10} {market_cap_str:<12}")
    
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(collect_nasdaq_sample_data())