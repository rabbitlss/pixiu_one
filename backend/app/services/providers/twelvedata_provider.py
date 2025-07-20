import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import time

from app.services.stock_data_service import DataProvider

logger = logging.getLogger(__name__)


class TwelveDataProvider(DataProvider):
    """Twelve Data API 数据提供者"""
    
    def __init__(self, api_key: Optional[str] = None, max_workers: int = 2):
        self.api_key = api_key or "demo"  # 使用 demo key
        self.base_url = "https://api.twelvedata.com"
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # API调用间隔（免费版限制较宽松）
        self.api_interval = 2  # 秒
        self.last_call_time = 0
        
        # 设置请求session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantInfo-Collector/1.0'
        })
        
        logger.info(f"Initialized Twelve Data provider with API key: {self.api_key}")
    
    def _wait_for_rate_limit(self):
        """等待满足API调用限制"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.api_interval:
            wait_time = self.api_interval - time_since_last_call
            logger.info(f"Rate limit: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    async def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从Twelve Data获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            股票数据列表
        """
        try:
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
            self._wait_for_rate_limit()
            
            # 构建请求参数
            params = {
                'symbol': symbol,
                'interval': '1day',
                'apikey': self.api_key,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'format': 'JSON'
            }
            
            logger.info(f"Fetching data from Twelve Data for {symbol}")
            
            response = self.session.get(f"{self.base_url}/time_series", params=params, timeout=30)
            response.raise_for_status()
            
            data_json = response.json()
            
            # 检查错误信息
            if 'status' in data_json and data_json['status'] == 'error':
                logger.error(f"Twelve Data error: {data_json.get('message', 'Unknown error')}")
                return []
            
            if 'values' not in data_json:
                logger.warning(f"No price data available for {symbol}")
                return []
            
            # 解析价格数据
            price_data = []
            for item in data_json['values']:
                try:
                    price_record = {
                        'date': datetime.strptime(item['datetime'], '%Y-%m-%d'),
                        'open': float(item['open']),
                        'high': float(item['high']),
                        'low': float(item['low']),
                        'close': float(item['close']),
                        'volume': int(item.get('volume', 0)),
                        'adjusted_close': float(item['close'])  # Twelve Data 默认提供调整价格
                    }
                    price_data.append(price_record)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing price record for {symbol}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(price_data)} price records for {symbol}")
            return price_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {e}")
            return []
    
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """获取公司概况信息"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._get_company_profile_sync,
                symbol
            )
        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {e}")
            return {}
    
    def _get_company_profile_sync(self, symbol: str) -> Dict[str, Any]:
        """同步获取公司概况"""
        try:
            self._wait_for_rate_limit()
            
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/profile", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Twelve Data profile error for {symbol}: {data.get('message')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {e}")
            return {}
    
    async def get_financial_statements(self, symbol: str) -> Dict[str, Any]:
        """获取财务报表数据"""
        try:
            loop = asyncio.get_event_loop()
            
            # 并行获取三种财务报表
            income_task = loop.run_in_executor(
                self.executor, self._get_income_statement_sync, symbol
            )
            balance_task = loop.run_in_executor(
                self.executor, self._get_balance_sheet_sync, symbol
            )
            cashflow_task = loop.run_in_executor(
                self.executor, self._get_cash_flow_sync, symbol
            )
            
            income_data, balance_data, cashflow_data = await asyncio.gather(
                income_task, balance_task, cashflow_task, return_exceptions=True
            )
            
            return {
                'income_statement': income_data if not isinstance(income_data, Exception) else {},
                'balance_sheet': balance_data if not isinstance(balance_data, Exception) else {},
                'cash_flow': cashflow_data if not isinstance(cashflow_data, Exception) else {}
            }
            
        except Exception as e:
            logger.error(f"Error fetching financial statements for {symbol}: {e}")
            return {'income_statement': {}, 'balance_sheet': {}, 'cash_flow': {}}
    
    def _get_income_statement_sync(self, symbol: str) -> Dict[str, Any]:
        """获取损益表"""
        try:
            self._wait_for_rate_limit()
            
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/income_statement", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Income statement error for {symbol}: {data.get('message')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting income statement for {symbol}: {e}")
            return {}
    
    def _get_balance_sheet_sync(self, symbol: str) -> Dict[str, Any]:
        """获取资产负债表"""
        try:
            self._wait_for_rate_limit()
            
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/balance_sheet", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Balance sheet error for {symbol}: {data.get('message')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting balance sheet for {symbol}: {e}")
            return {}
    
    def _get_cash_flow_sync(self, symbol: str) -> Dict[str, Any]:
        """获取现金流量表"""
        try:
            self._wait_for_rate_limit()
            
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/cash_flow", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Cash flow error for {symbol}: {data.get('message')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting cash flow for {symbol}: {e}")
            return {}
    
    async def fetch_realtime_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时数据"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._fetch_realtime_data_sync,
                symbols
            )
        except Exception as e:
            logger.error(f"Error fetching realtime data: {e}")
            return {}
    
    def _fetch_realtime_data_sync(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """同步获取实时数据"""
        try:
            self._wait_for_rate_limit()
            
            # Twelve Data 支持批量查询
            symbols_str = ','.join(symbols)
            params = {
                'symbol': symbols_str,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/quote", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Realtime data error: {data.get('message')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting realtime data: {e}")
            return {}
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._search_stocks_sync,
                query
            )
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    def _search_stocks_sync(self, query: str) -> List[Dict[str, Any]]:
        """同步搜索股票"""
        try:
            self._wait_for_rate_limit()
            
            params = {
                'symbol': query,
                'apikey': self.api_key
            }
            
            response = self.session.get(f"{self.base_url}/symbol_search", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Stock search error: {data.get('message')}")
                return []
            
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    def cleanup(self):
        """清理资源"""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Twelve Data provider cleaned up")