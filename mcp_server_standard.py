#!/usr/bin/env python3
"""
표준 MCP 프로토콜 기반 부동산 서버
FastMCP 의존성 없이 순수 MCP SDK만 사용
"""

import asyncio
import sys
import os
import json
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# MCP 라이브러리 임포트
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

class RealEstateServer:
    def __init__(self):
        self.server = Server("real-estate-korea")
        self.api_key = os.getenv("MOLIT_API_KEY")
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not self.api_key:
            print("Warning: MOLIT_API_KEY not found", file=sys.stderr)
        if not self.naver_client_id or not self.naver_client_secret:
            print("Warning: NAVER API keys not found", file=sys.stderr)
    
    def setup_handlers(self):
        """MCP 핸들러 설정"""
        
        # 도구 목록 핸들러
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_apartment_sales",
                    description="아파트 매매 실거래가 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region_code": {"type": "string", "description": "지역코드 (예: 11110)"},
                            "deal_ymd": {"type": "string", "description": "거래년월 (예: 202401)"}
                        },
                        "required": ["region_code", "deal_ymd"]
                    }
                ),
                Tool(
                    name="search_nearby_facilities",
                    description="주변 편의시설 검색",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "address": {"type": "string", "description": "검색할 주소"},
                            "radius": {"type": "number", "description": "검색 반경(m)", "default": 1000},
                            "category": {"type": "string", "description": "시설 종류", "default": "편의점"}
                        },
                        "required": ["address"]
                    }
                ),
                Tool(
                    name="comprehensive_recommendation",
                    description="종합 부동산 추천 분석",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {"type": "string", "description": "매물 주소"},
                            "price": {"type": "number", "description": "매매가격(만원)"},
                            "area": {"type": "number", "description": "전용면적(㎡)"},
                            "floor": {"type": "integer", "description": "층수"},
                            "total_floor": {"type": "integer", "description": "총층수"},
                            "building_year": {"type": "integer", "description": "건축년도"},
                            "property_type": {"type": "string", "description": "매물종류"},
                            "deal_type": {"type": "string", "description": "거래종류"},
                            "user_preference": {"type": "string", "description": "사용자 성향"}
                        },
                        "required": ["address", "price", "area", "floor", "total_floor", "building_year"]
                    }
                )
            ]
        
        # 도구 호출 핸들러
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "get_apartment_sales":
                    result = await self.get_apartment_sales(**arguments)
                elif name == "search_nearby_facilities":
                    result = await self.search_nearby_facilities(**arguments)
                elif name == "comprehensive_recommendation":
                    result = await self.comprehensive_recommendation(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text", 
                    text=f"Error: {str(e)}"
                )]
    
    async def get_apartment_sales(self, region_code: str, deal_ymd: str) -> Dict[str, Any]:
        """아파트 매매 실거래가 조회"""
        if not self.api_key:
            return {"error": "MOLIT_API_KEY not configured"}
        
        url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
        params = {
            "serviceKey": self.api_key,
            "LAWD_CD": region_code,
            "DEAL_YMD": deal_ymd,
            "numOfRows": 100,
            "pageNo": 1
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                
            if response.status_code != 200:
                return {"error": f"API request failed: {response.status_code}"}
            
            # XML 파싱
            root = ET.fromstring(response.text)
            items = []
            
            for item in root.findall(".//item"):
                items.append({
                    "아파트": item.find("아파트").text if item.find("아파트") is not None else "",
                    "거래금액": item.find("거래금액").text if item.find("거래금액") is not None else "",
                    "건축년도": item.find("건축년도").text if item.find("건축년도") is not None else "",
                    "년": item.find("년").text if item.find("년") is not None else "",
                    "월": item.find("월").text if item.find("월") is not None else "",
                    "일": item.find("일").text if item.find("일") is not None else "",
                    "전용면적": item.find("전용면적").text if item.find("전용면적") is not None else "",
                    "층": item.find("층").text if item.find("층") is not None else "",
                    "법정동": item.find("법정동").text if item.find("법정동") is not None else "",
                    "지번": item.find("지번").text if item.find("지번") is not None else ""
                })
            
            return {
                "success": True,
                "data": items,
                "total_count": len(items),
                "region_code": region_code,
                "deal_ymd": deal_ymd
            }
            
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def search_nearby_facilities(self, address: str, radius: int = 1000, category: str = "편의점") -> Dict[str, Any]:
        """주변 편의시설 검색"""
        if not self.naver_client_id or not self.naver_client_secret:
            return {"error": "NAVER API keys not configured"}
        
        try:
            # 네이버 지도 API로 좌표 변환
            geocode_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.naver_client_id,
                "X-NCP-APIGW-API-KEY": self.naver_client_secret
            }
            
            async with httpx.AsyncClient() as client:
                geocode_response = await client.get(
                    geocode_url,
                    headers=headers,
                    params={"query": address},
                    timeout=30.0
                )
            
            if geocode_response.status_code != 200:
                return {"error": f"Geocoding failed: {geocode_response.status_code}"}
            
            geocode_data = geocode_response.json()
            if not geocode_data.get("addresses"):
                return {"error": "Address not found"}
            
            location = geocode_data["addresses"][0]
            lat = float(location["y"])
            lng = float(location["x"])
            
            # 주변 시설 검색
            search_url = "https://naveropenapi.apigw.ntruss.com/map-place/v1/search"
            
            async with httpx.AsyncClient() as client:
                search_response = await client.get(
                    search_url,
                    headers=headers,
                    params={
                        "query": category,
                        "coordinate": f"{lng},{lat}",
                        "radius": radius
                    },
                    timeout=30.0
                )
            
            if search_response.status_code != 200:
                return {"error": f"Search failed: {search_response.status_code}"}
            
            search_data = search_response.json()
            places = search_data.get("places", [])
            
            return {
                "success": True,
                "data": {
                    "center_location": {"lat": lat, "lng": lng},
                    "places": places[:10],  # 최대 10개만 반환
                    "total_count": len(places)
                },
                "address": address,
                "category": category,
                "radius": radius
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def comprehensive_recommendation(self, **kwargs) -> Dict[str, Any]:
        """종합 추천 분석"""
        try:
            # 간단한 점수 계산 로직
            price = kwargs.get("price", 0)
            area = kwargs.get("area", 0)
            floor = kwargs.get("floor", 0)
            total_floor = kwargs.get("total_floor", 1)
            building_year = kwargs.get("building_year", 2000)
            
            # 가격 점수 (면적당 가격 기준)
            price_per_sqm = price * 10000 / area if area > 0 else 0
            price_score = max(0, min(100, 100 - (price_per_sqm - 50000000) / 1000000))
            
            # 층수 점수
            floor_ratio = floor / total_floor if total_floor > 0 else 0
            floor_score = max(0, min(100, floor_ratio * 100))
            
            # 건축년도 점수
            current_year = datetime.now().year
            building_age = current_year - building_year
            age_score = max(0, min(100, 100 - building_age * 2))
            
            # 종합 점수
            total_score = (price_score + floor_score + age_score) / 3
            
            # 등급 결정
            if total_score >= 90:
                grade = "A+"
            elif total_score >= 80:
                grade = "A"
            elif total_score >= 70:
                grade = "B+"
            elif total_score >= 60:
                grade = "B"
            else:
                grade = "C"
            
            return {
                "success": True,
                "data": {
                    "property_info": kwargs,
                    "evaluation": {
                        "total_score": round(total_score, 1),
                        "grade": grade,
                        "price_score": round(price_score, 1),
                        "floor_score": round(floor_score, 1),
                        "age_score": round(age_score, 1)
                    },
                    "recommendation": {
                        "recommended": total_score >= 70,
                        "pros": ["가격 경쟁력 양호"] if price_score >= 70 else [],
                        "cons": ["건물 노후도 높음"] if age_score < 60 else [],
                        "reason": f"종합 점수 {total_score:.1f}점으로 {'추천' if total_score >= 70 else '보류'} 매물입니다"
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

async def main():
    """메인 함수"""
    real_estate_server = RealEstateServer()
    real_estate_server.setup_handlers()
    
    # 서버 실행
    async with real_estate_server.server.run_stdio() as streams:
        await real_estate_server.server.run_loop(streams[0], streams[1])

if __name__ == "__main__":
    asyncio.run(main())