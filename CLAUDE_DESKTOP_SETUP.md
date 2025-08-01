# Claude Desktop MCP 설정 가이드

## 1️⃣ 의존성 설치

```bash
# 프로젝트 디렉토리로 이동
cd /Users/jhseo/Desktop/0020.project/A2A_Agent

# 가상환경 생성 (옵션)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 필요한 패키지 설치
pip install -r requirements.txt
```

## 2️⃣ API 키 설정

### 국토교통부 API 키 발급
1. https://www.data.go.kr/ 접속
2. 회원가입 후 로그인
3. "부동산 실거래가" 검색
4. API 신청 및 승인 대기
5. 발급받은 API 키 복사

### 네이버 클라우드 플랫폼 API 키 발급  
1. https://www.ncloud.com/ 접속
2. 회원가입 후 콘솔 로그인
3. AI·Application Service > Maps 선택
4. Application 등록
5. Client ID, Client Secret 복사

## 3️⃣ Claude Desktop 설정

### macOS
```bash
# 설정 파일 위치
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```bash
# 설정 파일 위치  
%APPDATA%\Claude\claude_desktop_config.json
```

## 4️⃣ 설정 파일 내용

아래 내용을 `claude_desktop_config.json`에 복사하세요:

```json
{
  "mcpServers": {
    "real-estate-korea": {
      "command": "python3",
      "args": [
        "/Users/jhseo/Desktop/0020.project/A2A_Agent/mcp_real_estate_server.py"
      ],
      "env": {
        "MOLIT_API_KEY": "발급받은_국토교통부_API_키",
        "NAVER_CLIENT_ID": "발급받은_네이버_CLIENT_ID", 
        "NAVER_CLIENT_SECRET": "발급받은_네이버_CLIENT_SECRET"
      }
    }
  }
}
```

⚠️ **주의사항:**
- 절대 경로를 정확히 입력하세요
- API 키를 실제 발급받은 키로 교체하세요
- Windows의 경우 경로 구분자를 `\\` 또는 `/`로 사용하세요

## 5️⃣ Claude Desktop 재시작

1. Claude Desktop 완전 종료
2. 애플리케이션 재시작
3. 새 대화 시작

## 6️⃣ 사용 가능한 기능 확인

Claude Desktop에서 다음과 같이 물어보세요:

```
사용 가능한 도구들을 보여줘
```

다음 도구들이 표시되어야 합니다:
- 🏠 `get_apartment_sales` - 아파트 매매 실거래가 조회
- 🏢 `get_officetel_sales` - 오피스텔 매매 실거래가 조회  
- 🏘️ `get_multi_family_sales` - 연립다세대 매매 실거래가 조회
- 🚇 `calculate_subway_distance` - 지하철역 거리 계산
- 🏪 `search_nearby_facilities` - 주변 편의시설 검색
- 🤖 `evaluate_investment_value` - 투자가치 평가
- 💝 `evaluate_life_quality` - 삶의질가치 평가
- 🎯 `comprehensive_recommendation` - 종합 추천

## 7️⃣ 사용 예시

```
강남구 역삼동 아파트 실거래가를 조회해줘

서울특별시 강남구 역삼동 123-45, 15억, 84㎡, 15층/25층, 2018년 건축 아파트의 투자가치를 평가해줘

위 매물에 대한 종합 추천을 해줘
```

## 🔧 문제 해결

### MCP 서버가 연결되지 않을 때:
1. 경로가 정확한지 확인
2. Python 환경에 필요한 패키지가 설치되었는지 확인
3. API 키가 올바르게 설정되었는지 확인
4. Claude Desktop 로그 확인

### 로그 확인 방법:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%LOCALAPPDATA%\Claude\logs\mcp*.log`

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. Python 버전 (3.8 이상 권장)
2. 필요한 패키지 설치 상태
3. API 키 유효성
4. 네트워크 연결 상태