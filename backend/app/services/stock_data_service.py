from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import logging
import asyncio
from abc import ABC, abstractmethod

from app.models.stock import Stock, StockPrice, TechnicalIndicator
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    @abstractmethod
    async def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取股票数据"""
        pass
    
    @abstractmethod
    async def fetch_realtime_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时数据"""
        pass
    
    @abstractmethod
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        pass


class StockDataService:
    """股票数据服务"""
    
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
    
    async def update_stock_data(self, stock_id: int, days: int = 30) -> bool:
        """
        更新指定股票的数据
        
        Args:
            stock_id: 股票ID
            days: 更新的天数
            
        Returns:
            是否成功更新
        """
        async with AsyncSessionLocal() as db:
            try:
                # 获取股票信息
                result = await db.execute(select(Stock).where(Stock.id == stock_id))
                stock = result.scalar_one_or_none()
                
                if not stock or not stock.is_active:
                    logger.warning(f"Stock {stock_id} not found or inactive")
                    return False
                
                # 计算更新日期范围
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # 获取最后更新日期
                last_price_result = await db.execute(
                    select(StockPrice)
                    .where(StockPrice.stock_id == stock_id)
                    .order_by(desc(StockPrice.date))
                    .limit(1)
                )
                last_price = last_price_result.scalar_one_or_none()
                
                if last_price:
                    # 从最后更新日期的下一天开始
                    start_date = max(start_date, last_price.date + timedelta(days=1))
                
                if start_date >= end_date:
                    logger.info(f"Stock {stock.symbol} data is up to date")
                    return True
                
                # 从数据提供者获取数据
                data = await self.data_provider.fetch_stock_data(
                    stock.symbol, start_date, end_date
                )
                
                if not data:
                    logger.warning(f"No data received for stock {stock.symbol}")
                    return False
                
                # 保存数据到数据库
                price_objects = []
                for record in data:
                    try:
                        price_obj = StockPrice(
                            stock_id=stock_id,
                            date=record['date'],
                            open=float(record['open']),
                            high=float(record['high']),
                            low=float(record['low']),
                            close=float(record['close']),
                            volume=int(record['volume']),
                            adjusted_close=float(record.get('adjusted_close', record['close']))
                        )
                        price_objects.append(price_obj)
                    except (ValueError, KeyError) as e:
                        logger.error(f"Invalid data format for {stock.symbol}: {e}")
                        continue
                
                if price_objects:
                    db.add_all(price_objects)
                    await db.commit()
                    logger.info(f"Updated {len(price_objects)} price records for {stock.symbol}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error updating stock data for {stock_id}: {e}")
                await db.rollback()
                return False
    
    async def update_all_active_stocks(self, days: int = 7) -> Dict[str, int]:
        """
        更新所有活跃股票的数据
        
        Args:
            days: 更新的天数
            
        Returns:
            更新结果统计
        """
        async with AsyncSessionLocal() as db:
            # 获取所有活跃股票
            result = await db.execute(
                select(Stock).where(Stock.is_active == True)
            )
            active_stocks = result.scalars().all()
            
            if not active_stocks:
                logger.warning("No active stocks found")
                return {"total": 0, "success": 0, "failed": 0}
            
            logger.info(f"Starting to update {len(active_stocks)} active stocks")
            
            # 并发更新（限制并发数以避免过载）
            semaphore = asyncio.Semaphore(5)  # 最多5个并发请求
            
            async def update_with_semaphore(stock_id: int) -> bool:
                async with semaphore:
                    return await self.update_stock_data(stock_id, days)
            
            # 执行并发更新
            tasks = [update_with_semaphore(stock.id) for stock in active_stocks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            success_count = sum(1 for result in results if result is True)
            failed_count = len(results) - success_count
            
            logger.info(f"Update completed: {success_count} success, {failed_count} failed")
            
            return {
                "total": len(active_stocks),
                "success": success_count,
                "failed": failed_count
            }
    
    async def get_realtime_quotes(self, stock_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        获取实时行情数据
        
        Args:
            stock_ids: 股票ID列表
            
        Returns:
            股票实时数据字典
        """
        async with AsyncSessionLocal() as db:
            try:
                # 获取股票信息
                result = await db.execute(
                    select(Stock).where(
                        and_(
                            Stock.id.in_(stock_ids),
                            Stock.is_active == True
                        )
                    )
                )
                stocks = result.scalars().all()
                
                if not stocks:
                    return {}
                
                # 获取股票代码列表
                symbols = [stock.symbol for stock in stocks]
                
                # 从数据提供者获取实时数据
                realtime_data = await self.data_provider.fetch_realtime_data(symbols)
                
                # 转换为以股票ID为键的字典
                result_data = {}
                for stock in stocks:
                    if stock.symbol in realtime_data:
                        result_data[stock.id] = realtime_data[stock.symbol]
                
                return result_data
                
            except Exception as e:
                logger.error(f"Error fetching realtime quotes: {e}")
                return {}
    
    async def search_and_add_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索并可选择添加新股票
        
        Args:
            query: 搜索查询
            limit: 返回结果限制
            
        Returns:
            搜索结果列表
        """
        try:
            # 从数据提供者搜索股票
            search_results = await self.data_provider.search_stocks(query)
            
            if not search_results:
                return []
            
            # 限制结果数量
            search_results = search_results[:limit]
            
            # 检查哪些股票已经在数据库中
            async with AsyncSessionLocal() as db:
                symbols = [result['symbol'] for result in search_results]
                existing_result = await db.execute(
                    select(Stock.symbol).where(Stock.symbol.in_(symbols))
                )
                existing_symbols = set(row[0] for row in existing_result.fetchall())
                
                # 标记已存在的股票
                for result in search_results:
                    result['exists_in_db'] = result['symbol'] in existing_symbols
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    async def calculate_technical_indicators(self, stock_id: int, indicator_types: List[str]) -> bool:
        """
        计算技术指标
        
        Args:
            stock_id: 股票ID
            indicator_types: 指标类型列表 ['MA', 'EMA', 'RSI', 'MACD']
            
        Returns:
            是否成功计算
        """
        async with AsyncSessionLocal() as db:
            try:
                # 获取股票价格数据（最近100天用于计算指标）
                result = await db.execute(
                    select(StockPrice)
                    .where(StockPrice.stock_id == stock_id)
                    .order_by(desc(StockPrice.date))
                    .limit(100)
                )
                prices = result.scalars().all()
                
                if len(prices) < 20:  # 至少需要20天数据
                    logger.warning(f"Insufficient price data for stock {stock_id}")
                    return False
                
                # 按日期正序排列
                prices = sorted(prices, key=lambda x: x.date)
                
                # 提取收盘价
                closes = [float(price.close) for price in prices]
                
                indicator_objects = []
                
                # 计算各种技术指标
                for indicator_type in indicator_types:
                    if indicator_type == 'MA':
                        # 移动平均线
                        for period in [5, 10, 20, 50]:
                            if len(closes) >= period:
                                ma_values = self._calculate_ma(closes, period)
                                for i, value in enumerate(ma_values):
                                    if value is not None:
                                        indicator_objects.append(TechnicalIndicator(
                                            stock_id=stock_id,
                                            date=prices[i + period - 1].date,
                                            indicator_type='MA',
                                            period=period,
                                            value=value
                                        ))
                    
                    elif indicator_type == 'RSI':
                        # RSI指标
                        rsi_values = self._calculate_rsi(closes, 14)
                        for i, value in enumerate(rsi_values):
                            if value is not None:
                                indicator_objects.append(TechnicalIndicator(
                                    stock_id=stock_id,
                                    date=prices[i + 14].date,
                                    indicator_type='RSI',
                                    period=14,
                                    value=value
                                ))
                
                # 删除现有的指标数据（避免重复）
                for indicator_type in indicator_types:
                    await db.execute(
                        select(TechnicalIndicator).where(
                            and_(
                                TechnicalIndicator.stock_id == stock_id,
                                TechnicalIndicator.indicator_type == indicator_type
                            )
                        ).delete()
                    )
                
                # 保存新的指标数据
                if indicator_objects:
                    db.add_all(indicator_objects)
                    await db.commit()
                    logger.info(f"Calculated {len(indicator_objects)} technical indicators for stock {stock_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error calculating technical indicators for stock {stock_id}: {e}")
                await db.rollback()
                return False
    
    def _calculate_ma(self, prices: List[float], period: int) -> List[Optional[float]]:
        """计算移动平均线"""
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(None)
            else:
                ma = sum(prices[i - period + 1:i + 1]) / period
                ma_values.append(ma)
        return ma_values
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        # 计算价格变化
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # 分离涨跌
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        rsi_values = [None] * (period + 1)  # 前period+1个值为None
        
        # 计算初始平均涨跌幅
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(deltas)):
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
            
            # 更新平均涨跌幅（使用指数移动平均）
            if i < len(deltas) - 1:
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        return rsi_values