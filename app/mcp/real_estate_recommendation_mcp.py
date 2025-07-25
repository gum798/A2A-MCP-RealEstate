#!/usr/bin/env python3
"""
부동산 추천 시스템 MCP 서버 (FastMCP)
투자가치와 삶의질 평가를 통한 부동산 추천
"""

from fastmcp import FastMCP
import httpx
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

load_dotenv()

# FastMCP 서버 생성
mcp = FastMCP("Real Estate Recommendation System")

# API 키 설정
MOLIT_API_KEY = os.getenv("MOLIT_API_KEY", "")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

@dataclass
class PropertyInfo:
    """부동산 정보 데이터 클래스"""
    address: str
    price: int  # 만원 단위
    area: float  # 전용면적 (㎡)
    floor: int
    total_floor: int
    building_year: int
    property_type: str  # 아파트, 오피스텔, 연립다세대
    deal_type: str  # 매매, 전세, 월세
    lat: Optional[float] = None
    lon: Optional[float] = None

# 서울 지하철역 좌표 데이터
SUBWAY_STATIONS = {
    "강남역": {"lat": 37.4979, "lon": 127.0276, "lines": ["2호선", "신분당선"]},
    "역삼역": {"lat": 37.5000, "lon": 127.0366, "lines": ["2호선"]},
    "선릉역": {"lat": 37.5044, "lon": 127.0490, "lines": ["2호선", "분당선"]},
    "삼성역": {"lat": 37.5081, "lon": 127.0631, "lines": ["2호선"]},
    "종각역": {"lat": 37.5703, "lon": 126.9821, "lines": ["1호선"]},
    "명동역": {"lat": 37.5636, "lon": 126.9838, "lines": ["4호선"]},
    "홍대입구역": {"lat": 37.5567, "lon": 126.9244, "lines": ["2호선", "6호선", "공항철도"]},
    "신촌역": {"lat": 37.5551, "lon": 126.9366, "lines": ["2호선"]},
    "서울역": {"lat": 37.5547, "lon": 126.9706, "lines": ["1호선", "4호선", "공항철도", "KTX"]},
    "용산역": {"lat": 37.5299, "lon": 126.9646, "lines": ["1호선", "중앙선", "KTX"]},
    "여의도역": {"lat": 37.5219, "lon": 126.9245, "lines": ["5호선", "9호선"]},
    "강서구청역": {"lat": 37.5510, "lon": 126.8495, "lines": ["9호선"]},
    "김포공항역": {"lat": 37.5629, "lon": 126.8014, "lines": ["5호선", "9호선", "공항철도"]},
    "수원역": {"lat": 37.2656, "lon": 127.0011, "lines": ["1호선", "분당선"]},
    "성남시청역": {"lat": 37.4201, "lon": 127.1378, "lines": ["분당선"]},
    "판교역": {"lat": 37.3951, "lon": 127.1116, "lines": ["분당선", "신분당선"]},
    "분당역": {"lat": 37.3896, "lon": 127.1226, "lines": ["분당선"]},
    "가락시장역": {"lat": 37.4926, "lon": 127.1186, "lines": ["3호선", "8호선"]},
    "잠실역": {"lat": 37.5133, "lon": 127.1000, "lines": ["2호선", "8호선"]},
    "건대입구역": {"lat": 37.5403, "lon": 127.0703, "lines": ["2호선", "7호선"]},
}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """하버사인 공식으로 두 지점 간 거리 계산 (km)"""
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)

