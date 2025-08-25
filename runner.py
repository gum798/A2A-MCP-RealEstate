#!/usr/bin/env python3
"""
A2A Agent 서버 실행 스크립트
"""

import uvicorn
import sys
import os
import socket
import subprocess
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.config import settings
from app.utils.logger import logger

def check_port_available(port):
    """포트가 사용 가능한지 확인"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(('localhost', port))
            return True
        except OSError:
            return False

def kill_port_processes(port):
    """포트를 사용하는 프로세스들을 종료"""
    try:
        # lsof로 포트 사용 프로세스 찾기
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(["kill", "-9", pid], timeout=5)
                    logger.info(f"프로세스 {pid} 종료됨")
                except subprocess.TimeoutExpired:
                    pass
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False

def main():
    """서버 실행 메인 함수"""
    
    # 포트 사용 가능 여부 확인 및 자동 정리
    if not check_port_available(settings.port):
        logger.warning(f"⚠️  포트 {settings.port}가 이미 사용 중입니다.")
        logger.info("기존 프로세스를 자동으로 정리합니다...")
        
        if kill_port_processes(settings.port):
            logger.info("기존 프로세스가 종료되었습니다.")
            # 잠시 대기 후 다시 확인
            import time
            time.sleep(2)
            if not check_port_available(settings.port):
                logger.error(f"포트 {settings.port} 정리에 실패했습니다. 수동으로 확인이 필요합니다.")
                sys.exit(1)
        else:
            logger.info("정리할 프로세스가 없거나 이미 정리되었습니다.")
    
    # 환경 설정 출력
    logger.info("=" * 50)
    logger.info("🚀 A2A Agent 서버 시작")
    logger.info(f"📍 호스트: {settings.host}")
    logger.info(f"🔌 포트: {settings.port}")
    logger.info(f"🔧 환경: {settings.environment}")
    logger.info(f"🤖 에이전트 ID: {settings.agent_id}")
    logger.info(f"📝 에이전트 이름: {settings.agent_name}")
    logger.info(f"📊 로그 레벨: {settings.log_level}")
    
    # API 키 설정 확인
    if settings.molit_api_key:
        logger.info("🔑 국토교통부 API 키: 설정됨")
    else:
        logger.warning("⚠️  국토교통부 API 키: 설정되지 않음")
        logger.warning("   부동산 데이터 조회를 위해 .env 파일에 MOLIT_API_KEY를 설정하세요")
    
    if settings.naver_client_id and settings.naver_client_secret:
        logger.info("🗺️  네이버 API 키: 설정됨")
    else:
        logger.warning("⚠️  네이버 API 키: 설정되지 않음")
        logger.warning("   위치 서비스를 위해 .env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정하세요")
    
    # Gemini API 키 확인
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        logger.info("🤖 Google Gemini API 키: 설정됨")
        logger.info("   투심이와 삼돌이의 LLM 기반 응답 시스템이 활성화됩니다")
    else:
        logger.warning("⚠️  Google Gemini API 키: 설정되지 않음")
        logger.warning("   캐릭터 에이전트가 기본 응답으로 동작합니다")
        logger.warning("   .env 파일 또는 환경변수에 GEMINI_API_KEY를 설정하세요")
    
    logger.info("=" * 50)
    
    # 접속 링크 출력
    if settings.environment == "development":
        logger.info("🌐 로컬 접속 링크:")
        logger.info(f"   • 메인 페이지: http://localhost:{settings.port}/web/")
        logger.info(f"   • 투심이&삼돌이 채팅: http://localhost:{settings.port}/web/chat")
        logger.info(f"   • MCP 테스트: http://localhost:{settings.port}/web/mcp")
        logger.info(f"   • Agent 테스트: http://localhost:{settings.port}/web/agent")
        logger.info(f"   • API 문서: http://localhost:{settings.port}/docs")
    else:
        # Railway 배포 환경
        railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        # Render 배포 환경도 지원
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        deploy_url = railway_url or render_url
        
        if deploy_url:
            platform_name = "Railway" if railway_url else "Render"
            logger.info(f"🌐 {platform_name} 배포 링크:")
            logger.info(f"   • 메인 페이지: https://{deploy_url}/web/")
            logger.info(f"   • 투심이&삼돌이 채팅: https://{deploy_url}/web/chat")
            logger.info(f"   • MCP 테스트: https://{deploy_url}/web/mcp")
            logger.info(f"   • Agent 테스트: https://{deploy_url}/web/agent")
            logger.info(f"   • API 문서: https://{deploy_url}/docs")
        else:
            logger.info("🌐 배포 링크:")
            logger.info("   • 투심이&삼돌이 채팅: https://a2a-mcp-realestate.onrender.com/web/chat")
            logger.info("   • 메인 페이지: https://a2a-mcp-realestate.onrender.com/web/")
            logger.info("   • API 문서: https://a2a-mcp-realestate.onrender.com/docs")
    
    logger.info("=" * 50)
    
    # 서버 실행
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
        reload_dirs=[str(project_root / "app")] if settings.environment == "development" else None
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 서버가 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 서버 실행 중 오류 발생: {e}")
        sys.exit(1)