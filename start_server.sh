#!/bin/bash

# A2A Agent 서버 시작 스크립트 (포트 충돌 해결 포함)

PORT=28000
PYTHON_CMD="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"

echo "🚀 A2A Agent 서버 시작 중..."
echo "포트: $PORT"

# 1. 포트가 사용 중인지 확인
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  포트 $PORT이 사용 중입니다. 기존 프로세스를 종료합니다..."
    
    # uvicorn 프로세스 종료
    pkill -f "uvicorn.*$PORT" 2>/dev/null
    sleep 1
    
    # 포트를 사용하는 프로세스 강제 종료
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 2
    
    # 확인
    if lsof -ti:$PORT > /dev/null 2>&1; then
        echo "❌ 포트 $PORT을 해제할 수 없습니다. 수동으로 확인해주세요:"
        echo "   lsof -ti:$PORT | xargs kill -9"
        exit 1
    else
        echo "✅ 포트 $PORT이 해제되었습니다."
    fi
fi

# 2. Python 가상환경 확인
if [ -d "venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source venv/bin/activate
    PYTHON_CMD="python"
fi

# 3. 서버 시작
echo "🌟 A2A Agent 서버를 시작합니다..."
echo "   URL: http://localhost:$PORT"
echo "   Web Chat: http://localhost:$PORT/web/agent-chat"
echo "   API Docs: http://localhost:$PORT/docs"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo "=================================="

# uvicorn 서버 시작
$PYTHON_CMD -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT