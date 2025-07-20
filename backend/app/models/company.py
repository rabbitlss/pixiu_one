from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Company(Base):
    """公司基本信息表"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, unique=True)
    
    # 基本信息
    company_name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    ticker_symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    country = Column(String(100))
    currency = Column(String(10))
    
    # 公司描述和业务
    business_summary = Column(Text)
    website = Column(String(200))
    industry = Column(String(100))
    sector = Column(String(100))
    full_time_employees = Column(Integer)
    
    # 地址信息
    address1 = Column(String(200))
    address2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    phone = Column(String(50))
    fax = Column(String(50))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    stock = relationship("Stock", backref="company")
    financial_metrics = relationship("FinancialMetrics", back_populates="company", cascade="all, delete-orphan")
    market_position = relationship("MarketPosition", back_populates="company", cascade="all, delete-orphan")
    corporate_actions = relationship("CorporateAction", back_populates="company", cascade="all, delete-orphan")
    esg_metrics = relationship("ESGMetrics", back_populates="company", cascade="all, delete-orphan")


class FinancialMetrics(Base):
    """财务指标表"""
    __tablename__ = "financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    report_date = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # quarterly, annual
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer)  # 1-4 for quarterly reports
    
    # 收入指标
    revenue = Column(Float)  # 总收入
    gross_profit = Column(Float)  # 毛利润
    operating_income = Column(Float)  # 营业收入
    net_income = Column(Float)  # 净利润
    ebitda = Column(Float)  # 息税折旧摊销前利润
    
    # 每股指标
    earnings_per_share = Column(Float)  # 每股收益
    diluted_eps = Column(Float)  # 稀释每股收益
    book_value_per_share = Column(Float)  # 每股账面价值
    
    # 资产负债表指标
    total_assets = Column(Float)  # 总资产
    total_liabilities = Column(Float)  # 总负债
    shareholders_equity = Column(Float)  # 股东权益
    total_debt = Column(Float)  # 总债务
    cash_and_equivalents = Column(Float)  # 现金及现金等价物
    
    # 现金流指标
    operating_cash_flow = Column(Float)  # 经营活动现金流
    free_cash_flow = Column(Float)  # 自由现金流
    capital_expenditures = Column(Float)  # 资本支出
    
    # 比率指标
    return_on_equity = Column(Float)  # 股本回报率
    return_on_assets = Column(Float)  # 资产回报率
    debt_to_equity = Column(Float)  # 债务股权比
    current_ratio = Column(Float)  # 流动比率
    quick_ratio = Column(Float)  # 速动比率
    
    # 估值指标
    price_to_earnings = Column(Float)  # 市盈率
    price_to_book = Column(Float)  # 市净率
    price_to_sales = Column(Float)  # 市销率
    enterprise_value = Column(Float)  # 企业价值
    ev_to_revenue = Column(Float)  # 企业价值/收入
    ev_to_ebitda = Column(Float)  # 企业价值/EBITDA
    
    # 增长指标
    revenue_growth = Column(Float)  # 收入增长率
    earnings_growth = Column(Float)  # 利润增长率
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    company = relationship("Company", back_populates="financial_metrics")
    
    # 索引
    __table_args__ = (
        Index("idx_company_report_date", "company_id", "report_date", "period_type"),
    )


class MarketPosition(Base):
    """市场地位和占有率表"""
    __tablename__ = "market_position"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    analysis_date = Column(DateTime(timezone=True), nullable=False)
    
    # 市场占有率
    market_cap = Column(Float)  # 市值
    market_cap_rank_global = Column(Integer)  # 全球市值排名
    market_cap_rank_sector = Column(Integer)  # 行业市值排名
    market_share_percentage = Column(Float)  # 市场份额百分比
    
    # 行业地位
    industry_rank = Column(Integer)  # 行业排名
    sector_rank = Column(Integer)  # 板块排名
    revenue_rank_industry = Column(Integer)  # 行业收入排名
    profit_rank_industry = Column(Integer)  # 行业利润排名
    
    # 竞争对手分析
    main_competitors = Column(JSON)  # 主要竞争对手列表
    competitive_advantages = Column(Text)  # 竞争优势
    market_barriers = Column(Text)  # 市场壁垒
    
    # 地理分布
    geographic_segments = Column(JSON)  # 地理收入分布
    international_exposure = Column(Float)  # 国际业务暴露度
    
    # 产品/服务组合
    product_segments = Column(JSON)  # 产品线收入分布
    revenue_diversification_score = Column(Float)  # 收入多元化评分
    
    # 创新能力
    rd_spending = Column(Float)  # 研发支出
    rd_intensity = Column(Float)  # 研发强度（研发支出/收入）
    patent_count = Column(Integer)  # 专利数量
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    company = relationship("Company", back_populates="market_position")
    
    # 索引
    __table_args__ = (
        Index("idx_company_analysis_date", "company_id", "analysis_date"),
    )


class CorporateAction(Base):
    """公司行为表（分红、股票分拆等）"""
    __tablename__ = "corporate_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    action_type = Column(String(50), nullable=False)  # dividend, split, spinoff, merger, etc.
    announcement_date = Column(DateTime(timezone=True))
    ex_date = Column(DateTime(timezone=True))
    record_date = Column(DateTime(timezone=True))
    payment_date = Column(DateTime(timezone=True))
    
    # 分红相关
    dividend_amount = Column(Float)  # 分红金额
    dividend_yield = Column(Float)  # 分红收益率
    dividend_frequency = Column(String(20))  # quarterly, annual, etc.
    
    # 股票分拆相关
    split_ratio = Column(String(20))  # 分拆比例，如 "2:1"
    split_factor = Column(Float)  # 分拆因子
    
    # 其他信息
    description = Column(Text)
    currency = Column(String(10))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    company = relationship("Company", back_populates="corporate_actions")
    
    # 索引
    __table_args__ = (
        Index("idx_company_action_date", "company_id", "ex_date", "action_type"),
    )


class ESGMetrics(Base):
    """ESG（环境、社会、治理）指标表"""
    __tablename__ = "esg_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    assessment_date = Column(DateTime(timezone=True), nullable=False)
    
    # 总体ESG评分
    esg_score_total = Column(Float)  # 总ESG评分
    esg_score_environment = Column(Float)  # 环境评分
    esg_score_social = Column(Float)  # 社会评分
    esg_score_governance = Column(Float)  # 治理评分
    
    # 环境指标
    carbon_footprint = Column(Float)  # 碳足迹
    renewable_energy_usage = Column(Float)  # 可再生能源使用率
    waste_reduction = Column(Float)  # 废物减少率
    water_usage_efficiency = Column(Float)  # 水资源使用效率
    
    # 社会指标
    employee_satisfaction = Column(Float)  # 员工满意度
    diversity_score = Column(Float)  # 多样性评分
    community_investment = Column(Float)  # 社区投资
    safety_incidents = Column(Integer)  # 安全事故数量
    
    # 治理指标
    board_independence = Column(Float)  # 董事会独立性
    executive_compensation_ratio = Column(Float)  # 高管薪酬比
    audit_quality_score = Column(Float)  # 审计质量评分
    transparency_score = Column(Float)  # 透明度评分
    
    # 评级机构信息
    rating_agency = Column(String(100))  # 评级机构
    rating_methodology = Column(String(100))  # 评级方法
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    company = relationship("Company", back_populates="esg_metrics")
    
    # 索引
    __table_args__ = (
        Index("idx_company_assessment_date", "company_id", "assessment_date"),
    )


class AnalystRating(Base):
    """分析师评级表"""
    __tablename__ = "analyst_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # 评级信息
    rating_date = Column(DateTime(timezone=True), nullable=False)
    analyst_firm = Column(String(100))
    analyst_name = Column(String(100))
    
    # 评级和目标价
    rating = Column(String(20))  # Buy, Hold, Sell, Strong Buy, Strong Sell
    target_price = Column(Float)
    current_price = Column(Float)
    previous_rating = Column(String(20))
    previous_target_price = Column(Float)
    
    # 预测
    revenue_estimate = Column(Float)  # 收入预测
    earnings_estimate = Column(Float)  # 利润预测
    eps_estimate = Column(Float)  # 每股收益预测
    
    # 预测期间
    forecast_period = Column(String(20))  # current_year, next_year, etc.
    fiscal_year = Column(Integer)
    
    # 评级理由
    rating_rationale = Column(Text)
    key_points = Column(JSON)  # 关键要点列表
    
    # 风险因素
    upside_risks = Column(JSON)  # 上行风险
    downside_risks = Column(JSON)  # 下行风险
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index("idx_company_rating_date", "company_id", "rating_date"),
    )