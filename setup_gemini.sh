#!/bin/bash
# Gemini CLI 설정 스크립트

echo "🤖 Gemini CLI 설정 중..."

# Node.js 버전 확인
node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18 이상이 필요합니다. 현재 버전: $(node --version)"
    exit 1
fi

# Gemini CLI 설치 확인
if ! command -v gemini &> /dev/null; then
    echo "📦 Gemini CLI 설치 중..."
    npm install -g @google/gemini-cli
else
    echo "✅ Gemini CLI가 이미 설치되어 있습니다."
fi

echo ""
echo "🔑 Gemini CLI 인증 설정:"
echo "1. Google 계정 로그인 (권장): gemini 명령어 실행 후 로그인"
echo "2. API 키 사용: https://aistudio.google.com/apikey 에서 키 생성 후"
echo "   export GEMINI_API_KEY='your_api_key' 설정"
echo ""
echo "💡 사용법:"
echo "  gemini                    # 대화형 모드"
echo "  gemini '질문 내용'       # 직접 질문"
echo ""
echo "✅ Gemini CLI 설정 완료!"