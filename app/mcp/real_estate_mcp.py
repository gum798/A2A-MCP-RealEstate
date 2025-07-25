#!/usr/bin/env python3
"""
한국 부동산 가격 조회 MCP 서버 실행 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp.real_estate_server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())