# 股票信息采集系统

一个基于Web的股票信息采集与分析平台，提供实时数据采集、技术分析和个性化投资建议。

## 项目结构

```
quantinfo_collect/
├── frontend/       # React前端应用
├── backend/        # FastAPI后端服务
├── api-specs/      # API接口规范文档
├── docs/           # 项目文档
└── docker-compose.yml
```

## 技术栈

- **前端**: React + Vite + TypeScript + Ant Design
- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **数据采集**: Celery + Redis + yfinance
- **部署**: Docker + Docker Compose

## 开发分支策略

- `main`: 主分支，稳定版本
- `dev/frontend`: 前端开发分支
- `dev/backend`: 后端开发分支
- `dev/data-service`: 数据采集服务分支

## 快速开始

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 全栈开发
```bash
docker-compose up
```

## API文档

启动后端服务后访问：http://localhost:8000/docs

## 贡献指南

1. 从main分支创建feature分支
2. 完成开发后提交PR
3. Code Review通过后合并到对应的dev分支
4. 测试通过后合并到main分支