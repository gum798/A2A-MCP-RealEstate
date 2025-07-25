#!/usr/bin/env python3
"""
FastMCP를 사용한 한국 부동산 가격 조회 MCP 서버
국토교통부 공공데이터 API 연동
"""

from fastmcp import FastMCP
import httpx
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# FastMCP 서버 생성 - 한 줄로 끝!
mcp = FastMCP("Korean Real Estate API")

# 국토교통부 API 설정
MOLIT_API_KEY = os.getenv("MOLIT_API_KEY", "")
BASE_URL = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc"

def parse_xml_response(xml_text: str) -> Dict[str, Any]:
    """XML 응답 파싱"""
    try:
        root = ET.fromstring(xml_text)
        items = []
        
        # XML 구조에 따라 파싱
        for item in root.findall('.//item'):
            item_data = {}
            for child in item:
                if child.text:
                    item_data[child.tag] = child.text.strip()
            if item_data:  # 빈 아이템 제외
                items.append(item_data)
        
        return {
            "success": True,
            "items": items,
            "total_count": len(items)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"XML 파싱 실패: {str(e)}",
            "items": [],
            "total_count": 0
        }

@mcp.tool()
async def get_apartment_trade(lawd_cd: str, deal_ymd: str) -> Dict[str, Any]:
    """
    아파트 매매 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
    
    Returns:
        아파트 매매 실거래가 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    endpoint = f"{BASE_URL}/getRTMSDataSvcAptTradeDev"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            result = parse_xml_response(response.text)
            result["message"] = f"아파트 매매 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            result["query"] = {"lawd_cd": lawd_cd, "deal_ymd": deal_ymd}
            
            return result
            
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "요청 시간 초과",
                "message": "API 서버 응답이 지연되고 있습니다"
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP 오류: {e.response.status_code}",
                "message": "API 서버에서 오류 응답을 받았습니다"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "아파트 매매 실거래가 조회 중 오류가 발생했습니다"
            }

@mcp.tool()
async def get_apartment_rent(lawd_cd: str, deal_ymd: str) -> Dict[str, Any]:
    """
    아파트 전월세 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
    
    Returns:
        아파트 전월세 실거래가 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    endpoint = f"{BASE_URL}/getRTMSDataSvcAptRent"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            result = parse_xml_response(response.text)
            result["message"] = f"아파트 전월세 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            result["query"] = {"lawd_cd": lawd_cd, "deal_ymd": deal_ymd}
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "아파트 전월세 실거래가 조회 중 오류가 발생했습니다"
            }

@mcp.tool()
async def get_officetel_trade(lawd_cd: str, deal_ymd: str) -> Dict[str, Any]:
    """
    오피스텔 매매 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
    
    Returns:
        오피스텔 매매 실거래가 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    endpoint = f"{BASE_URL}/getRTMSDataSvcOffiTrade"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            result = parse_xml_response(response.text)
            result["message"] = f"오피스텔 매매 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            result["query"] = {"lawd_cd": lawd_cd, "deal_ymd": deal_ymd}
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "오피스텔 매매 실거래가 조회 중 오류가 발생했습니다"
            }

@mcp.tool()
async def get_villa_trade(lawd_cd: str, deal_ymd: str) -> Dict[str, Any]:
    """
    연립다세대 매매 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
    
    Returns:
        연립다세대 매매 실거래가 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    endpoint = f"{BASE_URL}/getRTMSDataSvcRHTrade"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            result = parse_xml_response(response.text)
            result["message"] = f"연립다세대 매매 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            result["query"] = {"lawd_cd": lawd_cd, "deal_ymd": deal_ymd}
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "연립다세대 매매 실거래가 조회 중 오류가 발생했습니다"
            }

@mcp.tool()
def get_recent_months(months: int = 12) -> Dict[str, Any]:
    """
    최근 N개월의 년월 목록을 반환
    
    Args:
        months: 반환할 개월 수 (기본값: 12)
    
    Returns:
        최근 개월 목록 (YYYYMM 형식)
    """
    try:
        now = datetime.now()
        month_list = []
        
        for i in range(months):
            # i개월 전 계산
            target_date = now - timedelta(days=i*30)
            month_str = target_date.strftime("%Y%m")
            month_name = target_date.strftime("%Y년 %m월")
            
            month_list.append({
                "month_code": month_str,
                "month_name": month_name,
                "year": target_date.year,
                "month": target_date.month
            })
        
        return {
            "success": True,
            "months": month_list,
            "message": f"최근 {months}개월 목록을 생성했습니다"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "개월 목록 생성 중 오류가 발생했습니다"
        }

# 리소스 정의 - 지역 코드 정보
@mcp.resource("realestate://regions")
async def get_region_codes() -> str:
    """한국 주요 지역 코드 정보"""
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
            "평택시": "41220",
            "의정부시": "41150",
            "시흥시": "41390",
            "파주시": "41480",
            "광명시": "41210",
            "김포시": "41570"
        },
        "부산광역시": {
            "해운대구": "26440",
            "부산진구": "26230",
            "동래구": "26260",
            "남구": "26200",
            "연제구": "26470",
            "수영구": "26380",
            "사상구": "26530",
            "기장군": "26710"
        },
        "대구광역시": {
            "중구": "27110",
            "동구": "27140",
            "서구": "27170",
            "남구": "27200",
            "북구": "27230",
            "수성구": "27260",
            "달서구": "27290",
            "달성군": "27710"
        },
        "인천광역시": {
            "중구": "28110",
            "동구": "28140",
            "미추홀구": "28177",
            "연수구": "28185",
            "남동구": "28200",
            "부평구": "28237",
            "계양구": "28245",
            "서구": "28260",
            "강화군": "28710",
            "옹진군": "28720"
        }
    }
    
    return json.dumps(regions, ensure_ascii=False, indent=2)

# 사용 가이드 리소스
@mcp.resource("realestate://guide")
async def get_usage_guide() -> str:
    """부동산 가격 조회 API 사용 가이드"""
    guide = """# 한국 부동산 가격 조회 MCP 서버 사용 가이드

## 개요
국토교통부 공공데이터 API를 활용하여 한국의 부동산 실거래가 정보를 조회할 수 있는 FastMCP 서버입니다.

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

### 4. get_villa_trade
연립다세대 매매 실거래가를 조회합니다.
- **lawd_cd**: 지역코드 (5자리)
- **deal_ymd**: 계약년월 (6자리)

### 5. get_recent_months
최근 N개월의 년월 목록을 반환합니다.
- **months**: 반환할 개월 수 (기본값: 12)

## 지역코드 예시
- 서울 강남구: 11680
- 서울 강서구: 11500
- 경기 수원시: 41110
- 부산 해운대구: 26440

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
- 실거래가 데이터는 통상 1-2개월 지연되어 업데이트됩니다

## API 키 설정
환경변수 MOLIT_API_KEY에 국토교통부 공공데이터포털에서 발급받은 API 키를 설정하세요.
"""
    return guide

# 서버 실행 - 한 줄로 끝!
if __name__ == "__main__":
    print("🏠 한국 부동산 가격 조회 MCP 서버")
    print(f"🔑 API 키 설정: {'✅ 설정됨' if MOLIT_API_KEY else '❌ 미설정'}")
    print("🚀 FastMCP 서버 시작...")
    mcp.run()