import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any
import json

from app.services.stock_data_service import StockDataService
from app.services.providers.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self):
        self.data_provider = YFinanceProvider()
        self.stock_data_service = StockDataService(self.data_provider)
        self.running = False
        self.tasks = {}
        
    async def start(self):
        """启动调度服务"""
        if self.running:
            logger.warning("Scheduler service is already running")
            return
        
        self.running = True
        logger.info("Starting scheduler service")
        
        # 启动各种定时任务
        self.tasks['daily_update'] = asyncio.create_task(self._daily_update_task())
        self.tasks['realtime_update'] = asyncio.create_task(self._realtime_update_task())
        self.tasks['technical_indicators'] = asyncio.create_task(self._technical_indicators_task())
        
        logger.info("All scheduler tasks started")
    
    async def stop(self):
        """停止调度服务"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping scheduler service")
        
        # 取消所有任务
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {task_name} cancelled")
        
        self.tasks.clear()
        logger.info("Scheduler service stopped")
    
    async def _daily_update_task(self):
        """每日数据更新任务"""
        logger.info("Daily update task started")
        
        while self.running:
            try:
                # 计算下次执行时间（每天凌晨2点）
                now = datetime.now()
                next_run = datetime.combine(now.date(), time(2, 0))
                
                # 如果当前时间已过凌晨2点，则调度到明天
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                # 等待到执行时间
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Daily update scheduled for {next_run}, waiting {wait_seconds:.0f} seconds")
                
                await asyncio.sleep(wait_seconds)
                
                if not self.running:
                    break
                
                # 执行每日更新
                logger.info("Starting daily stock data update")
                start_time = datetime.now()
                
                result = await self.stock_data_service.update_all_active_stocks(days=7)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(
                    f"Daily update completed in {duration:.1f}s. "
                    f"Results: {result['success']} success, {result['failed']} failed"
                )
                
                # 记录更新结果（可以保存到数据库或发送通知）
                await self._log_update_result("daily_update", result, duration)
                
            except asyncio.CancelledError:
                logger.info("Daily update task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in daily update task: {e}")
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)
    
    async def _realtime_update_task(self):
        """实时数据更新任务（市场开放时间）"""
        logger.info("Realtime update task started")
        
        while self.running:
            try:
                now = datetime.now()
                
                # 检查是否在交易时间内（这里简化为周一到周五的9:30-16:00）
                if (now.weekday() < 5 and  # 周一到周五
                    time(9, 30) <= now.time() <= time(16, 0)):  # 交易时间
                    
                    # 每5分钟更新一次实时数据
                    logger.debug("Fetching realtime quotes")
                    
                    # 这里可以实现获取热门股票的实时数据
                    # 为了避免过于复杂，这里只是记录日志
                    logger.debug("Realtime data update completed")
                    
                    await asyncio.sleep(300)  # 5分钟
                else:
                    # 非交易时间，每小时检查一次
                    await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                logger.info("Realtime update task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in realtime update task: {e}")
                await asyncio.sleep(300)  # 出错后5分钟重试
    
    async def _technical_indicators_task(self):
        """技术指标计算任务"""
        logger.info("Technical indicators task started")
        
        while self.running:
            try:
                # 每天下午6点计算技术指标
                now = datetime.now()
                next_run = datetime.combine(now.date(), time(18, 0))
                
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Technical indicators calculation scheduled for {next_run}")
                
                await asyncio.sleep(wait_seconds)
                
                if not self.running:
                    break
                
                # 这里可以实现技术指标的批量计算
                logger.info("Starting technical indicators calculation")
                
                # 示例：为所有活跃股票计算技术指标
                # 实际实现中需要获取股票列表并逐一计算
                logger.info("Technical indicators calculation completed")
                
            except asyncio.CancelledError:
                logger.info("Technical indicators task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in technical indicators task: {e}")
                await asyncio.sleep(3600)
    
    async def _log_update_result(self, task_type: str, result: Dict[str, Any], duration: float):
        """记录更新结果"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'task_type': task_type,
                'result': result,
                'duration_seconds': duration
            }
            
            # 这里可以保存到数据库或文件
            logger.info(f"Update result logged: {json.dumps(log_entry, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error logging update result: {e}")
    
    async def trigger_manual_update(self, stock_ids: Optional[list] = None, days: int = 30) -> Dict[str, Any]:
        """
        手动触发数据更新
        
        Args:
            stock_ids: 要更新的股票ID列表，None表示更新所有
            days: 更新的天数
            
        Returns:
            更新结果
        """
        try:
            logger.info(f"Manual update triggered for {len(stock_ids) if stock_ids else 'all'} stocks")
            start_time = datetime.now()
            
            if stock_ids:
                # 更新指定股票
                results = []
                for stock_id in stock_ids:
                    result = await self.stock_data_service.update_stock_data(stock_id, days)
                    results.append(result)
                
                success_count = sum(1 for r in results if r)
                result = {
                    'total': len(stock_ids),
                    'success': success_count,
                    'failed': len(stock_ids) - success_count
                }
            else:
                # 更新所有活跃股票
                result = await self.stock_data_service.update_all_active_stocks(days)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            await self._log_update_result("manual_update", result, duration)
            
            return {
                'success': True,
                'result': result,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"Error in manual update: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# 全局调度器实例
scheduler_service = SchedulerService()