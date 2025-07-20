import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestStocks:
    """股票相关测试"""
    
    async def test_list_stocks(self, client: AsyncClient, normal_user_token: str, sample_stock):
        """测试获取股票列表"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        response = await client.get("/api/v1/stocks", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
        
        # 检查示例股票是否在列表中
        stock_symbols = [stock["symbol"] for stock in data["items"]]
        assert "AAPL" in stock_symbols
    
    async def test_get_stock_detail(self, client: AsyncClient, normal_user_token: str, sample_stock):
        """测试获取股票详情"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        response = await client.get(f"/api/v1/stocks/{sample_stock.id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_stock.id
        assert data["symbol"] == sample_stock.symbol
        assert data["name"] == sample_stock.name
    
    async def test_get_nonexistent_stock(self, client: AsyncClient, normal_user_token: str):
        """测试获取不存在的股票"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        response = await client.get("/api/v1/stocks/99999", headers=headers)
        assert response.status_code == 404
    
    async def test_create_stock_as_superuser(self, client: AsyncClient, superuser_token: str):
        """测试超级用户创建股票"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        stock_data = {
            "symbol": "TSLA",
            "name": "Tesla, Inc.",
            "exchange": "NASDAQ",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers"
        }
        
        response = await client.post("/api/v1/stocks", json=stock_data, headers=headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["symbol"] == stock_data["symbol"]
        assert data["name"] == stock_data["name"]
        assert data["is_active"] is True
    
    async def test_create_stock_as_normal_user(self, client: AsyncClient, normal_user_token: str):
        """测试普通用户创建股票（应该被拒绝）"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        stock_data = {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Software"
        }
        
        response = await client.post("/api/v1/stocks", json=stock_data, headers=headers)
        assert response.status_code == 403
    
    async def test_create_duplicate_stock(self, client: AsyncClient, superuser_token: str, sample_stock):
        """测试创建重复股票"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        stock_data = {
            "symbol": sample_stock.symbol,  # 使用已存在的股票代码
            "name": "Duplicate Stock",
            "exchange": "NASDAQ"
        }
        
        response = await client.post("/api/v1/stocks", json=stock_data, headers=headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_update_stock(self, client: AsyncClient, superuser_token: str, sample_stock):
        """测试更新股票信息"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        update_data = {
            "name": "Apple Inc. (Updated)",
            "market_cap": 3000000000000
        }
        
        response = await client.put(
            f"/api/v1/stocks/{sample_stock.id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["market_cap"] == update_data["market_cap"]
    
    async def test_search_stocks(self, client: AsyncClient, normal_user_token: str, sample_stock):
        """测试搜索股票"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        # 按代码搜索
        response = await client.get("/api/v1/stocks?search=AAP", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 1
        
        # 按名称搜索
        response = await client.get("/api/v1/stocks?search=Apple", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 1
    
    async def test_add_stock_price(self, client: AsyncClient, superuser_token: str, sample_stock):
        """测试添加股票价格"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        price_data = {
            "date": datetime.now().isoformat(),
            "open": 150.0,
            "high": 155.0,
            "low": 148.0,
            "close": 152.0,
            "volume": 1000000
        }
        
        response = await client.post(
            f"/api/v1/stocks/{sample_stock.id}/prices",
            json=price_data,
            headers=headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["open"] == price_data["open"]
        assert data["close"] == price_data["close"]
        assert data["stock_id"] == sample_stock.id
    
    async def test_add_invalid_stock_price(self, client: AsyncClient, superuser_token: str, sample_stock):
        """测试添加无效股票价格"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        # 无效价格：开盘价高于最高价
        price_data = {
            "date": datetime.now().isoformat(),
            "open": 160.0,  # 高于最高价
            "high": 155.0,
            "low": 148.0,
            "close": 152.0,
            "volume": 1000000
        }
        
        response = await client.post(
            f"/api/v1/stocks/{sample_stock.id}/prices",
            json=price_data,
            headers=headers
        )
        assert response.status_code == 400
        assert "Invalid price data" in response.json()["detail"]
    
    async def test_get_stock_prices(self, client: AsyncClient, normal_user_token: str, sample_stock, db_session):
        """测试获取股票价格历史"""
        from app.models.stock import StockPrice
        
        # 先添加一些价格数据
        price = StockPrice(
            stock_id=sample_stock.id,
            date=datetime.now(),
            open=150.0,
            high=155.0,
            low=148.0,
            close=152.0,
            volume=1000000
        )
        db_session.add(price)
        await db_session.commit()
        
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        response = await client.get(
            f"/api/v1/stocks/{sample_stock.id}/prices",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
    
    async def test_bulk_add_stock_prices(self, client: AsyncClient, superuser_token: str, sample_stock):
        """测试批量添加股票价格"""
        headers = {"Authorization": f"Bearer {superuser_token}"}
        
        base_date = datetime.now()
        bulk_data = {
            "stock_id": sample_stock.id,
            "prices": [
                {
                    "date": (base_date - timedelta(days=2)).isoformat(),
                    "open": 148.0,
                    "high": 152.0,
                    "low": 147.0,
                    "close": 150.0,
                    "volume": 800000
                },
                {
                    "date": (base_date - timedelta(days=1)).isoformat(),
                    "open": 150.0,
                    "high": 155.0,
                    "low": 149.0,
                    "close": 153.0,
                    "volume": 900000
                }
            ]
        }
        
        response = await client.post(
            f"/api/v1/stocks/{sample_stock.id}/prices/bulk",
            json=bulk_data,
            headers=headers
        )
        assert response.status_code == 200
        assert "Successfully added 2 price records" in response.json()["message"]