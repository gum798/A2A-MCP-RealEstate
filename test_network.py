#!/usr/bin/env python3
"""
MCP 환경에서 네트워크 연결 테스트
"""

import asyncio
import httpx
import sys
import os
from dotenv import load_dotenv

load_dotenv()

async def test_network():
    """네트워크 연결 테스트"""
    print("🌐 네트워크 연결 테스트 시작", file=sys.stderr)
    
    # 환경변수 확인
    molit_key = os.getenv("MOLIT_API_KEY")
    print(f"🔑 MOLIT_API_KEY: {'있음' if molit_key else '없음'}", file=sys.stderr)
    
    # 간단한 HTTP 요청 테스트
    test_urls = [
        "https://httpbin.org/get",  # 기본 HTTP 테스트
        "http://openapi.molit.go.kr",  # 국토교통부 서버
        "https://rt.molit.go.kr"  # 실거래가 사이트
    ]
    
    for url in test_urls:
        try:
            print(f"📡 테스트 중: {url}", file=sys.stderr)
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                verify=False,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                print(f"✅ {url}: {response.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"❌ {url}: {str(e)}", file=sys.stderr)
    
    print("🌐 네트워크 테스트 완료", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(test_network())