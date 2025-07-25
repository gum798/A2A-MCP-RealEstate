#!/usr/bin/env python3
"""
FastMCP를 사용한 한국 부동산 가격 조회 MCP 서버 (간단 버전)
"""

from fastmcp import FastMCP
import httpx
from typing import Optional
from datetime import datetime

# FastMCP 서버 생성 - 한 줄로 끝!
mcp = FastMCP("Korean Real Estate")

# 국토교통부 API 설정
MOLIT_API_KEY = "aK73WEaxtJKAMoRuruK4ToXJIXqSVlIRybXr0PnJ0BgNs+/zL+ZAF2SpM93dpHOakprT1HTw/NfpzAFNzpt36A=="
BASE_URL = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc"

# 단순히 함수에 데코레이터만 추가하면 MCP 도구가 됨!
@mcp.tool()
async def get_apartment_trade(lawd_cd: str, deal_ymd: str) -> dict:
    """
    아파트 매매 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
    
    Returns:
        아파트 매매 실거래가 데이터
    """
    endpoint = f"{BASE_URL}/getRTMSDataSvcAptTradeDev"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 100,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            # 간단한 XML 파싱 (실제로는 더 정교하게 구현)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            items = []
            
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                items.append(item_data)
            
            return {
                "success": True,
                "data": items,
                "total_count": len(items),
                "message": f"아파트 매매 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "조회 중 오류가 발생했습니다."
            }

@mcp.tool()
async def get_apartment_rent(lawd_cd: str, deal_ymd: str) -> dict:
    """
    아파트 전월세 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리)
        deal_ymd: 계약년월 (YYYYMM)
    
    Returns:
        아파트 전월세 실거래가 데이터
    """
    endpoint = f"{BASE_URL}/getRTMSDataSvcAptRent"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 100,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            items = []
            
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                items.append(item_data)
            
            return {
                "success": True,
                "data": items,
                "total_count": len(items),
                "message": f"아파트 전월세 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "조회 중 오류가 발생했습니다."
            }

@mcp.tool()
async def get_officetel_trade(lawd_cd: str, deal_ymd: str) -> dict:
    """
    오피스텔 매매 실거래가 조회
    
    Args:
        lawd_cd: 지역코드 (5자리)
        deal_ymd: 계약년월 (YYYYMM)
    
    Returns:
        오피스텔 매매 실거래가 데이터
    """
    endpoint = f"{BASE_URL}/getRTMSDataSvcOffiTrade"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 100,
        "pageNo": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            items = []
            
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                items.append(item_data)
            
            return {
                "success": True,
                "data": items,
                "total_count": len(items),
                "message": f"오피스텔 매매 실거래가 조회 완료 ({lawd_cd}, {deal_ymd})"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "조회 중 오류가 발생했습니다."
            }

# 리소스도 간단하게 추가
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
            "도봉구": "11320"
        },
        "경기도": {
            "수원시": "41110",
            "성남시": "41130",
            "고양시": "41280",
            "용인시": "41460",
            "부천시": "41190"
        }
    }
    
    import json
    return json.dumps(regions, ensure_ascii=False, indent=2)

# 서버 실행 - 한 줄로 끝!
if __name__ == "__main__":
    mcp.run()