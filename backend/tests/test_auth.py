import pytest
from httpx import AsyncClient


class TestAuth:
    """认证相关测试"""
    
    async def test_register_user(self, client: AsyncClient):
        """测试用户注册"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewPassword123!",
            "full_name": "New User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "hashed_password" not in data
    
    async def test_register_user_duplicate_email(self, client: AsyncClient):
        """测试重复邮箱注册"""
        user_data = {
            "email": "test@example.com",
            "username": "user1",
            "password": "Password123!",
            "full_name": "User 1"
        }
        
        # 第一次注册
        response1 = await client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # 第二次注册相同邮箱
        user_data["username"] = "user2"
        response2 = await client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    async def test_register_user_invalid_password(self, client: AsyncClient):
        """测试无效密码注册"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",  # 弱密码
            "full_name": "Test User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    async def test_login_success(self, client: AsyncClient, normal_user_token: str):
        """测试成功登录"""
        # normal_user_token fixture已经创建了用户并获取了令牌
        assert normal_user_token is not None
        assert isinstance(normal_user_token, str)
        assert len(normal_user_token) > 0
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """测试无效凭据登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_get_current_user(self, client: AsyncClient, normal_user_token: str):
        """测试获取当前用户信息"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@user.com"
        assert data["is_active"] is True
    
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403
    
    async def test_invalid_token(self, client: AsyncClient):
        """测试无效令牌"""
        headers = {"Authorization": "Bearer invalid-token"}
        
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
    
    async def test_change_password(self, client: AsyncClient, normal_user_token: str):
        """测试修改密码"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        password_data = {
            "current_password": "testpassword123!",
            "new_password": "NewPassword456!"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
        
        # 测试用新密码登录
        login_data = {
            "username": "testuser",
            "password": "NewPassword456!"
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
    
    async def test_change_password_wrong_current(self, client: AsyncClient, normal_user_token: str):
        """测试使用错误当前密码修改密码"""
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword456!"
        }
        
        response = await client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert response.status_code == 400
        assert "Incorrect password" in response.json()["detail"]