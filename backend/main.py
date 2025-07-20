from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.database import create_db_and_tables
from app.core.init_db import init_db
from app.services.scheduler_service import scheduler_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    try:
        await init_db()
        await scheduler_service.start()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")
    try:
        await scheduler_service.stop()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="股票信息采集系统 API",
    description="提供股票数据查询、技术分析和用户管理功能",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "股票信息采集系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}