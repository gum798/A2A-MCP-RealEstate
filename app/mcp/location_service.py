#!/usr/bin/env python3
"""
위치 기반 서비스 MCP 서버 (FastMCP)
지하철역 거리, 편의시설 정보 등을 제공
"""

from fastmcp import FastMCP
import httpx
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# FastMCP 서버 생성
mcp = FastMCP("Location Service API")

# API 키 설정
SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "")  # 서울시 공공데이터 API 키
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")  # 카카오 API 키

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 지점 간의 거리를 계산 (하버사인 공식)
    
    Args:
        lat1, lon1: 첫 번째 지점의 위도, 경도
        lat2, lon2: 두 번째 지점의 위도, 경도
    
    Returns:
        거리 (km)
    """
    # 지구의 반지름 (km)
    R = 6371.0
    
    # 라디안으로 변환
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 하버사인 공식
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)

# 서울 지하철역 좌표 데이터 (주요 역들)
SUBWAY_STATIONS = {
    "강남역": {"lat": 37.4979, "lon": 127.0276, "lines": ["2호선", "신분당선"]},
    "역삼역": {"lat": 37.5000, "lon": 127.0366, "lines": ["2호선"]},
    "선릉역": {"lat": 37.5044, "lon": 127.0490, "lines": ["2호선", "분당선"]},
    "삼성역": {"lat": 37.5081, "lon": 127.0631, "lines": ["2호선"]},
    "종각역": {"lat": 37.5703, "lon": 126.9821, "lines": ["1호선"]},
    "명동역": {"lat": 37.5636, "lon": 126.9838, "lines": ["4호선"]},
    "홍대입구역": {"lat": 37.5567, "lon": 126.9244, "lines": ["2호선", "6호선", "공항철도"]},
    "신촌역": {"lat": 37.5551, "lon": 126.9366, "lines": ["2호선"]},
    "이대역": {"lat": 37.5564, "lon": 126.9458, "lines": ["2호선"]},
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
    "왕십리역": {"lat": 37.5618, "lon": 127.0372, "lines": ["2호선", "5호선", "중앙선", "경의중앙선"]},
    "청량리역": {"lat": 37.5802, "lon": 127.0479, "lines": ["1호선", "6호선", "중앙선", "경춘선"]},
    "동대문역": {"lat": 37.5712, "lon": 127.0096, "lines": ["1호선", "4호선"]},
    "동대문역사문화공원역": {"lat": 37.5656, "lon": 127.0077, "lines": ["2호선", "4호선", "5호선"]},
    "을지로3가역": {"lat": 37.5663, "lon": 126.9928, "lines": ["2호선", "3호선"]},
    "충무로역": {"lat": 37.5635, "lon": 126.9936, "lines": ["3호선", "4호선"]},
    "동작역": {"lat": 37.5026, "lon": 126.9397, "lines": ["4호선", "9호선"]},
    "사당역": {"lat": 37.4766, "lon": 126.9814, "lines": ["2호선", "4호선"]},
    "교대역": {"lat": 37.4934, "lon": 127.0146, "lines": ["2호선", "3호선"]},
    "서초역": {"lat": 37.4837, "lon": 127.0108, "lines": ["2호선"]},
    "방배역": {"lat": 37.4813, "lon": 126.9975, "lines": ["2호선"]},
    "선바위역": {"lat": 37.4845, "lon": 126.9971, "lines": ["4호선"]},
    "남태령역": {"lat": 37.4637, "lon": 126.9889, "lines": ["4호선"]},
}

@mcp.tool()
async def find_nearest_subway_stations(address: str, lat: float = None, lon: float = None, limit: int = 5) -> Dict[str, Any]:
    """
    주어진 주소나 좌표에서 가장 가까운 지하철역들을 찾기
    
    Args:
        address: 주소 (좌표가 없을 경우 주소로 좌표 변환)
        lat: 위도 (선택사항)
        lon: 경도 (선택사항)
        limit: 반환할 역의 개수 (기본값: 5)
    
    Returns:
        가장 가까운 지하철역들과 거리 정보
    """
    try:
        # 좌표가 없으면 주소로 좌표 변환
        if lat is None or lon is None:
            if not address:
                return {
                    "success": False,
                    "error": "주소 또는 좌표 정보가 필요합니다",
                    "message": "address 또는 lat, lon 파라미터를 제공해주세요"
                }
            
            # 카카오 API로 주소를 좌표로 변환
            coord_result = await address_to_coordinates(address)
            if not coord_result["success"]:
                return coord_result
            
            lat = coord_result["data"]["lat"]
            lon = coord_result["data"]["lon"]
        
        # 모든 지하철역과의 거리 계산
        distances = []
        for station_name, station_info in SUBWAY_STATIONS.items():
            distance = calculate_distance(lat, lon, station_info["lat"], station_info["lon"])
            distances.append({
                "station_name": station_name,
                "distance_km": distance,
                "distance_m": int(distance * 1000),
                "lines": station_info["lines"],
                "coordinates": {
                    "lat": station_info["lat"],
                    "lon": station_info["lon"]
                }
            })
        
        # 거리순으로 정렬
        distances.sort(key=lambda x: x["distance_km"])
        
        # 상위 N개 반환
        nearest_stations = distances[:limit]
        
        return {
            "success": True,
            "data": {
                "query_location": {
                    "address": address,
                    "lat": lat,
                    "lon": lon
                },
                "nearest_stations": nearest_stations,
                "total_found": len(distances)
            },
            "message": f"가장 가까운 지하철역 {len(nearest_stations)}개를 찾았습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "지하철역 검색 중 오류가 발생했습니다"
        }

@mcp.tool()
async def address_to_coordinates(address: str) -> Dict[str, Any]:
    """
    주소를 좌표(위도, 경도)로 변환
    
    Args:
        address: 변환할 주소
    
    Returns:
        좌표 정보 (위도, 경도)
    """
    if not KAKAO_API_KEY:
        return {
            "success": False,
            "error": "카카오 API 키가 설정되지 않았습니다",
            "message": "KAKAO_API_KEY 환경변수를 설정해주세요"
        }
    
    try:
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": address}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("documents"):
                return {
                    "success": False,
                    "error": "주소를 찾을 수 없습니다",
                    "message": f"'{address}' 주소 검색 결과가 없습니다"
                }
            
            # 첫 번째 결과 사용
            result = data["documents"][0]
            
            return {
                "success": True,
                "data": {
                    "address": result.get("address_name", address),
                    "road_address": result.get("road_address", {}).get("address_name", ""),
                    "lat": float(result["y"]),
                    "lon": float(result["x"]),
                    "region": {
                        "region_1depth_name": result.get("address", {}).get("region_1depth_name", ""),
                        "region_2depth_name": result.get("address", {}).get("region_2depth_name", ""),
                        "region_3depth_name": result.get("address", {}).get("region_3depth_name", "")
                    }
                },
                "message": "주소를 좌표로 변환했습니다"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "주소 변환 중 오류가 발생했습니다"
        }

@mcp.tool()
async def find_nearby_facilities(lat: float, lon: float, category: str = "편의점", radius: int = 1000) -> Dict[str, Any]:
    """
    주변 편의시설 검색
    
    Args:
        lat: 위도
        lon: 경도
        category: 시설 카테고리 (편의점, 병원, 학교, 마트, 공원 등)
        radius: 검색 반경 (미터, 기본값: 1000m)
    
    Returns:
        주변 편의시설 정보
    """
    if not KAKAO_API_KEY:
        return {
            "success": False,
            "error": "카카오 API 키가 설정되지 않았습니다",
            "message": "KAKAO_API_KEY 환경변수를 설정해주세요"
        }
    
    try:
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        
        # 카테고리 코드 매핑
        category_codes = {
            "편의점": "CS2",
            "마트": "MT1", 
            "대형마트": "MT1",
            "병원": "HP8",
            "약국": "PM9",
            "학교": "SC4",
            "은행": "BK9",
            "주유소": "OL7",
            "지하철역": "SW8",
            "버스정류장": "SW8",
            "공원": "AT4",
            "관광명소": "AT4",
            "음식점": "FD6",
            "카페": "CE7"
        }
        
        category_code = category_codes.get(category, "CS2")  # 기본값: 편의점
        
        params = {
            "category_group_code": category_code,
            "x": lon,
            "y": lat,
            "radius": radius,
            "sort": "distance"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            facilities = []
            for place in data.get("documents", []):
                facility = {
                    "name": place.get("place_name", ""),
                    "category": place.get("category_name", ""),
                    "address": place.get("address_name", ""),
                    "road_address": place.get("road_address_name", ""),
                    "phone": place.get("phone", ""),
                    "distance": int(place.get("distance", 0)),
                    "coordinates": {
                        "lat": float(place["y"]),
                        "lon": float(place["x"])
                    },
                    "place_url": place.get("place_url", "")
                }
                facilities.append(facility)
            
            return {
                "success": True,
                "data": {
                    "query": {
                        "category": category,
                        "lat": lat,
                        "lon": lon,
                        "radius": radius
                    },
                    "facilities": facilities,
                    "total_count": len(facilities)
                },
                "message": f"{category} {len(facilities)}개를 찾았습니다"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "편의시설 검색 중 오류가 발생했습니다"
        }

@mcp.tool()
def calculate_location_score(subway_distance: float, facilities_count: int, park_distance: float = None) -> Dict[str, Any]:
    """
    위치 점수 계산 (교통편, 편의성 등을 종합)
    
    Args:
        subway_distance: 가장 가까운 지하철역까지의 거리 (km)
        facilities_count: 반경 1km 내 편의시설 개수
        park_distance: 가장 가까운 공원까지의 거리 (km, 선택사항)
    
    Returns:
        위치 점수 및 세부 평가
    """
    try:
        # 교통 점수 (지하철 거리 기반)
        if subway_distance <= 0.5:
            transport_score = 100
        elif subway_distance <= 1.0:
            transport_score = 80
        elif subway_distance <= 1.5:
            transport_score = 60
        elif subway_distance <= 2.0:
            transport_score = 40
        else:
            transport_score = 20
        
        # 편의성 점수 (편의시설 개수 기반)
        if facilities_count >= 50:
            convenience_score = 100
        elif facilities_count >= 30:
            convenience_score = 80
        elif facilities_count >= 20:
            convenience_score = 60
        elif facilities_count >= 10:
            convenience_score = 40
        else:
            convenience_score = 20
        
        # 환경 점수 (공원 거리 기반)
        environment_score = 50  # 기본값
        if park_distance is not None:
            if park_distance <= 0.3:
                environment_score = 100
            elif park_distance <= 0.5:
                environment_score = 80
            elif park_distance <= 1.0:
                environment_score = 60
            elif park_distance <= 1.5:
                environment_score = 40
            else:
                environment_score = 20
        
        # 종합 점수 계산 (가중평균)
        total_score = (transport_score * 0.4 + convenience_score * 0.35 + environment_score * 0.25)
        
        # 등급 결정
        if total_score >= 90:
            grade = "A+"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B+"
        elif total_score >= 60:
            grade = "B"
        elif total_score >= 50:
            grade = "C+"
        else:
            grade = "C"
        
        return {
            "success": True,
            "data": {
                "total_score": round(total_score, 1),
                "grade": grade,
                "detail_scores": {
                    "transport": {
                        "score": transport_score,
                        "subway_distance_km": subway_distance,
                        "evaluation": "매우우수" if transport_score >= 80 else "우수" if transport_score >= 60 else "보통" if transport_score >= 40 else "미흡"
                    },
                    "convenience": {
                        "score": convenience_score,
                        "facilities_count": facilities_count,
                        "evaluation": "매우우수" if convenience_score >= 80 else "우수" if convenience_score >= 60 else "보통" if convenience_score >= 40 else "미흡"
                    },
                    "environment": {
                        "score": environment_score,
                        "park_distance_km": park_distance,
                        "evaluation": "매우우수" if environment_score >= 80 else "우수" if environment_score >= 60 else "보통" if environment_score >= 40 else "미흡"
                    }
                }
            },
            "message": f"위치 점수 {total_score:.1f}점 ({grade}) 으로 평가되었습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "위치 점수 계산 중 오류가 발생했습니다"
        }

# 리소스 정의
@mcp.resource("location://subway-stations")
async def get_subway_stations_info() -> str:
    """서울 지하철역 목록 및 좌표 정보"""
    return json.dumps(SUBWAY_STATIONS, ensure_ascii=False, indent=2)

@mcp.resource("location://guide")
async def get_location_guide() -> str:
    """위치 서비스 사용 가이드"""
    guide = """# 위치 기반 서비스 MCP 서버 사용 가이드

