"""
한국 부동산 가격 조회 MCP 서버
국토교통부 공공데이터 API를 활용한 실거래가 정보 조회
"""

import json
import asyncio
from typing import Any, Sequence
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource, 
    LoggingLevel
)
import mcp.types as types

from ..utils.logger import logger
from ..utils.config import settings

# MCP 서버 설정
app = Server("korean-realestate")

# 국토교통부 공공데이터 API 설정
MOLIT_BASE_URL = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc"
MOLIT_API_KEY = settings.molit_api_key if settings.molit_api_key else ""

class RealEstateAPI:
    """국토교통부 부동산 실거래가 API 클라이언트"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = MOLIT_BASE_URL
        # DNS 문제 해결을 위해 더 상세한 설정
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False  # SSL 인증서 검증 비활성화 (개발용)
        )
    
    async def get_apartment_trade(self, lawd_cd: str, deal_ymd: str) -> dict:
        """아파트 매매 실거래가 조회"""
        endpoint = f"{self.base_url}/getRTMSDataSvcAptTradeDev"
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": lawd_cd,  # 지역코드 (앞5자리)
            "DEAL_YMD": deal_ymd,  # 계약월 (YYYYMM)
            "numOfRows": 1000,
            "pageNo": 1
        }
        
        logger.info(f"MCP 아파트 매매 실거래가 조회 시작 - 지역코드: {lawd_cd}, 계약년월: {deal_ymd}")
        logger.debug(f"API 호출 URL: {endpoint}")
        logger.debug(f"API 요청 파라미터: {params}")
        
        try:
            response = await self.client.get(endpoint, params=params)
            logger.debug(f"API 응답 상태코드: {response.status_code}")
            logger.debug(f"API 응답 헤더: {dict(response.headers)}")
            logger.debug(f"API 응답 내용: {response.text[:1000]}...")
            response.raise_for_status()
            
            result = self._parse_xml_response(response.text)
            logger.info(f"MCP 아파트 매매 실거래가 조회 완료 - 총 {result.get('total_count', 0)}건")
            return result
        except Exception as e:
            logger.error(f"아파트 매매 실거래가 조회 오류: {e}")
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"요청 URL: {endpoint}")
            logger.error(f"요청 파라미터: {params}")
            return {"error": str(e)}
    
    async def get_apartment_rent(self, lawd_cd: str, deal_ymd: str) -> dict:
        """아파트 전월세 실거래가 조회"""
        endpoint = f"{self.base_url}/getRTMSDataSvcAptRent"
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd,
            "numOfRows": 1000,
            "pageNo": 1
        }
        
        logger.info(f"MCP 아파트 전월세 실거래가 조회 시작 - 지역코드: {lawd_cd}, 계약년월: {deal_ymd}")
        logger.debug(f"API 호출 URL: {endpoint}")
        logger.debug(f"API 요청 파라미터: {params}")
        
        try:
            response = await self.client.get(endpoint, params=params)
            logger.debug(f"API 응답 상태코드: {response.status_code}")
            response.raise_for_status()
            
            result = self._parse_xml_response(response.text)
            logger.info(f"MCP 아파트 전월세 실거래가 조회 완료 - 총 {result.get('total_count', 0)}건")
            return result
        except Exception as e:
            logger.error(f"아파트 전월세 실거래가 조회 오류: {e}")
            return {"error": str(e)}
    
    async def get_officetel_trade(self, lawd_cd: str, deal_ymd: str) -> dict:
        """오피스텔 매매 실거래가 조회"""
        endpoint = f"{self.base_url}/getRTMSDataSvcOffiTrade"
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd,
            "numOfRows": 1000,
            "pageNo": 1
        }
        
        logger.info(f"MCP 오피스텔 매매 실거래가 조회 시작 - 지역코드: {lawd_cd}, 계약년월: {deal_ymd}")
        logger.debug(f"API 호출 URL: {endpoint}")
        logger.debug(f"API 요청 파라미터: {params}")
        
        try:
            response = await self.client.get(endpoint, params=params)
            logger.debug(f"API 응답 상태코드: {response.status_code}")
            response.raise_for_status()
            
            result = self._parse_xml_response(response.text)
            logger.info(f"MCP 오피스텔 매매 실거래가 조회 완료 - 총 {result.get('total_count', 0)}건")
            return result
        except Exception as e:
            logger.error(f"오피스텔 매매 실거래가 조회 오류: {e}")
            return {"error": str(e)}
    
    def _parse_xml_response(self, xml_text: str) -> dict:
        """XML 응답 파싱 (간단한 파싱 로직)"""
        import xml.etree.ElementTree as ET
        
        try:
            logger.debug("XML 응답 파싱 시작")
            root = ET.fromstring(xml_text)
            items = []
            
            # XML 구조에 따라 파싱
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                items.append(item_data)
            
            logger.debug(f"XML 파싱 완료 - {len(items)}개 항목 추출")
            return {"items": items, "total_count": len(items)}
        except Exception as e:
            logger.error(f"XML 파싱 오류: {e}")
            logger.debug(f"파싱 실패한 XML 내용: {xml_text[:500]}...")  # 처음 500자만 로그
            return {"error": f"XML 파싱 실패: {e}"}

# API 클라이언트 인스턴스
logger.info(f"MCP RealEstateAPI 초기화 - API 키 설정 여부: {bool(MOLIT_API_KEY)}")
real_estate_api = RealEstateAPI(MOLIT_API_KEY)

@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """사용 가능한 리소스 목록 반환"""
    return [
        Resource(
            uri="realestate://regions",
            name="지역 코드 정보",
            description="부동산 조회를 위한 행정구역 코드 정보",
            mimeType="application/json"
        ),
        Resource(
            uri="realestate://guide",
            name="사용 가이드",
            description="부동산 가격 조회 API 사용 방법",
            mimeType="text/markdown"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """리소스 내용 읽기"""
    if uri == "realestate://regions":
        # 주요 지역 코드 정보
        regions = {
            "서울특별시": {
                "강남구": "11680",
                "강동구": "11740",
                "강북구": "11305",
                "강서구": "11500",
                "관악구": "11620",
                "광진구": "11215",
                "구로구": "11530",
                "금천구": "11545",
                "노원구": "11350",
                "도봉구": "11320",
                "동대문구": "11230",
                "동작구": "11590",
                "마포구": "11440",
                "서대문구": "11410",
                "서초구": "11650",
                "성동구": "11200",
                "성북구": "11290",
                "송파구": "11710",
                "양천구": "11470",
                "영등포구": "11560",
                "용산구": "11170",
                "은평구": "11380",
                "종로구": "11110",
                "중구": "11140",
                "중랑구": "11260"
            },
            "경기도": {
                "수원시": "41110",
                "성남시": "41130",
                "고양시": "41280",
                "용인시": "41460",
                "부천시": "41190",
                "안산시": "41270",
                "안양시": "41170",
                "남양주시": "41360",
                "화성시": "41590",
                "평택시": "41220"
            }
        }
        return json.dumps(regions, ensure_ascii=False, indent=2)
    
    elif uri == "realestate://guide":
        guide = """# 한국 부동산 가격 조회 MCP 서버 사용 가이드

