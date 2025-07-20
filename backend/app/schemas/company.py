from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """公司基本信息基础模式"""
    company_name: str = Field(..., max_length=200, description="公司名称")
    legal_name: Optional[str] = Field(None, max_length=200, description="法定名称")
    ticker_symbol: str = Field(..., max_length=20, description="股票代码")
    exchange: Optional[str] = Field(None, max_length=50, description="交易所")
    country: Optional[str] = Field(None, max_length=100, description="国家")
    currency: Optional[str] = Field(None, max_length=10, description="货币")
    business_summary: Optional[str] = Field(None, description="业务概述")
    website: Optional[str] = Field(None, max_length=200, description="网站")
    industry: Optional[str] = Field(None, max_length=100, description="行业")
    sector: Optional[str] = Field(None, max_length=100, description="板块")
    full_time_employees: Optional[int] = Field(None, ge=0, description="全职员工数")
    address1: Optional[str] = Field(None, max_length=200, description="地址1")
    address2: Optional[str] = Field(None, max_length=200, description="地址2")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    state: Optional[str] = Field(None, max_length=100, description="州/省")
    zip_code: Optional[str] = Field(None, max_length=20, description="邮编")
    phone: Optional[str] = Field(None, max_length=50, description="电话")
    fax: Optional[str] = Field(None, max_length=50, description="传真")


class CompanyCreate(CompanyBase):
    """创建公司信息模式"""
    stock_id: int = Field(..., description="股票ID")