@mcp.tool()
async def get_real_estate_data(lawd_cd: str, deal_ymd: str, property_type: str = "아파트") -> Dict[str, Any]:
    """
    부동산 실거래가 데이터 조회
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401)
        property_type: 부동산 유형 (아파트, 오피스텔, 연립다세대)
    
    Returns:
        실거래가 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "국토교통부 API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    # 부동산 유형별 API 엔드포인트
    endpoints = {
        "아파트": "getRTMSDataSvcAptTradeDev",
        "오피스텔": "getRTMSDataSvcOffiTrade", 
        "연립다세대": "getRTMSDataSvcRHTrade"
    }
    
    endpoint = f"http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/{endpoints.get(property_type, endpoints['아파트'])}"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            
            # XML 파싱
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            items = []
            
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    if child.text:
                        item_data[child.tag] = child.text.strip()
                if item_data:
                    items.append(item_data)
            
            return {
                "success": True,
                "data": {
                    "property_type": property_type,
                    "items": items,
                    "total_count": len(items),
                    "query": {"lawd_cd": lawd_cd, "deal_ymd": deal_ymd}
                },
                "message": f"{property_type} 실거래가 {len(items)}건을 조회했습니다"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"{property_type} 실거래가 조회 중 오류가 발생했습니다"
        }

@mcp.tool()
async def analyze_location(address: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """
    위치 분석 (지하철역 거리, 편의시설 등)
    
    Args:
        address: 주소
        lat: 위도 (선택사항)
        lon: 경도 (선택사항)
    
    Returns:
        위치 분석 결과
    """
    try:
        # 좌표가 없으면 주소로 변환
        if lat is None or lon is None:
            if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
                return {
                    "success": False,
                    "error": "네이버 API 키가 설정되지 않았습니다",
                    "message": "NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 환경변수를 설정해주세요"
                }
            
            # 주소를 좌표로 변환
            url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
            headers = {
                "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
            }
            params = {"query": address}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("addresses"):
                    return {
                        "success": False,
                        "error": "주소를 찾을 수 없습니다",
                        "message": f"'{address}' 주소 검색 결과가 없습니다"
                    }
                
                result = data["addresses"][0]
                lat = float(result["y"])
                lon = float(result["x"])
        
        # 가장 가까운 지하철역 찾기
        nearest_stations = []
        for station_name, station_info in SUBWAY_STATIONS.items():
            distance = calculate_distance(lat, lon, station_info["lat"], station_info["lon"])
            nearest_stations.append({
                "station_name": station_name,
                "distance_km": distance,
                "distance_m": int(distance * 1000),
                "lines": station_info["lines"]
            })
        
        nearest_stations.sort(key=lambda x: x["distance_km"])
        nearest_5 = nearest_stations[:5]
        
        # 편의시설 개수 (모의 데이터)
        facilities_count = max(10, 50 - int(nearest_5[0]["distance_km"] * 20))
        
        # 공원 거리 (모의 데이터)
        park_distance = min(2.0, nearest_5[0]["distance_km"] * 0.8)
        
        # 위치 점수 계산
        subway_distance = nearest_5[0]["distance_km"]
        location_score = calculate_location_score(subway_distance, facilities_count, park_distance)
        
        return {
            "success": True,
            "data": {
                "coordinates": {"lat": lat, "lon": lon},
                "address": address,
                "nearest_stations": nearest_5,
                "subway_distance": subway_distance,
                "facilities_count": facilities_count,
                "park_distance": park_distance,
                "location_score": location_score
            },
            "message": "위치 분석을 완료했습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "위치 분석 중 오류가 발생했습니다"
        }

def calculate_location_score(subway_distance: float, facilities_count: int, park_distance: float) -> Dict[str, Any]:
    """위치 점수 계산"""
    # 교통 점수
    if subway_distance <= 0.5:
        transport_score = 100
    elif subway_distance <= 1.0:
        transport_score = 80
    elif subway_distance <= 1.5:
        transport_score = 60
    else:
        transport_score = 40
    
    # 편의성 점수
    if facilities_count >= 40:
        convenience_score = 100
    elif facilities_count >= 30:
        convenience_score = 80
    elif facilities_count >= 20:
        convenience_score = 60
    else:
        convenience_score = 40
    
    # 환경 점수
    if park_distance <= 0.3:
        environment_score = 100
    elif park_distance <= 0.5:
        environment_score = 80
    elif park_distance <= 1.0:
        environment_score = 60
    else:
        environment_score = 40
    
    total_score = transport_score * 0.4 + convenience_score * 0.35 + environment_score * 0.25
    
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
        "total_score": round(total_score, 1),
        "grade": grade,
        "detail_scores": {
            "transport": transport_score,
            "convenience": convenience_score,
            "environment": environment_score
        }
    }

@mcp.tool()
async def evaluate_investment_value(
    address: str,
    price: int,
    area: float,
    floor: int,
    total_floor: int,
    building_year: int,
    property_type: str,
    deal_type: str
) -> Dict[str, Any]:
    """
    투자가치 평가
    
    Args:
        address: 주소
        price: 가격 (만원)
        area: 전용면적 (㎡)
        floor: 층수
        total_floor: 총 층수
        building_year: 건축년도
        property_type: 부동산 유형
        deal_type: 거래 유형
    
    Returns:
        투자가치 평가 결과
    """
    try:
        # 위치 분석
        location_result = await analyze_location(address)
        if not location_result["success"]:
            return location_result
        
        location_data = location_result["data"]
        
        # 1. 가격 점수 (평당 가격 기준)
        price_per_pyeong = price / (area / 3.3)
        if address.startswith("서울"):
            if price_per_pyeong <= 8000:
                price_score = 100
            elif price_per_pyeong <= 12000:
                price_score = 80
            elif price_per_pyeong <= 16000:
                price_score = 60
            else:
                price_score = 40
        else:
            if price_per_pyeong <= 3000:
                price_score = 100
            elif price_per_pyeong <= 5000:
                price_score = 80
            elif price_per_pyeong <= 7000:
                price_score = 60
            else:
                price_score = 40
        
        # 2. 면적 점수
        area_pyeong = area / 3.3
        if 20 <= area_pyeong <= 35:
            area_score = 100
        elif 15 <= area_pyeong < 20 or 35 < area_pyeong <= 45:
            area_score = 80
        elif 10 <= area_pyeong < 15 or 45 < area_pyeong <= 60:
            area_score = 60
        else:
            area_score = 40
        
        # 3. 층수 점수
        floor_rate = floor / total_floor
        if 0.3 <= floor_rate <= 0.8:
            floor_score = 100
        elif 0.2 <= floor_rate < 0.3 or 0.8 < floor_rate <= 0.9:
            floor_score = 80
        else:
            floor_score = 60
        
        # 4. 교통 점수
        subway_distance = location_data["subway_distance"]
        if subway_distance <= 0.5:
            transport_score = 100
        elif subway_distance <= 1.0:
            transport_score = 80
        elif subway_distance <= 1.5:
            transport_score = 60
        else:
            transport_score = 40
        
        # 5. 미래 발전 가능성
        current_year = datetime.now().year
        building_age = current_year - building_year
        future_score = 50
        
        if building_age >= 30:
            future_score += 20
        elif building_age >= 20:
            future_score += 10
        
        if subway_distance <= 0.5:
            future_score += 20
        elif subway_distance <= 1.0:
            future_score += 10
        
        future_score = min(future_score, 100)
        
        # 종합 점수
        total_score = (
            price_score * 0.25 +
            area_score * 0.20 +
            floor_score * 0.15 +
            transport_score * 0.25 +
            future_score * 0.15
        )
        
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
                "total_score": round(total_score, 1),
                "grade": grade,
                "detail_scores": {
                    "price_score": price_score,
                    "area_score": area_score,
                    "floor_score": floor_score,
                    "transport_score": transport_score,
                    "future_score": future_score
                },
                "analysis": {
                    "price_per_pyeong": round(price_per_pyeong, 0),
                    "area_pyeong": round(area_pyeong, 1),
                    "floor_rate": round(floor_rate, 2),
                    "building_age": building_age
                },
                "location_data": location_data
            },
            "message": f"투자가치 평가 완료: {total_score:.1f}점 ({grade})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "투자가치 평가 중 오류가 발생했습니다"
        }

@mcp.tool()
async def evaluate_life_quality(
    address: str,
    price: int,
    area: float,
    floor: int,
    total_floor: int,
    building_year: int,
    property_type: str,
    deal_type: str
) -> Dict[str, Any]:
    """
    삶의질가치 평가
    
    Args:
        address: 주소
        price: 가격 (만원)
        area: 전용면적 (㎡)
        floor: 층수
        total_floor: 총 층수
        building_year: 건축년도
        property_type: 부동산 유형
        deal_type: 거래 유형
    
    Returns:
        삶의질가치 평가 결과
    """
    try:
        # 위치 분석
        location_result = await analyze_location(address)
        if not location_result["success"]:
            return location_result
        
        location_data = location_result["data"]
        
        # 1. 환경 점수
        park_distance = location_data["park_distance"]
        environment_score = 50
        if park_distance <= 0.3:
            environment_score += 30
        elif park_distance <= 0.5:
            environment_score += 20
        elif park_distance <= 1.0:
            environment_score += 10
        environment_score = min(environment_score, 100)
        
        # 2. 편의성 점수
        facilities_count = location_data["facilities_count"]
        if facilities_count >= 40:
            convenience_score = 100
        elif facilities_count >= 30:
            convenience_score = 85
        elif facilities_count >= 20:
            convenience_score = 70
        elif facilities_count >= 10:
            convenience_score = 55
        else:
            convenience_score = 40
        
        # 3. 안전 점수
        safety_score = 70
        if floor == 1:
            safety_score -= 10
        elif floor >= 15:
            safety_score -= 5
        safety_score = max(safety_score, 30)
        
        # 4. 교육 점수 (임시)
        education_score = 70
        
        # 5. 문화 점수 (임시)
        culture_score = 65
        
        # 종합 점수
        total_score = (
            environment_score * 0.25 +
            convenience_score * 0.25 +
            safety_score * 0.20 +
            education_score * 0.15 +
            culture_score * 0.15
        )
        
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
                "total_score": round(total_score, 1),
                "grade": grade,
                "detail_scores": {
                    "environment_score": environment_score,
                    "convenience_score": convenience_score,
                    "safety_score": safety_score,
                    "education_score": education_score,
                    "culture_score": culture_score
                },
                "location_data": location_data
            },
            "message": f"삶의질가치 평가 완료: {total_score:.1f}점 ({grade})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "삶의질가치 평가 중 오류가 발생했습니다"
        }

@mcp.tool()
async def recommend_property(
    address: str,
    price: int,
    area: float,
    floor: int,
    total_floor: int,
    building_year: int,
    property_type: str,
    deal_type: str,
    user_preference: str = "균형"
) -> Dict[str, Any]:
    """
    종합 부동산 추천
    
    Args:
        address: 주소
        price: 가격 (만원)
        area: 전용면적 (㎡)
        floor: 층수
        total_floor: 총 층수
        building_year: 건축년도
        property_type: 부동산 유형
        deal_type: 거래 유형
        user_preference: 사용자 성향 (투자, 삶의질, 균형)
    
    Returns:
        종합 추천 결과
    """
    try:
        # 투자가치 평가
        investment_result = await evaluate_investment_value(
            address, price, area, floor, total_floor, building_year, property_type, deal_type
        )
        
        if not investment_result["success"]:
            return investment_result
        
        # 삶의질가치 평가
        life_quality_result = await evaluate_life_quality(
            address, price, area, floor, total_floor, building_year, property_type, deal_type
        )
        
        if not life_quality_result["success"]:
            return life_quality_result
        
        investment_score = investment_result["data"]["total_score"]
        life_quality_score = life_quality_result["data"]["total_score"]
        
        # 사용자 성향에 따른 가중치 적용
        if user_preference == "투자":
            final_score = investment_score * 0.8 + life_quality_score * 0.2
        elif user_preference == "삶의질":
            final_score = investment_score * 0.2 + life_quality_score * 0.8
        else:  # 균형
            final_score = investment_score * 0.5 + life_quality_score * 0.5
        
        if final_score >= 90:
            final_grade = "A+"
        elif final_score >= 80:
            final_grade = "A"
        elif final_score >= 70:
            final_grade = "B+"
        elif final_score >= 60:
            final_grade = "B"
        else:
            final_grade = "C"
        
        # 추천 여부 결정
        recommended = final_score >= 70
        
        # 장단점 분석
        pros = []
        cons = []
        
        if investment_result["data"]["detail_scores"]["transport_score"] >= 80:
            pros.append("교통접근성 우수")
        if life_quality_result["data"]["detail_scores"]["convenience_score"] >= 80:
            pros.append("편의시설 풍부")
        if life_quality_result["data"]["detail_scores"]["environment_score"] >= 80:
            pros.append("주변 환경 쾌적")
        
        if investment_result["data"]["detail_scores"]["transport_score"] < 60:
            cons.append("교통접근성 아쉬움")
        if investment_result["data"]["detail_scores"]["price_score"] < 60:
            cons.append("시세 대비 가격 높음")
        if life_quality_result["data"]["detail_scores"]["convenience_score"] < 60:
            cons.append("편의시설 부족")
        
        return {
            "success": True,
            "data": {
                "property_info": {
                    "address": address,
                    "price": price,
                    "area": area,
                    "floor": f"{floor}/{total_floor}",
                    "building_year": building_year,
                    "property_type": property_type,
                    "deal_type": deal_type
                },
                "evaluation": {
                    "final_score": round(final_score, 1),
                    "final_grade": final_grade,
                    "user_preference": user_preference,
                    "investment_evaluation": investment_result["data"],
                    "life_quality_evaluation": life_quality_result["data"]
                },
                "recommendation": {
                    "recommended": recommended,
                    "pros": pros,
                    "cons": cons,
                    "reason": "투자가치와 삶의질을 종합적으로 분석한 결과입니다"
                },
                "timestamp": datetime.now().isoformat()
            },
            "message": f"부동산 추천 완료: {final_score:.1f}점 ({final_grade}) - {'추천' if recommended else '보류'}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "부동산 추천 중 오류가 발생했습니다"
        }

# 리소스 정의
@mcp.resource("realestate://regions")
async def get_region_codes() -> str:
    """한국 주요 지역 코드 정보"""
    regions = {
        "서울특별시": {
            "강남구": "11680", "강동구": "11740", "강북구": "11305", "강서구": "11500",
            "관악구": "11620", "광진구": "11215", "구로구": "11530", "금천구": "11545",
            "노원구": "11350", "도봉구": "11320", "동대문구": "11230", "동작구": "11590",
            "마포구": "11440", "서대문구": "11410", "서초구": "11650", "성동구": "11200",
            "성북구": "11290", "송파구": "11710", "양천구": "11470", "영등포구": "11560",
            "용산구": "11170", "은평구": "11380", "종로구": "11110", "중구": "11140", "중랑구": "11260"
        },
        "경기도": {
            "수원시": "41110", "성남시": "41130", "고양시": "41280", "용인시": "41460",
            "부천시": "41190", "안산시": "41270", "안양시": "41170", "남양주시": "41360",
            "화성시": "41590", "평택시": "41220"
        }
    }
    return json.dumps(regions, ensure_ascii=False, indent=2)

@mcp.resource("realestate://guide")
async def get_usage_guide() -> str:
    """부동산 추천 시스템 사용 가이드"""
    guide = """# 부동산 추천 시스템 MCP 서버 사용 가이드