## 개요
국토교통부 공공데이터 API를 활용하여 한국의 부동산 실거래가 정보를 조회할 수 있는 MCP 서버입니다.

## 사용 가능한 도구

### 1. get_apartment_trade
아파트 매매 실거래가를 조회합니다.
- **lawd_cd**: 지역코드 (5자리, 예: 11680 - 서울 강남구)  
- **deal_ymd**: 계약년월 (6자리, 예: 202401)

### 2. get_apartment_rent  
아파트 전월세 실거래가를 조회합니다.
- **lawd_cd**: 지역코드 (5자리)
- **deal_ymd**: 계약년월 (6자리)

### 3. get_officetel_trade
오피스텔 매매 실거래가를 조회합니다.
- **lawd_cd**: 지역코드 (5자리)
- **deal_ymd**: 계약년월 (6자리)

## 사용 예시
```
강남구 2024년 1월 아파트 매매 실거래가 조회:
- 지역코드: 11680
- 계약년월: 202401
```

## 주의사항
- API 키가 필요합니다 (공공데이터포털에서 발급)
- 지역코드는 행정표준코드관리시스템의 법정동 코드 앞 5자리를 사용
- 계약년월은 YYYYMM 형식으로 입력
"""
        return guide
    
    raise ValueError(f"알 수 없는 리소스: {uri}")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="get_apartment_trade",
            description="아파트 매매 실거래가 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "lawd_cd": {
                        "type": "string",
                        "description": "지역코드 (5자리, 예: 11680)"
                    },
                    "deal_ymd": {
                        "type": "string", 
                        "description": "계약년월 (YYYYMM, 예: 202401)"
                    }
                },
                "required": ["lawd_cd", "deal_ymd"]
            }
        ),
        Tool(
            name="get_apartment_rent",
            description="아파트 전월세 실거래가 조회", 
            inputSchema={
                "type": "object",
                "properties": {
                    "lawd_cd": {
                        "type": "string",
                        "description": "지역코드 (5자리, 예: 11680)"
                    },
                    "deal_ymd": {
                        "type": "string",
                        "description": "계약년월 (YYYYMM, 예: 202401)"
                    }
                },
                "required": ["lawd_cd", "deal_ymd"]
            }
        ),
        Tool(
            name="get_officetel_trade", 
            description="오피스텔 매매 실거래가 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "lawd_cd": {
                        "type": "string",
                        "description": "지역코드 (5자리, 예: 11680)"
                    },
                    "deal_ymd": {
                        "type": "string",
                        "description": "계약년월 (YYYYMM, 예: 202401)"
                    }
                },
                "required": ["lawd_cd", "deal_ymd"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """도구 호출 처리"""
    logger.info(f"MCP 도구 호출 - 도구명: {name}, 파라미터: {arguments}")
    
    if name == "get_apartment_trade":
        lawd_cd = arguments.get("lawd_cd")
        deal_ymd = arguments.get("deal_ymd") 
        
        if not lawd_cd or not deal_ymd:
            logger.warning("필수 파라미터 누락 - lawd_cd 또는 deal_ymd")
            return [types.TextContent(
                type="text",
                text="지역코드(lawd_cd)와 계약년월(deal_ymd)이 필요합니다."
            )]
        
        result = await real_estate_api.get_apartment_trade(lawd_cd, deal_ymd)
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    elif name == "get_apartment_rent":
        lawd_cd = arguments.get("lawd_cd")
        deal_ymd = arguments.get("deal_ymd")
        
        if not lawd_cd or not deal_ymd:
            logger.warning("필수 파라미터 누락 - lawd_cd 또는 deal_ymd")
            return [types.TextContent(
                type="text",
                text="지역코드(lawd_cd)와 계약년월(deal_ymd)이 필요합니다."
            )]
        
        result = await real_estate_api.get_apartment_rent(lawd_cd, deal_ymd)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    elif name == "get_officetel_trade":
        lawd_cd = arguments.get("lawd_cd")
        deal_ymd = arguments.get("deal_ymd")
        
        if not lawd_cd or not deal_ymd:
            logger.warning("필수 파라미터 누락 - lawd_cd 또는 deal_ymd")
            return [types.TextContent(
                type="text",
                text="지역코드(lawd_cd)와 계약년월(deal_ymd)이 필요합니다."
            )]
        
        result = await real_estate_api.get_officetel_trade(lawd_cd, deal_ymd)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    else:
        logger.error(f"알 수 없는 도구 호출: {name}")
        raise ValueError(f"알 수 없는 도구: {name}")

async def main():
    """MCP 서버 실행"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="korean-realestate",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())