import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
from app.core.config import settings


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)


@pytest.fixture(scope="session")
def event_loop():
    """创建一个事件循环供整个测试会话使用"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
    
    # 清理：删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def superuser_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """创建超级用户并返回认证令牌"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # 创建超级用户
    superuser = User(
        email="test@admin.com",
        username="testadmin",
        hashed_password=get_password_hash("testpassword123!"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True
    )
    
    db_session.add(superuser)
    await db_session.commit()
    await db_session.refresh(superuser)
    
    # 登录获取令牌
    login_data = {
        "username": "testadmin",
        "password": "testpassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture
async def normal_user_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """创建普通用户并返回认证令牌"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # 创建普通用户
    user = User(
        email="test@user.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 登录获取令牌
    login_data = {
        "username": "testuser",
        "password": "testpassword123!"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture
async def sample_stock(db_session: AsyncSession):
    """创建示例股票数据"""
    from app.models.stock import Stock
    
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        is_active=True
    )
    
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)
    
    return stock