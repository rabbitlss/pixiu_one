import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import time

from app.services.stock_data_service import DataProvider

logger = logging.getLogger(__name__)


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage 数据提供者"""
    
    def __init__(self, api_key: Optional[str] = None, max_workers: int = 2):
        # Alpha Vantage免费版有严格的API限制
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY', 'FS08JVTKRD8XBUGZ')
        self.base_url = "https://www.alphavantage.co/query"
        self.max_workers = max_workers  # 限制并发数
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # API调用间隔（免费版限制每分钟5次调用）
        self.api_interval = 12  # 秒
        self.last_call_time = 0
        
        # 设置请求session
        self.session = requests.Session()
        
        logger.info(f"Initialized Alpha Vantage provider with API key: {self.api_key[:10]}...")
    
    def _wait_for_rate_limit(self):
        """等待API限制间隔"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.api_interval:
            wait_time = self.api_interval - time_since_last_call
            logger.info(f"Rate limit: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    async def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从Alpha Vantage获取股票历史数据
        
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
            # 等待API限制
            self._wait_for_rate_limit()
            
            # 构建请求参数
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'full'  # 获取完整历史数据
            }
            
            logger.info(f"Fetching data from Alpha Vantage for {symbol}")
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            # 检查错误信息
            if 'Error Message' in data_json:
                logger.error(f"Alpha Vantage error: {data_json['Error Message']}")
                return []
            
            if 'Information' in data_json:
                logger.warning(f"Alpha Vantage info: {data_json['Information']}")
                return []
            
            # 获取时间序列数据
            time_series_key = 'Time Series (Daily)'
            if time_series_key not in data_json:
                logger.error(f"No time series data found for {symbol}")
                return []
            
            time_series = data_json[time_series_key]
            
            # 转换数据格式
            data = []
            for date_str, daily_data in time_series.items():
                try:
                    # 解析日期
                    trade_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # 过滤日期范围
                    if not (start_date <= trade_date <= end_date):
                        continue
                    
                    # 解析价格数据
                    open_price = float(daily_data['1. open'])
                    high_price = float(daily_data['2. high'])
                    low_price = float(daily_data['3. low'])
                    close_price = float(daily_data['4. close'])
                    volume = int(daily_data['5. volume'])
                    
                    # 验证价格数据合理性
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
                        'adjusted_close': close_price  # Alpha Vantage需要单独的API调用获取调整价格
                    })
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error processing data for {symbol} on {date_str}: {e}")
                    continue
            
            # 按日期排序
            data.sort(key=lambda x: x['date'])
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol} from Alpha Vantage")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching data for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in _fetch_stock_data_sync for {symbol}: {e}")
            return []
    
    async def fetch_realtime_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取实时数据
        """
        try:
            if not symbols:
                return {}
            
            # 由于API限制，只处理前几个股票
            limited_symbols = symbols[:3]
            
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                self.executor,
                self._fetch_realtime_data_sync,
                limited_symbols
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching realtime data: {e}")
            return {}
    
    def _fetch_realtime_data_sync(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """同步获取实时数据"""
        try:
            result = {}
            
            # Alpha Vantage需要为每个股票单独调用
            for symbol in symbols:
                try:
                    # 等待API限制
                    self._wait_for_rate_limit()
                    
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': symbol,
                        'apikey': self.api_key
                    }
                    
                    response = self.session.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data_json = response.json()
                    
                    if 'Global Quote' in data_json:
                        quote = data_json['Global Quote']
                        result[symbol] = {
                            'open': float(quote['02. open']) if quote['02. open'] != '--' else None,
                            'high': float(quote['03. high']) if quote['03. high'] != '--' else None,
                            'low': float(quote['04. low']) if quote['04. low'] != '--' else None,
                            'close': float(quote['05. price']) if quote['05. price'] != '--' else None,
                            'volume': int(quote['06. volume']) if quote['06. volume'] != '--' else 0,
                            'timestamp': datetime.now()
                        }
                
                except Exception as e:
                    logger.error(f"Error fetching realtime data for {symbol}: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _fetch_realtime_data_sync: {e}")
            return {}
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索股票
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
            # 等待API限制
            self._wait_for_rate_limit()
            
            # Alpha Vantage提供符号搜索功能
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': query,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            results = []
            if 'bestMatches' in data_json:
                for match in data_json['bestMatches'][:10]:  # 限制结果数量
                    results.append({
                        'symbol': match.get('1. symbol'),
                        'name': match.get('2. name'),
                        'exchange': match.get('4. region'),
                        'sector': None,  # Alpha Vantage搜索不提供详细信息
                        'industry': None,
                        'market_cap': None,
                        'currency': match.get('8. currency', 'USD')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in _search_stocks_sync: {e}")
            return []
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
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
            # 等待API限制
            self._wait_for_rate_limit()
            
            # Alpha Vantage提供公司概况
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            overview = response.json()
            
            if 'Symbol' not in overview:
                return None
            
            return {
                'symbol': symbol,
                'name': overview.get('Name'),
                'exchange': overview.get('Exchange'),
                'sector': overview.get('Sector'),
                'industry': overview.get('Industry'),
                'market_cap': int(overview['MarketCapitalization']) if overview.get('MarketCapitalization', 'None') != 'None' else None,
                'currency': overview.get('Currency', 'USD'),
                'country': overview.get('Country'),
                'website': None,  # Alpha Vantage不提供网站信息
                'description': overview.get('Description', '').strip()[:500]
            }
            
        except Exception as e:
            logger.error(f"Error in _get_stock_info_sync for {symbol}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 等待API限制
            self._wait_for_rate_limit()
            
            # 尝试获取一个简单的股票报价
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            return response.status_code == 200 and 'Global Quote' in data
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        if hasattr(self, 'session'):
            self.session.close()