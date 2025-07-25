# 🏠 A2A MCP Real Estate

> Korean Real Estate Recommendation System using FastMCP  
> AI-powered property analysis with investment value and quality of life evaluation

[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.6-blue.svg)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-red.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

A2A MCP Real Estate는 한국 부동산 시장을 위한 AI 기반 추천 시스템입니다. FastMCP(Model Context Protocol) 서버를 통해 부동산 실거래가 데이터 분석, 위치 기반 서비스, 그리고 투자가치와 삶의질을 종합한 맞춤형 부동산 추천 서비스를 제공합니다.

### ✨ Key Features

- 🏢 **실거래가 데이터 조회**: 국토교통부 공공데이터 API 연동
- 📍 **위치 기반 분석**: 지하철역 거리, 편의시설, 공원 접근성 분석
- 💰 **투자가치 평가**: AI 기반 투자 수익성 분석
- 🌿 **삶의질 평가**: 거주 환경의 편의성과 안전성 분석
- 🎯 **맞춤형 추천**: 사용자 성향별 부동산 추천 (투자/삶의질/균형)
- 🌐 **웹 인터페이스**: 직관적인 부동산 분석 도구

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- 국토교통부 공공데이터포털 API 키
- 카카오 개발자센터 API 키

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/A2A-MCP-RealEstate.git
cd A2A-MCP-RealEstate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file with your API keys
```

### Environment Variables

```bash
# .env file
MOLIT_API_KEY=your_molit_api_key_here
KAKAO_API_KEY=your_kakao_api_key_here
PORT=8080
AGENT_ID=agent-py-001
AGENT_NAME=A2A_Python_Agent
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Running the Application

#### 1. Web Interface (Recommended)
```bash
# Start the web server
python runner.py

# Access the web interface
open http://localhost:8080/web/
```

#### 2. MCP Servers (Standalone)
```bash
# Real Estate Recommendation MCP Server
python app/mcp/real_estate_recommendation_mcp.py

# Location Service MCP Server
python app/mcp/location_service.py
```

#### 3. Claude Desktop Integration
Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "korean-realestate": {
      "command": "python",
      "args": ["app/mcp/real_estate_recommendation_mcp.py"],
      "cwd": "/path/to/A2A-MCP-RealEstate"
    }
  }
}
```

## 🛠️ MCP Tools

### Real Estate Recommendation Server

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_real_estate_data` | 부동산 실거래가 조회 | `lawd_cd`, `deal_ymd`, `property_type` |
| `analyze_location` | 위치 분석 (지하철, 편의시설) | `address`, `lat`, `lon` |
| `evaluate_investment_value` | 투자가치 평가 | Property details + preferences |
| `evaluate_life_quality` | 삶의질가치 평가 | Property details + preferences |
| `recommend_property` | 종합 부동산 추천 | All property details + `user_preference` |

### Location Service Server

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `find_nearest_subway_stations` | 가장 가까운 지하철역 검색 | `address`, `lat`, `lon`, `limit` |
| `address_to_coordinates` | 주소를 좌표로 변환 | `address` |
| `find_nearby_facilities` | 주변 편의시설 검색 | `lat`, `lon`, `category`, `radius` |
| `calculate_location_score` | 위치 점수 계산 | `subway_distance`, `facilities_count`, `park_distance` |

## 📊 Evaluation System

### Investment Value Analysis (투자가치 평가)

| Factor | Weight | Description |
|--------|--------|-------------|
| 🏷️ Price | 25% | 시세 대비 가격 합리성 |
| 📐 Area | 20% | 투자 선호 면적대 (20-35평) |
| 🏢 Floor | 15% | 중간층~중상층 선호도 |
| 🚇 Transportation | 25% | 지하철 접근성 |
| 🔮 Future Value | 15% | 재건축/개발 가능성 |

### Quality of Life Analysis (삶의질가치 평가)

| Factor | Weight | Description |
|--------|--------|-------------|
| 🌳 Environment | 25% | 공원, 녹지 접근성 |
| 🏪 Convenience | 25% | 편의시설 개수 및 접근성 |
| 🛡️ Safety | 20% | 층수, 치안, 교통안전 |
| 🎓 Education | 15% | 학교, 학원가 접근성 |
| 🎭 Culture | 15% | 문화시설 접근성 |

