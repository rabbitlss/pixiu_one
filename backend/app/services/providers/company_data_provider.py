import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.models import Company, Stock, FinancialMetrics, MarketPosition, CorporateAction, ESGMetrics

logger = logging.getLogger(__name__)


class CompanyDataProvider:
    """公司数据提供者 - 从Alpha Vantage获取公司基本信息和财务数据"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.session: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """发起API请求"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        params["apikey"] = self.api_key
        
        try:
            response = await self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 检查API错误
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API Error: {data['Error Message']}")
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage API Note: {data['Note']}")
                # API限制，等待后重试
                await asyncio.sleep(12)  # Alpha Vantage免费版限制
                response = await self.session.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    async def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """获取公司概览信息"""
        params = {
            "function": "OVERVIEW",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        return data
    
    async def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """获取损益表"""
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        return data
    
    async def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """获取资产负债表"""
        params = {
            "function": "BALANCE_SHEET",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        return data
    
    async def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """获取现金流量表"""
        params = {
            "function": "CASH_FLOW",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        return data
    
    async def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """获取收益数据"""
        params = {
            "function": "EARNINGS",
            "symbol": symbol
        }
        
        data = await self._make_request(params)
        return data
    
    def _parse_company_overview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析公司概览数据"""
        if not data or "Symbol" not in data:
            return {}
        
        def safe_float(value: str) -> Optional[float]:
            try:
                if value == "None" or value == "-" or not value:
                    return None
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value: str) -> Optional[int]:
            try:
                if value == "None" or value == "-" or not value:
                    return None
                return int(value)
            except (ValueError, TypeError):
                return None
        
        return {
            "ticker_symbol": data.get("Symbol", ""),
            "company_name": data.get("Name", ""),
            "business_summary": data.get("Description", ""),
            "exchange": data.get("Exchange", ""),
            "currency": data.get("Currency", ""),
            "country": data.get("Country", ""),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "address1": data.get("Address", ""),
            "full_time_employees": safe_int(data.get("FullTimeEmployees")),
            
            # 财务指标
            "market_cap": safe_float(data.get("MarketCapitalization")),
            "pe_ratio": safe_float(data.get("PERatio")),
            "peg_ratio": safe_float(data.get("PEGRatio")),
            "price_to_book": safe_float(data.get("PriceToBookRatio")),
            "price_to_sales": safe_float(data.get("PriceToSalesRatioTTM")),
            "dividend_yield": safe_float(data.get("DividendYield")),
            "eps": safe_float(data.get("EPS")),
            "revenue_ttm": safe_float(data.get("RevenueTTM")),
            "gross_profit_ttm": safe_float(data.get("GrossProfitTTM")),
            "ebitda": safe_float(data.get("EBITDA")),
            "profit_margin": safe_float(data.get("ProfitMargin")),
            "operating_margin": safe_float(data.get("OperatingMarginTTM")),
            "return_on_assets": safe_float(data.get("ReturnOnAssetsTTM")),
            "return_on_equity": safe_float(data.get("ReturnOnEquityTTM")),
            "revenue_growth": safe_float(data.get("QuarterlyRevenueGrowthYOY")),
            "earnings_growth": safe_float(data.get("QuarterlyEarningsGrowthYOY")),
            "analyst_target_price": safe_float(data.get("AnalystTargetPrice")),
            "week_52_high": safe_float(data.get("52WeekHigh")),
            "week_52_low": safe_float(data.get("52WeekLow")),
            "beta": safe_float(data.get("Beta"))
        }
    
    def _parse_financial_statement(self, data: Dict[str, Any], statement_type: str) -> List[Dict[str, Any]]:
        """解析财务报表数据"""
        financial_data = []
        
        # 获取年报和季报数据
        for report_type in ["annualReports", "quarterlyReports"]:
            if report_type not in data:
                continue
                
            period_type = "annual" if report_type == "annualReports" else "quarterly"
            
            for report in data[report_type]:
                fiscal_date = report.get("fiscalDateEnding")
                if not fiscal_date:
                    continue
                
                try:
                    report_date = datetime.strptime(fiscal_date, "%Y-%m-%d")
                    fiscal_year = report_date.year
                    fiscal_quarter = None
                    
                    if period_type == "quarterly":
                        # 计算季度
                        month = report_date.month
                        if month <= 3:
                            fiscal_quarter = 1
                        elif month <= 6:
                            fiscal_quarter = 2
                        elif month <= 9:
                            fiscal_quarter = 3
                        else:
                            fiscal_quarter = 4
                    
                    def safe_float(value: str) -> Optional[float]:
                        try:
                            if value == "None" or value == "-" or not value:
                                return None
                            return float(value)
                        except (ValueError, TypeError):
                            return None
                    
                    # 解析不同类型的财务报表
                    parsed_data = {
                        "report_date": report_date,
                        "period_type": period_type,
                        "fiscal_year": fiscal_year,
                        "fiscal_quarter": fiscal_quarter
                    }
                    
                    if statement_type == "income":
                        parsed_data.update({
                            "revenue": safe_float(report.get("totalRevenue")),
                            "gross_profit": safe_float(report.get("grossProfit")),
                            "operating_income": safe_float(report.get("operatingIncome")),
                            "net_income": safe_float(report.get("netIncome")),
                            "ebitda": safe_float(report.get("ebitda")),
                            "earnings_per_share": safe_float(report.get("reportedEPS"))
                        })
                    elif statement_type == "balance":
                        parsed_data.update({
                            "total_assets": safe_float(report.get("totalAssets")),
                            "total_liabilities": safe_float(report.get("totalLiabilities")),
                            "shareholders_equity": safe_float(report.get("totalShareholderEquity")),
                            "total_debt": safe_float(report.get("totalDebt")),
                            "cash_and_equivalents": safe_float(report.get("cashAndCashEquivalentsAtCarryingValue"))
                        })
                    elif statement_type == "cash_flow":
                        parsed_data.update({
                            "operating_cash_flow": safe_float(report.get("operatingCashflow")),
                            "capital_expenditures": safe_float(report.get("capitalExpenditures")),
                        })
                        
                        # 计算自由现金流
                        ocf = parsed_data.get("operating_cash_flow")
                        capex = parsed_data.get("capital_expenditures")
                        if ocf is not None and capex is not None:
                            parsed_data["free_cash_flow"] = ocf - abs(capex)
                    
                    financial_data.append(parsed_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse financial data: {e}")
                    continue
        
        return financial_data
    
    async def collect_company_data(self, symbol: str, db: AsyncSession) -> Dict[str, Any]:
        """采集公司完整数据"""
        try:
            logger.info(f"开始采集公司数据: {symbol}")
            
            # 查找股票记录
            stock_query = select(Stock).where(Stock.symbol == symbol)
            stock_result = await db.execute(stock_query)
            stock = stock_result.scalar_one_or_none()
            
            if not stock:
                logger.error(f"未找到股票: {symbol}")
                return {"error": f"Stock {symbol} not found"}
            
            # 获取公司概览
            overview_data = await self.get_company_overview(symbol)
            company_info = self._parse_company_overview(overview_data)
            
            if not company_info:
                logger.error(f"无法获取公司概览数据: {symbol}")
                return {"error": f"Failed to get company overview for {symbol}"}
            
            # 检查是否已存在公司记录
            company_query = select(Company).where(Company.stock_id == stock.id)
            company_result = await db.execute(company_query)
            company = company_result.scalar_one_or_none()
            
            if not company:
                # 创建公司记录
                company = Company(
                    stock_id=stock.id,
                    company_name=company_info.get("company_name", ""),
                    ticker_symbol=company_info.get("ticker_symbol", symbol),
                    exchange=company_info.get("exchange", ""),
                    country=company_info.get("country", ""),
                    currency=company_info.get("currency", ""),
                    business_summary=company_info.get("business_summary", ""),
                    industry=company_info.get("industry", ""),
                    sector=company_info.get("sector", ""),
                    full_time_employees=company_info.get("full_time_employees"),
                    address1=company_info.get("address1", "")
                )
                db.add(company)
                await db.commit()
                await db.refresh(company)
                logger.info(f"创建公司记录: {company.company_name}")
            else:
                # 更新公司信息
                for key, value in company_info.items():
                    if hasattr(company, key) and value is not None:
                        setattr(company, key, value)
                await db.commit()
                logger.info(f"更新公司记录: {company.company_name}")
            
            # 获取财务报表数据
            collected_data = {"company": company_info}
            
            try:
                # 损益表
                income_data = await self.get_income_statement(symbol)
                await asyncio.sleep(1)  # API限制
                
                # 资产负债表
                balance_data = await self.get_balance_sheet(symbol)
                await asyncio.sleep(1)
                
                # 现金流量表
                cash_flow_data = await self.get_cash_flow(symbol)
                await asyncio.sleep(1)
                
                # 解析财务数据
                income_statements = self._parse_financial_statement(income_data, "income")
                balance_sheets = self._parse_financial_statement(balance_data, "balance")
                cash_flows = self._parse_financial_statement(cash_flow_data, "cash_flow")
                
                # 合并财务数据
                financial_metrics = self._merge_financial_data(
                    income_statements, balance_sheets, cash_flows, company_info
                )
                
                # 保存财务指标
                for metrics in financial_metrics:
                    await self._save_financial_metrics(db, company.id, metrics)
                
                collected_data.update({
                    "financial_metrics_count": len(financial_metrics),
                    "income_statements": len(income_statements),
                    "balance_sheets": len(balance_sheets),
                    "cash_flows": len(cash_flows)
                })
                
            except Exception as e:
                logger.error(f"获取财务数据失败: {e}")
                collected_data["financial_error"] = str(e)
            
            # 创建市场地位记录
            try:
                market_position = MarketPosition(
                    company_id=company.id,
                    analysis_date=datetime.now(),
                    market_cap=company_info.get("market_cap"),
                    revenue_diversification_score=self._calculate_diversification_score(company_info),
                    rd_intensity=company_info.get("rd_intensity")
                )
                db.add(market_position)
                await db.commit()
                collected_data["market_position"] = True
            except Exception as e:
                logger.error(f"创建市场地位记录失败: {e}")
                collected_data["market_position_error"] = str(e)
            
            logger.info(f"公司数据采集完成: {symbol}")
            return collected_data
            
        except Exception as e:
            logger.error(f"采集公司数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def _merge_financial_data(
        self, 
        income_statements: List[Dict[str, Any]], 
        balance_sheets: List[Dict[str, Any]], 
        cash_flows: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """合并财务数据"""
        merged_data = {}
        
        # 按日期和期间类型合并数据
        for statement in income_statements + balance_sheets + cash_flows:
            key = (
                statement["report_date"].strftime("%Y-%m-%d"),
                statement["period_type"],
                statement.get("fiscal_quarter")
            )
            
            if key not in merged_data:
                merged_data[key] = {
                    "report_date": statement["report_date"],
                    "period_type": statement["period_type"],
                    "fiscal_year": statement["fiscal_year"],
                    "fiscal_quarter": statement.get("fiscal_quarter")
                }
            
            merged_data[key].update(statement)
        
        # 计算额外的比率指标
        for data in merged_data.values():
            self._calculate_financial_ratios(data, company_info)
        
        return list(merged_data.values())
    
    def _calculate_financial_ratios(self, data: Dict[str, Any], company_info: Dict[str, Any]):
        """计算财务比率"""
        try:
            # ROE = 净利润 / 股东权益
            if data.get("net_income") and data.get("shareholders_equity"):
                data["return_on_equity"] = data["net_income"] / data["shareholders_equity"] * 100
            elif company_info.get("return_on_equity"):
                data["return_on_equity"] = company_info["return_on_equity"]
            
            # ROA = 净利润 / 总资产
            if data.get("net_income") and data.get("total_assets"):
                data["return_on_assets"] = data["net_income"] / data["total_assets"] * 100
            elif company_info.get("return_on_assets"):
                data["return_on_assets"] = company_info["return_on_assets"]
            
            # 债务股权比 = 总债务 / 股东权益
            if data.get("total_debt") and data.get("shareholders_equity"):
                data["debt_to_equity"] = data["total_debt"] / data["shareholders_equity"]
            
            # 从公司概览获取估值指标
            data["price_to_earnings"] = company_info.get("pe_ratio")
            data["price_to_book"] = company_info.get("price_to_book")
            data["price_to_sales"] = company_info.get("price_to_sales")
            
            # 增长率
            data["revenue_growth"] = company_info.get("revenue_growth")
            data["earnings_growth"] = company_info.get("earnings_growth")
            
        except Exception as e:
            logger.warning(f"计算财务比率失败: {e}")
    
    def _calculate_diversification_score(self, company_info: Dict[str, Any]) -> Optional[float]:
        """计算收入多元化评分（简化版）"""
        try:
            # 基于行业和业务描述的简单评分
            score = 50.0  # 基础分数
            
            # 如果有详细的业务描述，提高评分
            if company_info.get("business_summary") and len(company_info["business_summary"]) > 100:
                score += 20.0
            
            # 基于行业类型调整
            sector = company_info.get("sector", "").lower()
            if "technology" in sector:
                score += 15.0
            elif "healthcare" in sector:
                score += 10.0
            
            return min(score, 100.0)
        except:
            return None
    
    async def _save_financial_metrics(self, db: AsyncSession, company_id: int, metrics: Dict[str, Any]):
        """保存财务指标"""
        try:
            # 检查是否已存在
            existing_query = select(FinancialMetrics).where(
                FinancialMetrics.company_id == company_id,
                FinancialMetrics.fiscal_year == metrics["fiscal_year"],
                FinancialMetrics.period_type == metrics["period_type"],
                FinancialMetrics.fiscal_quarter == metrics.get("fiscal_quarter")
            )
            existing_result = await db.execute(existing_query)
            existing_metrics = existing_result.scalar_one_or_none()
            
            if existing_metrics:
                # 更新现有记录
                for key, value in metrics.items():
                    if hasattr(existing_metrics, key) and value is not None:
                        setattr(existing_metrics, key, value)
            else:
                # 创建新记录
                financial_metrics = FinancialMetrics(
                    company_id=company_id,
                    **metrics
                )
                db.add(financial_metrics)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"保存财务指标失败: {e}")
            await db.rollback()
    
    async def collect_batch_company_data(self, symbols: List[str], db: AsyncSession) -> Dict[str, Any]:
        """批量采集公司数据"""
        results = {}
        
        for symbol in symbols:
            try:
                result = await self.collect_company_data(symbol, db)
                results[symbol] = result
                
                # API限制延迟
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"批量采集失败 {symbol}: {e}")
                results[symbol] = {"error": str(e)}
        
        return results