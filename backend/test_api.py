#!/usr/bin/env python3
"""
API功能测试脚本
"""

import asyncio
import httpx
import json


async def test_api():
    """测试API功能"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # 1. 测试健康检查
            print("🔍 测试健康检查...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"✅ 健康检查: {response.json()}")
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return
            
            # 2. 测试用户注册
            print("\n👤 测试用户注册...")
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            response = await client.post(f"{base_url}/api/v1/auth/register", json=user_data)
            if response.status_code == 201:
                print(f"✅ 用户注册成功: {response.json()['username']}")
            else:
                print(f"⚠️ 用户注册: {response.status_code} - {response.text}")
            
            # 3. 测试用户登录
            print("\n🔐 测试用户登录...")
            login_data = {
                "username": "testuser",
                "password": "TestPassword123!"
            }
            
            response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                token = token_data["access_token"]
                print(f"✅ 登录成功，令牌获取")
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return
            
            # 4. 测试获取股票列表
            print("\n📈 测试获取股票列表...")
            response = await client.get(f"{base_url}/api/v1/stocks", headers=headers)
            if response.status_code == 200:
                stocks_data = response.json()
                print(f"✅ 获取到 {len(stocks_data['items'])} 只股票")
                for stock in stocks_data['items'][:3]:
                    print(f"  - {stock['symbol']}: {stock['name']}")
            else:
                print(f"❌ 获取股票列表失败: {response.status_code}")
            
            # 5. 测试获取股票详情
            print("\n📊 测试获取股票详情...")
            if stocks_data['items']:
                stock_id = stocks_data['items'][0]['id']
                response = await client.get(f"{base_url}/api/v1/stocks/{stock_id}", headers=headers)
                if response.status_code == 200:
                    stock_detail = response.json()
                    print(f"✅ 股票详情: {stock_detail['symbol']} - {stock_detail['name']}")
                    if stock_detail.get('latest_price'):
                        print(f"  最新价格: ${stock_detail['latest_price']['close']}")
                    if stock_detail.get('price_change_24h'):
                        print(f"  24h变化: ${stock_detail['price_change_24h']:.2f}")
                else:
                    print(f"❌ 获取股票详情失败: {response.status_code}")
            
            # 6. 测试获取价格历史
            print("\n📈 测试获取价格历史...")
            if stocks_data['items']:
                stock_id = stocks_data['items'][0]['id']
                response = await client.get(f"{base_url}/api/v1/stocks/{stock_id}/prices", headers=headers)
                if response.status_code == 200:
                    prices_data = response.json()
                    print(f"✅ 获取到 {len(prices_data['items'])} 条价格记录")
                    for price in prices_data['items'][:3]:
                        print(f"  {price['date'][:10]}: 开${price['open']:.2f} 收${price['close']:.2f} 量{price['volume']:,}")
                else:
                    print(f"❌ 获取价格历史失败: {response.status_code}")
            
            # 7. 测试创建监控列表
            print("\n👀 测试创建监控列表...")
            watchlist_data = {
                "name": "我的测试监控列表",
                "description": "用于测试的监控列表",
                "is_public": False
            }
            
            response = await client.post(f"{base_url}/api/v1/watchlists", json=watchlist_data, headers=headers)
            if response.status_code == 201:
                watchlist = response.json()
                print(f"✅ 监控列表创建成功: {watchlist['name']}")
                
                # 8. 测试添加股票到监控列表
                if stocks_data['items']:
                    print("\n➕ 测试添加股票到监控列表...")
                    stock_to_add = {
                        "stock_id": stocks_data['items'][0]['id'],
                        "notes": "测试添加的股票"
                    }
                    
                    response = await client.post(
                        f"{base_url}/api/v1/watchlists/{watchlist['id']}/stocks",
                        json=stock_to_add,
                        headers=headers
                    )
                    if response.status_code == 201:
                        added_stock = response.json()
                        print(f"✅ 股票添加成功: {added_stock['stock']['symbol']}")
                    else:
                        print(f"❌ 添加股票失败: {response.status_code}")
            else:
                print(f"❌ 创建监控列表失败: {response.status_code}")
            
            print("\n🎉 API测试完成！")
            
        except httpx.ConnectError:
            print("❌ 无法连接到API服务器。请确保服务器正在运行在 http://localhost:8000")
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {e}")


if __name__ == "__main__":
    print("🚀 开始API功能测试")
    print("📝 请确保后端服务正在运行: uvicorn main:app --reload")
    print("-" * 50)
    
    asyncio.run(test_api())