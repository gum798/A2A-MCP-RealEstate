#!/usr/bin/env python3
"""
독립적인 MCP 서버 시작 스크립트
FastAPI 애플리케이션과 분리하여 진정한 MCP 프로토콜 사용
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.mcp.real_estate_recommendation_mcp import mcp

async def main():
    """MCP 서버 시작"""
    print("🏠 부동산 추천 MCP 서버 독립 실행")
    print("📡 MCP 프로토콜 통신 대기 중...")
    print("🔌 stdin/stdout을 통한 JSON-RPC 통신")
    
    # FastMCP 서버 실행
    mcp.run()

if __name__ == "__main__":
    asyncio.run(main())