class CompanyUpdate(BaseModel):
    """更新公司信息模式"""
    company_name: Optional[str] = Field(None, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    business_summary: Optional[str] = None
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    full_time_employees: Optional[int] = Field(None, ge=0)
    address1: Optional[str] = Field(None, max_length=200)
    address2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    fax: Optional[str] = Field(None, max_length=50)


class Company(CompanyBase):
    """公司信息响应模式"""
    id: int
    stock_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FinancialMetricsBase(BaseModel):
    """财务指标基础模式"""
    report_date: datetime = Field(..., description="报告日期")
    period_type: str = Field(..., pattern="^(quarterly|annual)$", description="报告期类型")
    fiscal_year: int = Field(..., ge=1900, le=2100, description="财年")
    fiscal_quarter: Optional[int] = Field(None, ge=1, le=4, description="财季")
    
    # 收入指标
    revenue: Optional[float] = Field(None, description="总收入")
    gross_profit: Optional[float] = Field(None, description="毛利润")
    operating_income: Optional[float] = Field(None, description="营业收入")
    net_income: Optional[float] = Field(None, description="净利润")
    ebitda: Optional[float] = Field(None, description="EBITDA")
    
    # 每股指标
    earnings_per_share: Optional[float] = Field(None, description="每股收益")
    diluted_eps: Optional[float] = Field(None, description="稀释每股收益")
    book_value_per_share: Optional[float] = Field(None, description="每股账面价值")
    
    # 资产负债表指标
    total_assets: Optional[float] = Field(None, description="总资产")
    total_liabilities: Optional[float] = Field(None, description="总负债")
    shareholders_equity: Optional[float] = Field(None, description="股东权益")
    total_debt: Optional[float] = Field(None, description="总债务")
    cash_and_equivalents: Optional[float] = Field(None, description="现金及现金等价物")
    
    # 现金流指标
    operating_cash_flow: Optional[float] = Field(None, description="经营活动现金流")
    free_cash_flow: Optional[float] = Field(None, description="自由现金流")
    capital_expenditures: Optional[float] = Field(None, description="资本支出")
    
    # 比率指标
    return_on_equity: Optional[float] = Field(None, description="股本回报率")
    return_on_assets: Optional[float] = Field(None, description="资产回报率")
    debt_to_equity: Optional[float] = Field(None, description="债务股权比")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    
    # 估值指标
    price_to_earnings: Optional[float] = Field(None, description="市盈率")
    price_to_book: Optional[float] = Field(None, description="市净率")
    price_to_sales: Optional[float] = Field(None, description="市销率")
    enterprise_value: Optional[float] = Field(None, description="企业价值")
    ev_to_revenue: Optional[float] = Field(None, description="企业价值/收入")
    ev_to_ebitda: Optional[float] = Field(None, description="企业价值/EBITDA")
    
    # 增长指标
    revenue_growth: Optional[float] = Field(None, description="收入增长率")
    earnings_growth: Optional[float] = Field(None, description="利润增长率")


class FinancialMetricsCreate(FinancialMetricsBase):
    """创建财务指标模式"""
    company_id: int = Field(..., description="公司ID")


class FinancialMetrics(FinancialMetricsBase):
    """财务指标响应模式"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarketPositionBase(BaseModel):
    """市场地位基础模式"""
    analysis_date: datetime = Field(..., description="分析日期")
    
    # 市场占有率
    market_cap: Optional[float] = Field(None, description="市值")
    market_cap_rank_global: Optional[int] = Field(None, ge=1, description="全球市值排名")
    market_cap_rank_sector: Optional[int] = Field(None, ge=1, description="行业市值排名")
    market_share_percentage: Optional[float] = Field(None, ge=0, le=100, description="市场份额百分比")
    
    # 行业地位
    industry_rank: Optional[int] = Field(None, ge=1, description="行业排名")
    sector_rank: Optional[int] = Field(None, ge=1, description="板块排名")
    revenue_rank_industry: Optional[int] = Field(None, ge=1, description="行业收入排名")
    profit_rank_industry: Optional[int] = Field(None, ge=1, description="行业利润排名")
    
    # 竞争对手分析
    main_competitors: Optional[List[str]] = Field(None, description="主要竞争对手")
    competitive_advantages: Optional[str] = Field(None, description="竞争优势")
    market_barriers: Optional[str] = Field(None, description="市场壁垒")
    
    # 地理分布
    geographic_segments: Optional[Dict[str, float]] = Field(None, description="地理收入分布")
    international_exposure: Optional[float] = Field(None, ge=0, le=100, description="国际业务暴露度")
    
    # 产品/服务组合
    product_segments: Optional[Dict[str, float]] = Field(None, description="产品线收入分布")
    revenue_diversification_score: Optional[float] = Field(None, ge=0, le=100, description="收入多元化评分")
    
    # 创新能力
    rd_spending: Optional[float] = Field(None, description="研发支出")
    rd_intensity: Optional[float] = Field(None, ge=0, le=100, description="研发强度")
    patent_count: Optional[int] = Field(None, ge=0, description="专利数量")


class MarketPositionCreate(MarketPositionBase):
    """创建市场地位模式"""
    company_id: int = Field(..., description="公司ID")


class MarketPosition(MarketPositionBase):
    """市场地位响应模式"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CorporateActionBase(BaseModel):
    """公司行为基础模式"""
    action_type: str = Field(..., description="行为类型")
    announcement_date: Optional[datetime] = Field(None, description="公告日期")
    ex_date: Optional[datetime] = Field(None, description="除权日")
    record_date: Optional[datetime] = Field(None, description="登记日")
    payment_date: Optional[datetime] = Field(None, description="支付日期")
    
    # 分红相关
    dividend_amount: Optional[float] = Field(None, description="分红金额")
    dividend_yield: Optional[float] = Field(None, description="分红收益率")
    dividend_frequency: Optional[str] = Field(None, description="分红频率")
    
    # 股票分拆相关
    split_ratio: Optional[str] = Field(None, description="分拆比例")
    split_factor: Optional[float] = Field(None, description="分拆因子")
    
    # 其他信息
    description: Optional[str] = Field(None, description="描述")
    currency: Optional[str] = Field(None, max_length=10, description="货币")


class CorporateActionCreate(CorporateActionBase):
    """创建公司行为模式"""
    company_id: int = Field(..., description="公司ID")


class CorporateAction(CorporateActionBase):
    """公司行为响应模式"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ESGMetricsBase(BaseModel):
    """ESG指标基础模式"""
    assessment_date: datetime = Field(..., description="评估日期")
    
    # 总体ESG评分
    esg_score_total: Optional[float] = Field(None, ge=0, le=100, description="总ESG评分")
    esg_score_environment: Optional[float] = Field(None, ge=0, le=100, description="环境评分")
    esg_score_social: Optional[float] = Field(None, ge=0, le=100, description="社会评分")
    esg_score_governance: Optional[float] = Field(None, ge=0, le=100, description="治理评分")
    
    # 环境指标
    carbon_footprint: Optional[float] = Field(None, description="碳足迹")
    renewable_energy_usage: Optional[float] = Field(None, ge=0, le=100, description="可再生能源使用率")
    waste_reduction: Optional[float] = Field(None, description="废物减少率")
    water_usage_efficiency: Optional[float] = Field(None, description="水资源使用效率")
    
    # 社会指标
    employee_satisfaction: Optional[float] = Field(None, ge=0, le=100, description="员工满意度")
    diversity_score: Optional[float] = Field(None, ge=0, le=100, description="多样性评分")
    community_investment: Optional[float] = Field(None, description="社区投资")
    safety_incidents: Optional[int] = Field(None, ge=0, description="安全事故数量")
    
    # 治理指标
    board_independence: Optional[float] = Field(None, ge=0, le=100, description="董事会独立性")
    executive_compensation_ratio: Optional[float] = Field(None, description="高管薪酬比")
    audit_quality_score: Optional[float] = Field(None, ge=0, le=100, description="审计质量评分")
    transparency_score: Optional[float] = Field(None, ge=0, le=100, description="透明度评分")
    
    # 评级机构信息
    rating_agency: Optional[str] = Field(None, max_length=100, description="评级机构")
    rating_methodology: Optional[str] = Field(None, max_length=100, description="评级方法")


class ESGMetricsCreate(ESGMetricsBase):
    """创建ESG指标模式"""
    company_id: int = Field(..., description="公司ID")


class ESGMetrics(ESGMetricsBase):
    """ESG指标响应模式"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalystRatingBase(BaseModel):
    """分析师评级基础模式"""
    rating_date: datetime = Field(..., description="评级日期")
    analyst_firm: Optional[str] = Field(None, max_length=100, description="分析师公司")
    analyst_name: Optional[str] = Field(None, max_length=100, description="分析师姓名")
    
    # 评级和目标价
    rating: Optional[str] = Field(None, max_length=20, description="评级")
    target_price: Optional[float] = Field(None, description="目标价")
    current_price: Optional[float] = Field(None, description="当前价")
    previous_rating: Optional[str] = Field(None, max_length=20, description="之前评级")
    previous_target_price: Optional[float] = Field(None, description="之前目标价")
    
    # 预测
    revenue_estimate: Optional[float] = Field(None, description="收入预测")
    earnings_estimate: Optional[float] = Field(None, description="利润预测")
    eps_estimate: Optional[float] = Field(None, description="每股收益预测")
    
    # 预测期间
    forecast_period: Optional[str] = Field(None, max_length=20, description="预测期间")
    fiscal_year: Optional[int] = Field(None, ge=1900, le=2100, description="财年")
    
    # 评级理由
    rating_rationale: Optional[str] = Field(None, description="评级理由")
    key_points: Optional[List[str]] = Field(None, description="关键要点")
    
    # 风险因素
    upside_risks: Optional[List[str]] = Field(None, description="上行风险")
    downside_risks: Optional[List[str]] = Field(None, description="下行风险")


class AnalystRatingCreate(AnalystRatingBase):
    """创建分析师评级模式"""
    company_id: int = Field(..., description="公司ID")


class AnalystRating(AnalystRatingBase):
    """分析师评级响应模式"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyDetailResponse(Company):
    """公司详细信息响应模式"""
    latest_financial_metrics: Optional[FinancialMetrics] = None
    latest_market_position: Optional[MarketPosition] = None
    recent_corporate_actions: List[CorporateAction] = []
    latest_esg_metrics: Optional[ESGMetrics] = None
    recent_analyst_ratings: List[AnalystRating] = []


class CompanySearchResponse(BaseModel):
    """公司搜索响应模式"""
    items: List[Company]
    total: int
    page: int
    size: int
    pages: int