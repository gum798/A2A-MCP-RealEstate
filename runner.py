#!/usr/bin/env python3
"""
A2A Agent 서버 실행 스크립트
"""

import uvicorn
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.config import settings
from app.utils.logger import logger

def main():
    """서버 실행 메인 함수"""
    
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