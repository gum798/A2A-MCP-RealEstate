"""
A2A Agent FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from datetime import datetime
import os

from app.routes import agent_routes, data_routes, ai_routes, mcp_routes, web_routes, review_routes, character_routes
from app.utils.config import settings
from app.utils.logger import logger
from app.utils.fastmcp_client import cleanup_mcp_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting A2A Agent Server")
    logger.info(f"Agent ID: {settings.agent_id}")
    logger.info(f"Agent Name: {settings.agent_name}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Agent Card URL: http://localhost:{settings.port}/api/agent/.well-known/agent-card")
    logger.info(f"Character Agents: http://localhost:{settings.port}/api/characters/characters")
    logger.info(f"Chat UI: http://localhost:{settings.port}/web/chat")
    yield
    logger.info("Shutting down A2A Agent Server")
    # MCP 클라이언트들 정리
    await cleanup_mcp_clients()


# FastAPI 앱 생성
app = FastAPI(
    title="A2A Agent",
    description="Application-to-Application Agent for inter-service communication",
    version="1.0.0",
    lifespan=lifespan
)

# JSON 응답 UTF-8 인코딩 설정
import json
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# 기본 JSON 응답 인코딩 설정
@app.middleware("http")
async def ensure_utf8_json(request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Request {request_id} completed in {process_time:.3f}s - Status: {response.status_code}")
    
    return response

# 라우터 등록
app.include_router(agent_routes.router, prefix="/api/agent", tags=["agent"])
app.include_router(character_routes.router, prefix="/api/characters", tags=["characters"])
app.include_router(data_routes.router, prefix="/api/data", tags=["data"])
app.include_router(ai_routes.router, prefix="/api/ai", tags=["ai"])
app.include_router(mcp_routes.router, tags=["mcp"])
app.include_router(web_routes.router, tags=["web"])
app.include_router(review_routes.router, tags=["reviews"])

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent": {
            "id": settings.agent_id,
            "name": settings.agent_name
        },
        "version": "1.0.0"
    }

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 정보"""
    return {
        "message": "A2A Python Agent Server",
        "version": "1.0.0",
        "agent": {
            "id": settings.agent_id,
            "name": settings.agent_name
        },
        "endpoints": [
            "/health",
            "/docs",
            "/api/agent/",
            "/api/characters/",
            "/api/data/",
            "/api/ai/",
            "/api/mcp/",
            "/web/"
        ],
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )