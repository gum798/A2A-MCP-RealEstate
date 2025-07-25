"""
로깅 유틸리티
"""
import sys
from loguru import logger as loguru_logger
from app.utils.config import settings


def setup_logger():
    """로거 설정"""
    # 기본 핸들러 제거
    loguru_logger.remove()
    
    # 콘솔 핸들러 추가
    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # 파일 핸들러 추가 (프로덕션 환경)
    if settings.environment == "production":
        loguru_logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
    
    return loguru_logger


# 로거 인스턴스
logger = setup_logger()

def get_logger(name: str = None):
    """로거 인스턴스 반환"""
    return logger.bind(name=name) if name else logger