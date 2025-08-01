#!/usr/bin/env python3
"""
부동산 MCP 서버 - Claude Desktop용
실거래가 조회, 위치 분석, AI 추천을 제공하는 독립 실행형 MCP 서버
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 직접 real_estate_recommendation_mcp 모듈 실행
if __name__ == "__main__":
    # 원본 모듈의 main 실행부를 호출
    from app.mcp import real_estate_recommendation_mcp
    
    # 이미 모듈 끝에 있는 실행 코드가 동작함
    print("🏠 부동산 추천 시스템 MCP 서버", file=sys.stderr)
    print(f"🔑 MOLIT API 키: {'✅ 설정됨' if os.getenv('MOLIT_API_KEY') else '❌ 미설정'}", file=sys.stderr)
    print(f"🗺️  NAVER API 키: {'✅ 설정됨' if os.getenv('NAVER_CLIENT_ID') else '❌ 미설정'}", file=sys.stderr)
    print("🚀 FastMCP JSON-RPC 서버 시작 (stdin/stdout)...", file=sys.stderr)
    
    # FastMCP 서버 실행
    real_estate_recommendation_mcp.mcp.run()