#!/bin/bash
# A2A Agent 프로덕션 서버 실행 스크립트

echo "🏭 A2A Agent 프로덕션 서버 시작 중..."

# 가상환경 활성화
source venv/bin/activate

# 프로덕션 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 28000