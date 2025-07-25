#!/usr/bin/env python3
"""
FastMCP 한국 부동산 가격 조회 서버 테스트 스크립트
"""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

async def test_fastmcp_server():
    """FastMCP 서버 테스트"""
    
    print("=== FastMCP 한국 부동산 가격 조회 서버 테스트 ===\n")
    
    # 테스트용 MCP 클라이언트 생성
    test_commands = [
        # 1. 서버 정보 확인
        {
            "name": "서버 정보 확인",
            "command": ["python", "app/mcp/fastmcp_realestate.py", "--help"]
        },
        
        # 2. 도구 목록 확인
        {
            "name": "사용 가능한 도구 목록 확인", 
            "description": "FastMCP는 자동으로 함수에서 도구를 생성합니다"
        },
        
        # 3. 리소스 목록 확인
        {
            "name": "사용 가능한 리소스 확인",
            "description": "지역 코드 정보와 사용 가이드가 리소스로 제공됩니다"
        }
    ]
    
    for i, test in enumerate(test_commands, 1):
        print(f"{i}. {test['name']}")
        
        if 'command' in test:
            try:
                result = subprocess.run(
                    test['command'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    cwd=Path(__file__).parent
                )
                
                if result.returncode == 0:
                    print(f"   ✅ 성공")
                    if result.stdout:
                        print(f"   📝 출력: {result.stdout[:200]}...")
                else:
                    print(f"   ❌ 오류: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ 타임아웃")
            except Exception as e:
                print(f"   ❌ 예외: {e}")
        else:
            print(f"   ℹ️  {test.get('description', '테스트 설명이 없습니다')}")
        
        print()
    
    print("=" * 70)
    print("FastMCP 서버 테스트 완료!")
    print("=" * 70)
    
    # 실행 가이드
    print("\n📋 FastMCP 서버 실행 가이드:")
    print("1. MCP 서버 직접 실행:")
    print("   python app/mcp/fastmcp_realestate.py")
    print()
    print("2. Claude Desktop과 연동:")
    print("   Claude Desktop의 설정에서 다음과 같이 MCP 서버를 추가하세요:")
    print("   {")
    print('     "mcpServers": {')
    print('       "korean-realestate": {')
    print('         "command": "python",')
    print('         "args": ["app/mcp/fastmcp_realestate.py"],')
    print('         "cwd": "/path/to/your/project"')
    print('       }')
    print('     }')
    print("   }")
    print()
    print("3. FastMCP Inspector 사용:")
    print("   FastMCP에는 내장 디버깅 도구가 있어 웹 브라우저에서 테스트할 수 있습니다.")
    print()
    print("4. 환경 변수 설정:")
    print("   MOLIT_API_KEY=your_api_key")
    print()
    print("🔗 공공데이터포털: https://www.data.go.kr/dataset/3050988/openapi.do")

def check_environment():
    """환경 확인"""
    print("🔍 환경 확인:")
    
    # Python 버전 확인
    python_version = sys.version.split()[0]
    print(f"   Python 버전: {python_version}")
    
    # FastMCP 설치 확인
    try:
        import fastmcp
        print(f"   FastMCP 버전: {fastmcp.__version__}")
    except ImportError:
        print("   ❌ FastMCP가 설치되지 않았습니다")
        return False
    
    # .env 파일 확인
    env_file = Path(".env")
    if env_file.exists():
        print("   📄 .env 파일: 존재함")
        # API 키 확인
        with open(env_file) as f:
            content = f.read()
            if "MOLIT_API_KEY" in content:
                print("   🔑 MOLIT_API_KEY: 설정됨")
            else:
                print("   ⚠️  MOLIT_API_KEY: 설정되지 않음")
    else:
        print("   ⚠️  .env 파일: 없음")
    
    print()
    return True

if __name__ == "__main__":
    if check_environment():
        asyncio.run(test_fastmcp_server())
    else:
        print("환경 설정을 먼저 완료해주세요.")