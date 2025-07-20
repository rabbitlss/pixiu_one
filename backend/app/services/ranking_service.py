"""
个性化股票排名服务
基于真实市场数据实现多维度排名算法
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, desc, asc
from datetime import datetime, timedelta

from app.models.stock import Stock, StockPrice

logger = logging.getLogger(__name__)


class StockRankingService:
    """股票排名服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_activity_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        活跃度排名 - 基于成交量
        优先级: 1
        """
        try:
            query = text("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    sp.close as current_price,
                    sp.volume,
                    sp.volume * sp.close as turnover,
                    RANK() OVER (ORDER BY sp.volume DESC) as volume_rank,
                    RANK() OVER (ORDER BY sp.volume * sp.close DESC) as turnover_rank
                FROM stocks s
                INNER JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
                AND sp.date = (
                    SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
                )
                ORDER BY sp.volume DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                symbol, name, sector, price, volume, turnover, vol_rank, turn_rank = row
                
                rankings.append({
                    "rank": i,
                    "symbol": symbol,
                    "name": name,
                    "sector": sector,
                    "current_price": float(price) if price else 0,
                    "volume": int(volume) if volume else 0,
                    "turnover": float(turnover) if turnover else 0,
                    "volume_rank": int(vol_rank) if vol_rank else 0,
                    "turnover_rank": int(turn_rank) if turn_rank else 0,
                    "activity_score": self._calculate_activity_score(volume, turnover),
                    "ranking_type": "activity"
                })
            
            logger.info(f"Generated activity ranking for {len(rankings)} stocks")
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating activity ranking: {e}")
            return []
    
    async def get_volatility_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        波动性排名 - 基于日内振幅和价格波动
        优先级: 2
        """
        try:
            query = text("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    sp.close as current_price,
                    sp.high,
                    sp.low,
                    sp.open,
                    (sp.high - sp.low) as daily_range,
                    ((sp.high - sp.low) / sp.close * 100) as volatility_percent,
                    ABS(sp.close - sp.open) as intraday_move,
                    (ABS(sp.close - sp.open) / sp.open * 100) as move_percent
                FROM stocks s
                INNER JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
                AND sp.date = (
                    SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
                )
                ORDER BY ((sp.high - sp.low) / sp.close * 100) DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                symbol, name, sector, price, high, low, open_price, daily_range, volatility_pct, intraday_move, move_pct = row
                
                rankings.append({
                    "rank": i,
                    "symbol": symbol,
                    "name": name,
                    "sector": sector,
                    "current_price": float(price) if price else 0,
                    "high": float(high) if high else 0,
                    "low": float(low) if low else 0,
                    "open": float(open_price) if open_price else 0,
                    "daily_range": float(daily_range) if daily_range else 0,
                    "volatility_percent": float(volatility_pct) if volatility_pct else 0,
                    "intraday_move": float(intraday_move) if intraday_move else 0,
                    "move_percent": float(move_pct) if move_pct else 0,
                    "volatility_score": self._calculate_volatility_score(volatility_pct, move_pct),
                    "ranking_type": "volatility"
                })
            
            logger.info(f"Generated volatility ranking for {len(rankings)} stocks")
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating volatility ranking: {e}")
            return []
    
    async def get_performance_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        涨跌排名 - 基于当日表现
        优先级: 3  
        """
        try:
            query = text("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    sp.close as current_price,
                    sp.open,
                    (sp.close - sp.open) as price_change,
                    ((sp.close - sp.open) / sp.open * 100) as percent_change,
                    sp.volume,
                    CASE 
                        WHEN sp.close > sp.open THEN 'UP'
                        WHEN sp.close < sp.open THEN 'DOWN'
                        ELSE 'FLAT'
                    END as direction,
                    CASE 
                        WHEN sp.close > sp.open THEN '🔺'
                        WHEN sp.close < sp.open THEN '🔻'
                        ELSE '➡️'
                    END as trend_emoji
                FROM stocks s
                INNER JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
                AND sp.date = (
                    SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
                )
                ORDER BY ((sp.close - sp.open) / sp.open * 100) DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                symbol, name, sector, price, open_price, price_change, percent_change, volume, direction, trend_emoji = row
                
                rankings.append({
                    "rank": i,
                    "symbol": symbol,
                    "name": name,
                    "sector": sector,
                    "current_price": float(price) if price else 0,
                    "open_price": float(open_price) if open_price else 0,
                    "price_change": float(price_change) if price_change else 0,
                    "percent_change": float(percent_change) if percent_change else 0,
                    "volume": int(volume) if volume else 0,
                    "direction": direction,
                    "trend_emoji": trend_emoji,
                    "performance_score": abs(float(percent_change)) if percent_change else 0,
                    "ranking_type": "performance"
                })
            
            logger.info(f"Generated performance ranking for {len(rankings)} stocks")
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating performance ranking: {e}")
            return []
    
    async def get_market_cap_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        市值排名 - 基于公司市值
        优先级: 4
        """
        try:
            query = text("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    s.market_cap,
                    sp.close as current_price,
                    sp.volume,
                    (s.market_cap / 1000000000) as market_cap_billions
                FROM stocks s
                INNER JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
                AND sp.date = (
                    SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
                )
                AND s.market_cap IS NOT NULL
                ORDER BY s.market_cap DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                symbol, name, sector, market_cap, price, volume, market_cap_billions = row
                
                rankings.append({
                    "rank": i,
                    "symbol": symbol,
                    "name": name,
                    "sector": sector,
                    "market_cap": float(market_cap) if market_cap else 0,
                    "market_cap_billions": float(market_cap_billions) if market_cap_billions else 0,
                    "current_price": float(price) if price else 0,
                    "volume": int(volume) if volume else 0,
                    "market_cap_score": self._calculate_market_cap_score(market_cap),
                    "ranking_type": "market_cap"
                })
            
            logger.info(f"Generated market cap ranking for {len(rankings)} stocks")
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating market cap ranking: {e}")
            return []
    
    async def get_price_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        价格排名 - 基于股票价格
        优先级: 5
        """
        try:
            query = text("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    sp.close as current_price,
                    sp.high,
                    sp.low,
                    sp.volume,
                    sp.open,
                    ((sp.close - sp.open) / sp.open * 100) as daily_change_pct
                FROM stocks s
                INNER JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.symbol IN ('AAPL','MSFT','NVDA','META','NFLX','PYPL','INTC','CSCO','ADBE','QCOM')
                AND sp.date = (
                    SELECT MAX(date) FROM stock_prices WHERE stock_id = s.id
                )
                ORDER BY sp.close DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                symbol, name, sector, price, high, low, volume, open_price, daily_change_pct = row
                
                rankings.append({
                    "rank": i,
                    "symbol": symbol,
                    "name": name,
                    "sector": sector,
                    "current_price": float(price) if price else 0,
                    "high": float(high) if high else 0,
                    "low": float(low) if low else 0,
                    "open": float(open_price) if open_price else 0,
                    "volume": int(volume) if volume else 0,
                    "daily_change_percent": float(daily_change_pct) if daily_change_pct else 0,
                    "price_score": float(price) if price else 0,
                    "ranking_type": "price"
                })
            
            logger.info(f"Generated price ranking for {len(rankings)} stocks")
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating price ranking: {e}")
            return []
    
    async def get_comprehensive_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        综合排名 - 基于多维度加权算法
        """
        try:
            # 获取各项排名
            activity_ranking = await self.get_activity_ranking(limit)
            volatility_ranking = await self.get_volatility_ranking(limit)
            performance_ranking = await self.get_performance_ranking(limit)
            market_cap_ranking = await self.get_market_cap_ranking(limit)
            price_ranking = await self.get_price_ranking(limit)
            
            # 构建综合评分字典
            comprehensive_scores = {}
            
            # 权重配置（按你的优先级）
            weights = {
                "activity": 0.3,      # 优先级1: 30%
                "volatility": 0.25,   # 优先级2: 25%
                "performance": 0.2,   # 优先级3: 20%
                "market_cap": 0.15,   # 优先级4: 15%
                "price": 0.1          # 优先级5: 10%
            }
            
            # 收集所有股票的基础信息
            all_rankings = {
                "activity": {item["symbol"]: item for item in activity_ranking},
                "volatility": {item["symbol"]: item for item in volatility_ranking},
                "performance": {item["symbol"]: item for item in performance_ranking},
                "market_cap": {item["symbol"]: item for item in market_cap_ranking},
                "price": {item["symbol"]: item for item in price_ranking}
            }
            
            # 获取所有股票符号
            all_symbols = set()
            for ranking_data in all_rankings.values():
                all_symbols.update(ranking_data.keys())
            
            # 计算综合评分
            for symbol in all_symbols:
                base_info = None
                weighted_score = 0
                dimension_scores = {}
                
                for dimension, weight in weights.items():
                    if symbol in all_rankings[dimension]:
                        item = all_rankings[dimension][symbol]
                        if base_info is None:
                            base_info = item  # 保存基础信息
                        
                        # 计算标准化分数 (排名越高分数越高)
                        rank = item["rank"]
                        normalized_score = (limit - rank + 1) / limit * 100
                        dimension_scores[dimension] = normalized_score
                        weighted_score += normalized_score * weight
                    else:
                        dimension_scores[dimension] = 0
                
                if base_info:
                    comprehensive_scores[symbol] = {
                        **base_info,
                        "comprehensive_score": weighted_score,
                        "dimension_scores": dimension_scores,
                        "ranking_type": "comprehensive"
                    }
            
            # 按综合评分排序
            sorted_stocks = sorted(
                comprehensive_scores.values(),
                key=lambda x: x["comprehensive_score"],
                reverse=True
            )
            
            # 重新分配排名
            for i, stock in enumerate(sorted_stocks[:limit], 1):
                stock["rank"] = i
            
            logger.info(f"Generated comprehensive ranking for {len(sorted_stocks[:limit])} stocks")
            return sorted_stocks[:limit]
            
        except Exception as e:
            logger.error(f"Error generating comprehensive ranking: {e}")
            return []
    
    def _calculate_activity_score(self, volume: int, turnover: float) -> float:
        """计算活跃度评分"""
        if not volume:
            return 0
        # 成交量权重70%，成交额权重30%
        volume_score = min(volume / 100_000_000 * 70, 70)  # 1亿成交量得满分
        turnover_score = min(turnover / 50_000_000_000 * 30, 30)  # 500亿成交额得满分
        return volume_score + turnover_score
    
    def _calculate_volatility_score(self, volatility_pct: float, move_pct: float) -> float:
        """计算波动性评分"""
        if not volatility_pct:
            return 0
        # 日内振幅权重60%，价格变动权重40%
        range_score = min(volatility_pct * 10, 60)  # 6%振幅得满分
        move_score = min(abs(move_pct) * 10, 40)    # 4%变动得满分
        return range_score + move_score
    
    def _calculate_market_cap_score(self, market_cap: float) -> float:
        """计算市值评分"""
        if not market_cap:
            return 0
        # 市值越大评分越高，3万亿美元得满分
        return min(market_cap / 3_000_000_000_000 * 100, 100)