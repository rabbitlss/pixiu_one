import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from app.services.stock_data_service import DataProvider

logger = logging.getLogger(__name__)


class IEXProvider(DataProvider):
    """IEX Exchange 数据提供者"""
    
    def __init__(self, api_key: Optional[str] = None, max_workers: int = 5):
        self.api_key = api_key or os.getenv('IEX_API_KEY', 'pk_test_demo')  # 使用测试密钥
        self.base_url = "https://cloud.iexapis.com/stable"
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 设置请求session
        self.session = requests.Session()
        self.session.params = {'token': self.api_key}
        
        logger.info(f"Initialized IEX provider with API key: {self.api_key[:10]}...")
    
    async def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从IEX获取股票历史数据
        
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
            # IEX支持不同的时间范围
            days_diff = (end_date - start_date).days
            
            if days_diff <= 30:
                range_param = "1m"
            elif days_diff <= 90:
                range_param = "3m"
            elif days_diff <= 365:
                range_param = "1y"
            else:
                range_param = "2y"
            
            # 构建请求URL
            url = f"{self.base_url}/stock/{symbol}/chart/{range_param}"
            
            logger.info(f"Fetching data from IEX for {symbol} with range {range_param}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            if not data_json:
                logger.warning(f"No data returned for {symbol}")
                return []
            
            # 转换数据格式
            data = []
            for item in data_json:
                try:
                    # 解析日期
                    trade_date = datetime.strptime(item['date'], '%Y-%m-%d')
                    
                    # 过滤日期范围
                    if not (start_date <= trade_date <= end_date):
                        continue
                    
                    # 验证必要字段
                    if not all(key in item for key in ['open', 'high', 'low', 'close', 'volume']):
                        continue
                    
                    # 跳过空值
                    if any(item[key] is None for key in ['open', 'high', 'low', 'close']):
                        continue
                    
                    open_price = float(item['open'])
                    high_price = float(item['high'])
                    low_price = float(item['low'])
                    close_price = float(item['close'])
                    volume = int(item['volume']) if item['volume'] is not None else 0
                    
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
                        'adjusted_close': close_price  # IEX不提供调整后价格，使用收盘价
                    })
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error processing data for {symbol} on {item.get('date', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol} from IEX")
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
            result = {}
            
            # IEX支持批量获取报价
            symbols_str = ",".join(symbols)
            url = f"{self.base_url}/stock/market/batch"
            params = {
                'symbols': symbols_str,
                'types': 'quote',
                'token': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            for symbol, data in data_json.items():
                if 'quote' in data:
                    quote = data['quote']
                    result[symbol] = {
                        'open': quote.get('open'),
                        'high': quote.get('high'),
                        'low': quote.get('low'),
                        'close': quote.get('latestPrice'),
                        'volume': quote.get('volume', 0),
                        'timestamp': datetime.now()
                    }
            
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
            # IEX提供股票搜索API
            url = f"{self.base_url}/search/{query}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            results = []
            for item in data_json[:10]:  # 限制结果数量
                results.append({
                    'symbol': item.get('symbol'),
                    'name': item.get('securityName'),
                    'exchange': item.get('exchange'),
                    'sector': item.get('sector'),
                    'industry': item.get('industry'),
                    'market_cap': None,  # IEX搜索不直接提供市值
                    'currency': 'USD'
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
            # 获取公司信息
            url = f"{self.base_url}/stock/{symbol}/company"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            company_info = response.json()
            
            # 获取统计信息
            stats_url = f"{self.base_url}/stock/{symbol}/stats"
            stats_response = self.session.get(stats_url, timeout=30)
            stats_info = {}
            if stats_response.status_code == 200:
                stats_info = stats_response.json()
            
            return {
                'symbol': symbol,
                'name': company_info.get('companyName'),
                'exchange': company_info.get('exchange'),
                'sector': company_info.get('sector'),
                'industry': company_info.get('industry'),
                'market_cap': stats_info.get('marketcap'),
                'currency': 'USD',
                'country': company_info.get('country'),
                'website': company_info.get('website'),
                'description': company_info.get('description', '').strip()[:500]
            }
            
        except Exception as e:
            logger.error(f"Error in _get_stock_info_sync for {symbol}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            # 尝试获取一个简单的股票信息
            url = f"{self.base_url}/stock/AAPL/quote"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        if hasattr(self, 'session'):
            self.session.close()