### Grading System

- **A+ (90-100점)**: 매우 우수 - 강력 추천
- **A (80-89점)**: 우수 - 추천
- **B+ (70-79점)**: 양호 - 조건부 추천
- **B (60-69점)**: 보통 - 신중 검토
- **C (60점 미만)**: 개선 필요 - 보류

## 🏗️ Architecture

```
📁 A2A-MCP-RealEstate/
├── 📂 app/
│   ├── 📂 mcp/                    # FastMCP Servers
│   │   ├── 🏠 real_estate_recommendation_mcp.py  # Main recommendation server
│   │   └── 📍 location_service.py                # Location analysis server
│   ├── 📂 routes/                 # Web API Routes
│   │   ├── 🌐 web_routes.py       # Web interface routes
│   │   └── 🔧 mcp_routes.py       # MCP API routes
│   ├── 📂 utils/                  # Utilities
│   │   ├── 🔌 mcp_client.py       # MCP client utilities
│   │   ├── ⚙️ config.py           # Configuration management
│   │   └── 📝 logger.py           # Logging utilities
│   ├── 📂 templates/              # HTML Templates
│   │   ├── 🏠 index.html          # Home page
│   │   ├── 🧪 mcp_test.html       # MCP testing interface
│   │   ├── 🤖 agent_test.html     # Agent testing interface
│   │   └── 📊 result templates    # Result display templates
│   └── 📄 main.py                 # FastAPI application
├── 📄 runner.py                   # Application runner
├── 📄 requirements.txt            # Python dependencies
├── 📄 task.md                     # Development tasks
└── 📄 README.md                   # This file
```

## 📱 Web Interface

### Home Page
- 시스템 개요 및 주요 기능 소개
- MCP 테스트와 Agent 테스트로의 직접 링크

### MCP Testing Interface
- 실거래가 조회 도구 테스트
- 지하철역 검색 도구 테스트
- 편의시설 검색 도구 테스트
- 위치 점수 계산 도구 테스트

### Agent Testing Interface
- 부동산 정보 입력 폼
- 실시간 투자가치 및 삶의질 분석
- 종합 추천 결과 시각화
- 상세 평가 리포트

## 🔧 API Keys Setup

### 1. 국토교통부 공공데이터포털
1. [공공데이터포털](https://www.data.go.kr/) 회원가입
2. "아파트 실거래가 정보" 활용신청
3. 승인된 API 키를 `MOLIT_API_KEY`에 설정

### 2. 카카오 개발자센터
1. [카카오 개발자센터](https://developers.kakao.com/) 앱 생성
2. "로컬 > 주소 검색" API 활성화
3. REST API 키를 `KAKAO_API_KEY`에 설정

## 📈 Usage Examples

### CLI Example (MCP Server)
```bash
# Start the MCP server
python app/mcp/real_estate_recommendation_mcp.py

# The server will be available for MCP clients
# Example tools: get_real_estate_data, recommend_property, etc.
```

### Web Interface Example
```bash
# Start web server
python runner.py

# Navigate to http://localhost:8080/web/
# 1. Go to "MCP 테스트" for data query testing
# 2. Go to "Agent 테스트" for property recommendation
```

### API Example
```python
import httpx

# Get apartment trade data
response = await httpx.post("http://localhost:8080/web/api/mcp/test", json={
    "tool_name": "get_real_estate_data",
    "parameters": {
        "lawd_cd": "11680",  # Gangnam-gu, Seoul
        "deal_ymd": "202401",  # January 2024
        "property_type": "아파트"
    }
})
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastMCP**: FastMCP framework for rapid MCP server development
- **국토교통부**: Real estate transaction data via public data portal
- **카카오**: Location and mapping services
- **FastAPI**: Modern web framework for building APIs
- **Bootstrap**: Frontend framework for responsive web design

## 📞 Support

- 📧 Issues: [GitHub Issues](https://github.com/your-username/A2A-MCP-RealEstate/issues)
- 📖 Documentation: See `/docs` endpoint when running the server
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/A2A-MCP-RealEstate/discussions)

---

**🏠 A2A MCP Real Estate** - Making Korean real estate investment decisions smarter with AI and MCP technology.