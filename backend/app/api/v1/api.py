from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, stocks, watchlists, admin

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 股票相关路由
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])

# 监控列表路由
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])

# 管理员路由
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])