## 개요
투자가치와 삶의질 분석을 통한 AI 기반 부동산 추천 시스템입니다.

## 사용 가능한 도구

### 1. get_real_estate_data
부동산 실거래가 데이터를 조회합니다.
- **lawd_cd**: 지역코드 (5자리)
- **deal_ymd**: 계약년월 (YYYYMM)
- **property_type**: 부동산 유형 (아파트, 오피스텔, 연립다세대)

### 2. analyze_location
위치 분석을 수행합니다.
- **address**: 주소
- **lat, lon**: 좌표 (선택사항)

### 3. evaluate_investment_value
투자가치를 평가합니다.
- 가격, 면적, 층수, 교통 접근성, 미래 발전 가능성 분석

### 4. evaluate_life_quality
삶의질가치를 평가합니다.
- 환경, 편의성, 안전, 교육, 문화 요소 분석

### 5. recommend_property
종합 부동산 추천을 제공합니다.
- **user_preference**: 사용자 성향 (투자, 삶의질, 균형)

## 평가 기준

### 투자가치 평가 (가중치)
- 가격 (25%): 시세 대비 합리성
- 면적 (20%): 투자 선호 면적대
- 층수 (15%): 중간층~중상층 선호
- 교통 (25%): 지하철 접근성
- 미래가치 (15%): 재건축, 개발 가능성

### 삶의질 평가 (가중치)
- 환경 (25%): 공원, 녹지 접근성
- 편의성 (25%): 편의시설 개수
- 안전 (20%): 층수, 치안 등
- 교육 (15%): 학교, 학원가 접근성
- 문화 (15%): 문화시설 접근성

## 등급 체계
- A+ (90점 이상): 매우 우수
- A (80-89점): 우수
- B+ (70-79점): 양호
- B (60-69점): 보통
- C (60점 미만): 개선 필요

## API 키 설정
- MOLIT_API_KEY: 국토교통부 공공데이터 API 키
- NAVER_CLIENT_ID: 네이버 클라우드 플랫폼 클라이언트 ID
- NAVER_CLIENT_SECRET: 네이버 클라우드 플랫폼 클라이언트 시크릿
"""
    return guide

# 서버 실행
if __name__ == "__main__":
    print("🏠 부동산 추천 시스템 MCP 서버")
    print(f"🔑 국토교통부 API 키: {'✅ 설정됨' if MOLIT_API_KEY else '❌ 미설정'}")
    print(f"🗺️  네이버 API 키: {'✅ 설정됨' if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET else '❌ 미설정'}")
    print("🚀 FastMCP 서버 시작...")
    mcp.run()