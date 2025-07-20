import yfinance as yf
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.stock_data_service import DataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(DataProvider):
    """Yahoo Finance 数据提供者"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从Yahoo Finance获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            股票数据列表
        """
        try:
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor,
                self._fetch_stock_data_sync,
                symbol,
                start_date,
                end_date
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []
    
    def _fetch_stock_data_sync(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """同步获取股票数据"""
        try:
            # 创建yfinance Ticker对象
            ticker = yf.Ticker(symbol)
            
            # 获取历史数据
            hist = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                auto_adjust=False,
                prepost=True,
                threads=True
            )
            
            if hist.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return []
            
            # 转换为字典列表
            data = []
            for date_index, row in hist.iterrows():
                try:
                    # 确保日期是datetime对象
                    if hasattr(date_index, 'to_pydatetime'):
                        trade_date = date_index.to_pydatetime()
                    else:
                        trade_date = pd.to_datetime(date_index).to_pydatetime()
                    
                    # 验证数据完整性
                    if pd.isna(row['Open']) or pd.isna(row['Close']) or pd.isna(row['High']) or pd.isna(row['Low']):
                        logger.warning(f"Incomplete data for {symbol} on {trade_date}")
                        continue
                    
                    # 验证价格数据的合理性
                    open_price = float(row['Open'])
                    high_price = float(row['High'])
                    low_price = float(row['Low'])
                    close_price = float(row['Close'])
                    volume = int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    
                    if not (low_price <= open_price <= high_price and low_price <= close_price <= high_price):
                        logger.warning(f"Invalid price data for {symbol} on {trade_date}")
                        continue
                    
                    if any(price <= 0 for price in [open_price, high_price, low_price, close_price]):
                        logger.warning(f"Invalid price values (<=0) for {symbol} on {trade_date}")
                        continue
                    
                    data.append({
                        'date': trade_date,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume,
                        'adjusted_close': float(row.get('Adj Close', close_price))
                    })
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing data for {symbol} on {date_index}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error in _fetch_stock_data_sync for {symbol}: {e}")
            return []
    
    async def fetch_realtime_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取实时数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            实时数据字典
        """
        try:
            if not symbols:
                return {}
            
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor,
                self._fetch_realtime_data_sync,
                symbols
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching realtime data: {e}")
            return {}
    
    def _fetch_realtime_data_sync(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """同步获取实时数据"""
        try:
            # 使用yfinance的download函数获取最新数据
            data = yf.download(
                symbols,
                period="1d",
                interval="1m",
                group_by='ticker',
                auto_adjust=False,
                prepost=True,
                threads=True
            )
            
            result = {}
            
            if len(symbols) == 1:
                # 单个股票的情况
                symbol = symbols[0]
                if not data.empty:
                    latest = data.iloc[-1]
                    result[symbol] = self._parse_realtime_record(latest)
            else:
                # 多个股票的情况
                for symbol in symbols:
                    try:
                        if symbol in data.columns.levels[0]:
                            symbol_data = data[symbol]
                            if not symbol_data.empty:
                                latest = symbol_data.iloc[-1]
                                result[symbol] = self._parse_realtime_record(latest)
                    except Exception as e:
                        logger.error(f"Error processing realtime data for {symbol}: {e}")
                        continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _fetch_realtime_data_sync: {e}")
            return {}
    
    def _parse_realtime_record(self, record) -> Dict[str, Any]:
        """解析实时数据记录"""
        try:
            return {
                'open': float(record['Open']) if not pd.isna(record['Open']) else None,
                'high': float(record['High']) if not pd.isna(record['High']) else None,
                'low': float(record['Low']) if not pd.isna(record['Low']) else None,
                'close': float(record['Close']) if not pd.isna(record['Close']) else None,
                'volume': int(record['Volume']) if not pd.isna(record['Volume']) else 0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing realtime record: {e}")
            return {}
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索股票（简单实现，主要用于已知代码的验证）
        
        Args:
            query: 搜索查询
            
        Returns:
            搜索结果列表
        """
        try:
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor,
                self._search_stocks_sync,
                query
            )
            return data
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    def _search_stocks_sync(self, query: str) -> List[Dict[str, Any]]:
        """同步搜索股票"""
        try:
            # Yahoo Finance 没有直接的搜索API，这里实现一个简单的验证
            # 实际生产环境中，你可能需要使用其他的股票搜索API
            
            # 尝试将查询作为股票代码获取信息
            possible_symbols = [
                query.upper(),
                f"{query.upper()}.SS",  # 上海证券交易所
                f"{query.upper()}.SZ",  # 深圳证券交易所
                f"{query.upper()}.HK",  # 香港交易所
            ]
            
            results = []
            
            for symbol in possible_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # 检查是否获取到有效信息
                    if info and 'symbol' in info and info.get('regularMarketPrice'):
                        results.append({
                            'symbol': symbol,
                            'name': info.get('longName', info.get('shortName', symbol)),
                            'exchange': info.get('exchange', 'Unknown'),
                            'sector': info.get('sector'),
                            'industry': info.get('industry'),
                            'market_cap': info.get('marketCap'),
                            'currency': info.get('currency', 'USD')
                        })
                        
                        # 找到一个有效结果就停止
                        break
                        
                except Exception as e:
                    logger.debug(f"Symbol {symbol} not found or invalid: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in _search_stocks_sync: {e}")
            return []
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                self.executor,
                self._get_stock_info_sync,
                symbol
            )
            return info
        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def _get_stock_info_sync(self, symbol: str) -> Optional[Dict[str, Any]]:
        """同步获取股票基本信息"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            return {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'exchange': info.get('exchange'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'USD'),
                'country': info.get('country'),
                'website': info.get('website'),
                'description': info.get('longBusinessSummary', '').strip()[:500]  # 限制描述长度
            }
            
        except Exception as e:
            logger.error(f"Error in _get_stock_info_sync for {symbol}: {e}")
            return None
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)