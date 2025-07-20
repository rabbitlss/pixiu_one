#!/usr/bin/env python3
"""
测试股票排名系统
展示基于真实数据的个性化排名功能
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.ranking_service import StockRankingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_ranking_system():
    """测试完整的排名系统"""
    
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
            ranking_service = StockRankingService(session)
            
            print("🏆" + "="*80)
            print("🏆 纳斯达克样本股票个性化排名系统")
            print("🏆" + "="*80)
            
            # 1. 活跃度排名 (优先级最高)
            print("\n📊 1. 活跃度排名 (基于成交量和成交额)")
            print("-" * 60)
            activity_ranking = await ranking_service.get_activity_ranking()
            
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'成交量(M)':<12} {'成交额(亿)':<12} {'活跃评分':<8}")
            print("-" * 60)
            for stock in activity_ranking:
                volume_m = stock['volume'] / 1_000_000
                turnover_b = stock['turnover'] / 100_000_000
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"{volume_m:.1f}M{'':<7} ${turnover_b:.1f}亿{'':<7} {stock['activity_score']:.1f}")
            
            # 2. 波动性排名
            print("\n🌊 2. 波动性排名 (基于日内振幅)")
            print("-" * 60)
            volatility_ranking = await ranking_service.get_volatility_ranking()
            
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'日内振幅':<10} {'振幅%':<8} {'波动评分':<8}")
            print("-" * 60)
            for stock in volatility_ranking:
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"${stock['daily_range']:.2f}{'':<4} {stock['volatility_percent']:.2f}%{'':<3} {stock['volatility_score']:.1f}")
            
            # 3. 涨跌排名
            print("\n📈 3. 涨跌排名 (基于当日表现)")
            print("-" * 60)
            performance_ranking = await ranking_service.get_performance_ranking()
            
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'涨跌幅':<8} {'涨跌额':<10} {'趋势':<4}")
            print("-" * 60)
            for stock in performance_ranking:
                change_display = f"{stock['percent_change']:+.2f}%"
                price_change_display = f"${stock['price_change']:+.2f}"
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"{change_display:<8} {price_change_display:<10} {stock['trend_emoji']}")
            
            # 4. 市值排名
            print("\n🏢 4. 市值排名 (基于公司市值)")
            print("-" * 60)
            market_cap_ranking = await ranking_service.get_market_cap_ranking()
            
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'市值(万亿)':<12} {'当前价格':<10}")
            print("-" * 60)
            for stock in market_cap_ranking:
                market_cap_t = stock['market_cap_billions'] / 1000
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"${market_cap_t:.2f}万亿{'':<6} ${stock['current_price']:.2f}")
            
            # 5. 价格排名
            print("\n💰 5. 价格排名 (基于股票价格)")
            print("-" * 60)
            price_ranking = await ranking_service.get_price_ranking()
            
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'当前价格':<10} {'日变幅':<8}")
            print("-" * 60)
            for stock in price_ranking:
                daily_change = f"{stock['daily_change_percent']:+.2f}%"
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"${stock['current_price']:.2f}{'':<4} {daily_change}")
            
            # 6. 综合排名 (基于加权算法)
            print("\n🎯 6. 综合排名 (多维度加权算法)")
            print("-" * 80)
            comprehensive_ranking = await ranking_service.get_comprehensive_ranking()
            
            print("权重配置: 活跃度30% + 波动性25% + 涨跌20% + 市值15% + 价格10%")
            print("-" * 80)
            print(f"{'排名':<4} {'代码':<6} {'公司名称':<20} {'综合评分':<10} {'活跃':<6} {'波动':<6} {'涨跌':<6} {'市值':<6}")
            print("-" * 80)
            for stock in comprehensive_ranking:
                scores = stock['dimension_scores']
                print(f"{stock['rank']:<4} {stock['symbol']:<6} {stock['name'][:17]:<20} "
                      f"{stock['comprehensive_score']:.1f}{'':<6} "
                      f"{scores.get('activity', 0):.0f}{'':<4} "
                      f"{scores.get('volatility', 0):.0f}{'':<4} "
                      f"{scores.get('performance', 0):.0f}{'':<4} "
                      f"{scores.get('market_cap', 0):.0f}")
            
            print("\n🎊 排名系统测试完成!")
            print("="*80)
            
            # 生成排名洞察
            await generate_ranking_insights(
                activity_ranking, volatility_ranking, performance_ranking,
                market_cap_ranking, price_ranking, comprehensive_ranking
            )
            
    except Exception as e:
        logger.error(f"排名系统测试失败: {e}")
        raise
    finally:
        await engine.dispose()


async def generate_ranking_insights(activity, volatility, performance, market_cap, price, comprehensive):
    """生成排名洞察分析"""
    
    print("\n💡 排名洞察分析")
    print("="*60)
    
    # 最活跃股票
    most_active = activity[0]
    print(f"📈 最活跃: {most_active['symbol']} ({most_active['name'][:20]})")
    print(f"   成交量: {most_active['volume']:,} 股")
    
    # 最波动股票
    most_volatile = volatility[0]
    print(f"🌊 最波动: {most_volatile['symbol']} ({most_volatile['name'][:20]})")
    print(f"   日内振幅: {most_volatile['volatility_percent']:.2f}%")
    
    # 最佳表现
    best_performer = performance[0]
    print(f"🏆 最佳表现: {best_performer['symbol']} ({best_performer['name'][:20]})")
    print(f"   涨跌幅: {best_performer['percent_change']:+.2f}%")
    
    # 最大市值
    largest_cap = market_cap[0]
    print(f"🏢 最大市值: {largest_cap['symbol']} ({largest_cap['name'][:20]})")
    print(f"   市值: ${largest_cap['market_cap_billions']/1000:.2f}万亿")
    
    # 最高价格
    highest_price = price[0]
    print(f"💰 最高价格: {highest_price['symbol']} ({highest_price['name'][:20]})")
    print(f"   股价: ${highest_price['current_price']:.2f}")
    
    # 综合冠军
    overall_winner = comprehensive[0]
    print(f"🎯 综合冠军: {overall_winner['symbol']} ({overall_winner['name'][:20]})")
    print(f"   综合评分: {overall_winner['comprehensive_score']:.1f}")
    
    print("\n📊 行业分布分析:")
    sector_count = {}
    for stock in comprehensive:
        sector = stock.get('sector', 'Unknown')
        sector_count[sector] = sector_count.get(sector, 0) + 1
    
    for sector, count in sorted(sector_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   {sector}: {count}只股票")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_ranking_system())