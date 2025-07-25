#!/bin/bash
# A2A Agent 가상환경 활성화 스크립트

echo "🐍 A2A Agent 가상환경 활성화 중..."

# 가상환경 활성화
source venv/bin/activate

echo "✅ 가상환경이 활성화되었습니다."
echo "📦 설치된 패키지 목록:"
pip list

echo ""
echo "🚀 서버 실행 명령어:"
echo "  개발 서버: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  프로덕션: uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "📖 API 문서: http://localhost:8000/docs"
echo "💾 환경 변수: .env 파일에서 설정"
echo ""

# 사용자 셸 실행
exec "$SHELL"