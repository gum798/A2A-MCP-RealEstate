#!/bin/bash
# A2A Agent 개발 서버 실행 스크립트

echo "🚀 A2A Agent 개발 서버 시작 중..."

# 가상환경 활성화
source venv/bin/activate

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 28000