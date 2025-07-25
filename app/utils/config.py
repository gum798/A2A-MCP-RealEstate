"""
설정 관리 모듈
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    port: int = 8000
    host: str = "0.0.0.0"
    environment: str = "development"
    
    # 에이전트 설정
    agent_id: str = "agent-py-001"
    agent_name: str = "A2A_Python_Agent"
    
    # 로깅 설정
    log_level: str = "INFO"
    
    # 기타 설정
    request_timeout: int = 30
    max_connections: int = 100
    
    # 부동산 API 설정
    molit_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역 설정 인스턴스
settings = Settings()

def get_settings():
    """설정 인스턴스 반환"""
    return settings