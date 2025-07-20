#!/usr/bin/env python3
"""
逐只采集纳斯达克样本股票数据（避免API限制）
"""
import asyncio
import logging
import requests
import time
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.core.config import settings
from app.models.stock import Stock, StockPrice

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


def get_stock_quote(symbol: str) -> dict:
    """获取单只股票报价数据"""
    try:
        url = "https://api.twelvedata.com/quote"
        params = {
            'symbol': symbol,
            'apikey': TWELVE_DATA_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'status' in data and data['status'] == 'error':
            logger.error(f"API error for {symbol}: {data.get('message')}")
            return {}
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return {}


async def collect_nasdaq_individual_data():
    """逐只采集纳斯达克样本股票数据"""
    
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
            logger.info("开始逐只采集纳斯达克10只样本股票数据...")
            
            success_count = 0
            fail_count = 0
            
            for i, symbol in enumerate(NASDAQ_SAMPLE_STOCKS, 1):
                try:
                    logger.info(f"[{i}/10] 正在获取 {symbol} 数据...")
                    
                    # 获取股票数据
                    stock_data = get_stock_quote(symbol)
                    
                    if not stock_data:
                        logger.warning(f"❌ {symbol} 数据获取失败")
                        fail_count += 1
                        time.sleep(8)  # 等待更长时间
                        continue
                    
                    logger.info(f"✅ {symbol} - {stock_data.get('name', 'Unknown')} - ${stock_data.get('close', 'N/A')}")
                    
                    # 更新股票基础信息
                    await update_stock_info(session, symbol, stock_data)
                    
                    # 保存最新价格数据
                    await save_price_data(session, symbol, stock_data)
                    
                    success_count += 1
                    
                    # API限制：等待8秒避免超出每分钟8次限制
                    if i < len(NASDAQ_SAMPLE_STOCKS):
                        logger.info(f"等待8秒以避免API限制...")
                        time.sleep(8)
                    
                except Exception as e:
                    logger.error(f"❌ {symbol} 处理异常: {e}")
                    fail_count += 1
                    time.sleep(8)  # 出错时也要等待
            
            await session.commit()
            
            logger.info(f"数据采集完成! 成功: {success_count}, 失败: {fail_count}")
            
            # 显示采集结果统计
            await show_collection_summary(session)
            
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
        
        # 计算市值（使用收盘价和估算的流通股数）
        close_price = float(stock_data.get('close', 0))
        if close_price > 0 and stock.market_cap:
            # 根据之前的市值和当前价格重新估算
            estimated_shares = stock.market_cap / 200  # 假设之前价格约200美元
            stock.market_cap = close_price * estimated_shares
        
        logger.debug(f"Updated stock info for {symbol}")
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
        
        # 使用股票数据中的日期
        price_date = datetime.now(pytz.UTC)
        if 'datetime' in stock_data:
            try:
                price_date = datetime.strptime(stock_data['datetime'], '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            except:
                pass
        
        # 检查是否已存在相同日期的价格记录
        from sqlalchemy import and_, func
        existing_result = await session.execute(
            select(StockPrice).where(
                and_(
                    StockPrice.stock_id == stock.id,
                    func.date(StockPrice.date) == price_date.date()
                )
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
            logger.debug(f"Updated price data for {symbol}")
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
            logger.debug(f"Created new price data for {symbol}")
        
    except Exception as e:
        logger.error(f"Error saving price data for {symbol}: {e}")


async def show_collection_summary(session: AsyncSession):
    """显示采集结果摘要"""
    
    logger.info("="*80)
    logger.info("📊 纳斯达克样本股票采集结果")
    logger.info("="*80)
    
    # 显示最新的股票数据
    result = await session.execute(text("""
        SELECT s.symbol, s.name, s.sector, s.market_cap,
               sp.close as latest_price, sp.volume, 
               sp.high - sp.low as daily_range,
               CASE 
                   WHEN sp.close > sp.open THEN '↗️'
                   WHEN sp.close < sp.open THEN '↘️'
                   ELSE '→'
               END as trend
        FROM stocks s 
        LEFT JOIN stock_prices sp ON s.id = sp.stock_id 
        WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
        AND sp.date = (
            SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
        )
        ORDER BY sp.close DESC
    """))
    
    stocks_data = result.fetchall()
    
    logger.info(f"{'代码':<6} {'公司名称':<20} {'价格':<8} {'成交量':<12} {'日内振幅':<8} {'趋势':<4}")
    logger.info("-"*70)
    
    total_market_value = 0
    
    for row in stocks_data:
        symbol, name, sector, market_cap, price, volume, daily_range, trend = row
        
        # 格式化显示
        price_str = f"${price:.2f}" if price else "N/A"
        volume_str = f"{volume:,}" if volume else "N/A"
        range_str = f"${daily_range:.2f}" if daily_range else "N/A"
        
        # 截断过长的公司名称
        display_name = name[:17] + "..." if len(name) > 20 else name
        
        logger.info(f"{symbol:<6} {display_name:<20} {price_str:<8} {volume_str:<12} {range_str:<8} {trend:<4}")
        
        if price and market_cap:
            total_market_value += market_cap
    
    logger.info("-"*70)
    if total_market_value > 0:
        logger.info(f"样本总市值: ${total_market_value/1e12:.2f}万亿美元")
    
    # 统计信息
    result = await session.execute(text("SELECT COUNT(*) FROM stocks"))
    total_stocks = result.scalar()
    
    result = await session.execute(text("SELECT COUNT(*) FROM stock_prices"))
    total_prices = result.scalar()
    
    logger.info(f"数据库统计: {total_stocks}只股票, {total_prices}条价格记录")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(collect_nasdaq_individual_data())