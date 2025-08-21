 🎯 Render 배포 시작하기

  이제 Render에서 직접 배포해보겠습니다:

  1단계: Render 사이트 접속

  https://render.com 으로 이동하여 GitHub 계정으로 로그인하세요.

  2단계: 새 서비스 생성

  1. "New +" 버튼 클릭 (우측 상단)
  2. "Web Service" 선택
  3. "Connect a repository" 에서 GitHub 연결

  3단계: 저장소 선택

  - gum798/A2A-MCP-RealEstate 저장소 선택
  - "Connect" 클릭

  4단계: 서비스 설정

  Name: a2a-agent-card
  Region: Oregon (US West)
  Branch: main
  Runtime: Python 3
  Build Command: pip install -r requirements.txt
  Start Command: python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT

  5단계: 환경 변수 추가

  "Environment Variables" 섹션에서 다음을 추가:
  ENVIRONMENT = production
  AGENT_ID = agent-py-001
  AGENT_NAME = A2A_Python_Agent
  LOG_LEVEL = INFO

  6단계: 배포 시작

  - "Create Web Service" 클릭
  - 빌드 로그를 확인하며 배포 진행상황 모니터링

  ⏰ 예상 소요시간

  - 빌드: 3-5분
  - 배포: 1-2분

  배포가 시작되면 로그에서 진행상황을 확인할 수 있습니다. 완료되면 생성된 URL을 알려주세요!