## 개요
지하철역 거리, 편의시설 정보, 위치 점수 계산 등을 제공하는 위치 기반 서비스입니다.

## 사용 가능한 도구

### 1. find_nearest_subway_stations
가장 가까운 지하철역들을 찾습니다.
- **address**: 주소 (선택사항)
- **lat**: 위도 (선택사항)
- **lon**: 경도 (선택사항)
- **limit**: 반환할 역의 개수 (기본값: 5)

### 2. address_to_coordinates
주소를 좌표로 변환합니다.
- **address**: 변환할 주소

### 3. find_nearby_facilities  
주변 편의시설을 검색합니다.
- **lat**: 위도
- **lon**: 경도
- **category**: 시설 카테고리 (편의점, 병원, 학교, 마트, 공원 등)
- **radius**: 검색 반경 (미터, 기본값: 1000m)

### 4. calculate_location_score
위치 점수를 계산합니다.
- **subway_distance**: 지하철역까지의 거리 (km)
- **facilities_count**: 편의시설 개수
- **park_distance**: 공원까지의 거리 (km, 선택사항)

## 지원하는 편의시설 카테고리
- 편의점, 마트, 대형마트
- 병원, 약국
- 학교, 은행, 주유소
- 지하철역, 버스정류장
- 공원, 관광명소
- 음식점, 카페

## API 키 설정
- KAKAO_API_KEY: 카카오 개발자 API 키 필요
- SEOUL_API_KEY: 서울시 공공데이터 API 키 (선택사항)

## 위치 점수 평가 기준
- **교통 점수 (40%)**: 지하철역 거리
- **편의성 점수 (35%)**: 편의시설 개수  
- **환경 점수 (25%)**: 공원 거리
"""
    return guide

# 서버 실행
if __name__ == "__main__":
    print("📍 위치 기반 서비스 MCP 서버")
    print(f"🔑 카카오 API 키: {'✅ 설정됨' if KAKAO_API_KEY else '❌ 미설정'}")
    print(f"🏛️  서울시 API 키: {'✅ 설정됨' if SEOUL_API_KEY else '❌ 미설정'}")
    print("🚀 FastMCP 서버 시작...")
    mcp.run()