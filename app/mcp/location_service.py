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
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")  # 네이버 클라이언트 ID
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")  # 네이버 클라이언트 시크릿
TOPIS_API_KEY = os.getenv("TOPIS_API_KEY", "")  # TOPIS 교통정보 API 키

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
            
            # MCP 내부에서 다른 도구 호출 - 실제 함수 호출 방식 (FastMCP 호환)
            coord_result = await address_to_coordinates.fn(address)
            if not coord_result.get("success", False):
                return coord_result
            
            # 결과 구조 확인 후 좌표 추출
            if "data" in coord_result:
                lat = coord_result["data"]["lat"]
                lon = coord_result["data"]["lon"]
            else:
                # 직접 반환된 경우
                lat = coord_result["lat"]
                lon = coord_result["lon"]
        
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
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        # API 키가 없을 때 기본 서울 중심 좌표 사용
        return {
            "success": True,
            "lat": 37.5665,
            "lon": 126.9780,
            "address": address,
            "message": "기본 좌표 사용 (서울 중심)",
            "fallback": True
        }
    
    try:
        # Check if using IAM credentials (need to convert to proper API credentials)
        if NAVER_CLIENT_ID.startswith("ncp_iam_"):
            return {
                "success": False,
                "error": "NCP IAM 자격 증명이 감지되었습니다. Maps API에는 Application API 키가 필요합니다.",
                "message": "네이버 클라우드 플랫폼 콘솔에서 Maps → Application 등록 후 Client ID/Secret을 발급받아 사용해주세요."
            }
        
        url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
        headers = {
            "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
        }
        params = {"query": address}
        
        # 로컬 디버깅용 URL 로깅
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] API 호출 URL: {url}")
            print(f"[DEBUG] 파라미터: {params}")
            
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("addresses"):
                return {
                    "success": False,
                    "error": "주소를 찾을 수 없습니다",
                    "message": f"'{address}' 주소 검색 결과가 없습니다"
                }
            
            # 첫 번째 결과 사용
            result = data["addresses"][0]
            
            return {
                "success": True,
                "data": {
                    "address": result.get("jibunAddress", address),
                    "road_address": result.get("roadAddress", ""),
                    "lat": float(result["y"]),
                    "lon": float(result["x"]),
                    "region": {
                        "region_1depth_name": result.get("addressElements", [{}])[0].get("longName", ""),
                        "region_2depth_name": result.get("addressElements", [{}])[1].get("longName", "") if len(result.get("addressElements", [])) > 1 else "",
                        "region_3depth_name": result.get("address", {}).get("region_3depth_name", "")
                    }
                },
                "message": "주소를 좌표로 변환했습니다"
            }
            
    except Exception as e:
        # API 인증 실패 시 기본 좌표 반환
        return {
            "success": True,
            "lat": 37.5665,
            "lon": 126.9780,
            "address": address,
            "message": f"API 오류로 기본 좌표 사용: {str(e)}",
            "fallback": True
        }

@mcp.tool()
async def find_nearby_facilities(lat: float = None, lon: float = None, address: str = "", category: str = "편의점", radius: int = 1000) -> Dict[str, Any]:
    """
    주변 편의시설 검색
    
    Args:
        lat: 위도 (선택사항)
        lon: 경도 (선택사항)
        address: 주소 (좌표가 없을 경우 주소로 좌표 변환)
        category: 시설 카테고리 (편의점, 병원, 학교, 마트, 공원 등)
        radius: 검색 반경 (미터, 기본값: 1000m)
    
    Returns:
        주변 편의시설 정보
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        # API 키가 없을 때 기본 편의시설 데이터 반환
        mock_facilities = [
            {"name": f"샘플 {category} 1", "distance": 200, "type": category, "address": "서울시 중구"},
            {"name": f"샘플 {category} 2", "distance": 350, "type": category, "address": "서울시 중구"},
            {"name": f"샘플 {category} 3", "distance": 500, "type": category, "address": "서울시 중구"}
        ]
        return {
            "success": True,
            "data": {
                "query_location": {
                    "address": address if address else "기본 위치",
                    "lat": lat if lat else 37.5665,
                    "lon": lon if lon else 126.9780
                },
                "facilities": mock_facilities,
                "total_count": len(mock_facilities)
            },
            "message": f"API 키 없음으로 샘플 {category} {len(mock_facilities)}개 반환",
            "fallback": True
        }
    
    # Check if using IAM credentials (need to convert to proper API credentials)
    if NAVER_CLIENT_ID.startswith("ncp_iam_"):
        return {
            "success": False,
            "error": "NCP IAM 자격 증명이 감지되었습니다. Maps API에는 Application API 키가 필요합니다.",
            "message": "네이버 클라우드 플랫폼 콘솔에서 Maps → Application 등록 후 Client ID/Secret을 발급받아 사용해주세요."
        }
    
    # 좌표가 없으면 주소로 좌표 변환
    if lat is None or lon is None:
        if not address:
            return {
                "success": False,
                "error": "주소 또는 좌표 정보가 필요합니다",
                "message": "address 또는 lat, lon 파라미터를 제공해주세요"
            }
        
        # MCP 내부에서 다른 도구 호출 - 실제 함수 호출 방식 (FastMCP 호환)
        coord_result = await address_to_coordinates.fn(address)
        if not coord_result.get("success", False):
            return coord_result
        
        # 결과 구조 확인 후 좌표 추출
        if "data" in coord_result:
            lat = coord_result["data"]["lat"]
            lon = coord_result["data"]["lon"]
        else:
            # 직접 반환된 경우
            lat = coord_result["lat"]
            lon = coord_result["lon"]
    
    try:
        url = "https://naveropenapi.apigw.ntruss.com/map-place/v1/search"
        headers = {
            "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
        }
        
        # 카테고리 한글명 매핑 (네이버는 한글 검색어 사용)
        category_mapping = {
            "편의점": "편의점",
            "마트": "마트", 
            "대형마트": "대형마트",
            "병원": "병원",
            "약국": "약국",
            "학교": "학교",
            "은행": "은행",
            "주유소": "주유소",
            "지하철역": "지하철역",
            "버스정류장": "버스정류장",
            "공원": "공원",
            "관광명소": "관광명소",
            "음식점": "음식점",
            "카페": "카페"
        }
        
        search_query = category_mapping.get(category, "편의점")  # 기본값: 편의점
        
        params = {
            "query": search_query,
            "coordinate": f"{lon},{lat}",
            "radius": radius,
            "sort": "distance"
        }
        
        # 로컬 디버깅용 URL 로깅
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] API 호출 URL: {url}")
            print(f"[DEBUG] 파라미터: {params}")
            
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            facilities = []
            for place in data.get("places", []):
                facility = {
                    "name": place.get("name", ""),
                    "category": place.get("category", [category]),
                    "address": place.get("address", ""),
                    "road_address": place.get("roadAddress", ""),
                    "phone": place.get("tel", ""),
                    "distance": calculate_distance(lat, lon, float(place.get("y", 0)), float(place.get("x", 0))) * 1000,  # km를 m로 변환
                    "coordinates": {
                        "lat": float(place.get("y", 0)),
                        "lon": float(place.get("x", 0))
                    },
                    "place_url": place.get("bizhourInfo", "")
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
        # API 오류 시 기본 편의시설 데이터 반환
        mock_facilities = [
            {"name": f"기본 {category} 1", "distance": 300, "type": category, "address": "주변 지역"},
            {"name": f"기본 {category} 2", "distance": 600, "type": category, "address": "주변 지역"}
        ]
        return {
            "success": True,
            "data": {
                "query_location": {
                    "address": address if address else "기본 위치",
                    "lat": lat if lat else 37.5665,
                    "lon": lon if lon else 126.9780
                },
                "facilities": mock_facilities,
                "total_count": len(mock_facilities)
            },
            "message": f"API 오류로 기본 {category} {len(mock_facilities)}개 반환: {str(e)}",
            "fallback": True
        }

@mcp.tool()
async def calculate_location_score(subway_distance: float, facilities_count: int, park_distance: float = None) -> Dict[str, Any]:
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

@mcp.tool()
async def get_realtime_traffic_info(start_lat: float, start_lon: float, end_lat: float, end_lon: float, transport_type: str = "transit") -> Dict[str, Any]:
    """
    실시간 교통 정보 조회 (TOPIS API)
    
    Args:
        start_lat: 출발지 위도
        start_lon: 출발지 경도
        end_lat: 도착지 위도
        end_lon: 도착지 경도
        transport_type: 교통수단 (transit: 대중교통, driving: 자동차, walking: 도보)
    
    Returns:
        실시간 교통 정보 (소요시간, 경로, 요금 등)
    """
    try:
        # 도보 경로는 API 키 없이도 계산 가능
        if transport_type == "walking":
            distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)
            walking_time = int(distance / 4.5 * 60)  # 4.5km/h 도보 속도, distance는 이미 km
            
            return {
                "success": True,
                "data": {
                    "transport_type": "walking",
                    "distance_km": distance,
                    "duration_minutes": walking_time,
                    "route_summary": f"도보 {distance}km, 약 {walking_time}분 소요",
                    "paths": [
                        {
                            "type": "walking",
                            "distance": distance * 1000,
                            "duration": walking_time,
                            "start_location": {"lat": start_lat, "lon": start_lon},
                            "end_location": {"lat": end_lat, "lon": end_lon}
                        }
                    ]
                },
                "message": f"도보 경로 안내: {distance}km, {walking_time}분"
            }
        
        # TOPIS API가 필요한 경우 API 키 확인
        if not TOPIS_API_KEY:
            # API 키가 없으면 mock 데이터 반환
            distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)
            
            if transport_type == "transit":
                estimated_time = int(distance * 30)  # 대중교통 평균 30분/km
                return {
                    "success": True,
                    "data": {
                        "transport_type": "transit",
                        "routes": [
                            {
                                "total_time": f"{estimated_time}분",
                                "total_distance": f"{distance:.1f}km",
                                "fare": "1370원",
                                "transfer_count": "1",
                                "route_type": "지하철+버스"
                            }
                        ],
                        "mock_data": True,
                        "query_time": datetime.now().isoformat()
                    },
                    "message": f"예상 대중교통 시간: {estimated_time}분 (실제 API 연동 필요)"
                }
            elif transport_type == "driving":
                estimated_time = int(distance * 15)  # 자동차 평균 15분/km
                return {
                    "success": True,
                    "data": {
                        "transport_type": "driving",
                        "total_time_minutes": estimated_time,
                        "total_distance_km": distance,
                        "toll_fee": int(distance * 500),  # 예상 통행료
                        "traffic_condition": "평균 교통량 기준",
                        "mock_data": True,
                        "query_time": datetime.now().isoformat()
                    },
                    "message": f"예상 자동차 시간: {estimated_time}분 (실제 API 연동 필요)"
                }
        
        # TOPIS API 엔드포인트 (예시 - 실제 API 문서 확인 필요)
        base_url = "http://openapi.topis.co.kr/openapi/service"
        
        if transport_type == "transit":
            # 대중교통 경로 검색
            url = f"{base_url}/transitRoute"
            params = {
                "serviceKey": TOPIS_API_KEY,
                "startX": start_lon,
                "startY": start_lat,
                "endX": end_lon,
                "endY": end_lat,
                "reqDttm": datetime.now().strftime("%Y%m%d%H%M%S"),
                "numOfRows": 5,
                "pageNo": 1
            }
        elif transport_type == "driving":
            # 자동차 경로 검색
            url = f"{base_url}/drivingRoute"
            params = {
                "serviceKey": TOPIS_API_KEY,
                "startX": start_lon,
                "startY": start_lat,
                "endX": end_lon,
                "endY": end_lat,
                "reqDttm": datetime.now().strftime("%Y%m%d%H%M%S"),
                "option": "trafast"  # 교통량 고려 최단시간
            }
        
        # 로컬 디버깅용 URL 로깅
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] TOPIS API 호출 URL: {url}")
            print(f"[DEBUG] 파라미터: {params}")
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # XML 응답을 JSON으로 파싱 (TOPIS API는 XML 응답)
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(response.text)
            
            # 응답 파싱 (실제 TOPIS API 응답 구조에 맞게 수정 필요)
            if transport_type == "transit":
                routes = []
                for item in root.findall(".//item"):
                    route_info = {
                        "total_time": item.find("totalTime").text if item.find("totalTime") is not None else "N/A",
                        "total_distance": item.find("totalDistance").text if item.find("totalDistance") is not None else "N/A",
                        "fare": item.find("fare").text if item.find("fare") is not None else "N/A",
                        "transfer_count": item.find("transferCount").text if item.find("transferCount") is not None else "0",
                        "route_type": "대중교통"
                    }
                    routes.append(route_info)
                
                return {
                    "success": True,
                    "data": {
                        "transport_type": "transit",
                        "routes": routes[:3],  # 상위 3개 경로
                        "query_time": datetime.now().isoformat(),
                        "start_location": {"lat": start_lat, "lon": start_lon},
                        "end_location": {"lat": end_lat, "lon": end_lon}
                    },
                    "message": f"대중교통 경로 {len(routes)}개를 찾았습니다"
                }
            
            elif transport_type == "driving":
                # 자동차 경로 파싱
                total_time = root.find(".//totalTime")
                total_distance = root.find(".//totalDistance")
                toll_fee = root.find(".//tollFee")
                
                return {
                    "success": True,
                    "data": {
                        "transport_type": "driving",
                        "total_time_minutes": int(total_time.text) if total_time is not None else 0,
                        "total_distance_km": float(total_distance.text) / 1000 if total_distance is not None else 0,
                        "toll_fee": int(toll_fee.text) if toll_fee is not None else 0,
                        "traffic_condition": "실시간 교통량 반영",
                        "query_time": datetime.now().isoformat(),
                        "start_location": {"lat": start_lat, "lon": start_lon},
                        "end_location": {"lat": end_lat, "lon": end_lon}
                    },
                    "message": "자동차 경로 안내가 완료되었습니다"
                }
            
    except Exception as e:
        # API 키가 없거나 API 호출 실패 시 mock 데이터 반환
        distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)
        
        if transport_type == "transit":
            estimated_time = int(distance * 30)  # 대중교통 평균 30분/km
            return {
                "success": True,
                "data": {
                    "transport_type": "transit",
                    "routes": [
                        {
                            "total_time": f"{estimated_time}분",
                            "total_distance": f"{distance:.1f}km",
                            "fare": "1370원",
                            "transfer_count": "1",
                            "route_type": "지하철+버스"
                        }
                    ],
                    "mock_data": True,
                    "query_time": datetime.now().isoformat()
                },
                "message": f"예상 대중교통 시간: {estimated_time}분 (실제 API 연동 필요)"
            }
        elif transport_type == "driving":
            estimated_time = int(distance * 15)  # 자동차 평균 15분/km
            return {
                "success": True,
                "data": {
                    "transport_type": "driving",
                    "total_time_minutes": estimated_time,
                    "total_distance_km": distance,
                    "toll_fee": int(distance * 500),  # 예상 통행료
                    "traffic_condition": "평균 교통량 기준",
                    "mock_data": True,
                    "query_time": datetime.now().isoformat()
                },
                "message": f"예상 자동차 시간: {estimated_time}분 (실제 API 연동 필요)"
            }
        
        # 실제 오류인 경우
        return {
            "success": False,
            "error": str(e),
            "message": "실시간 교통 정보 조회 중 오류가 발생했습니다"
        }

@mcp.tool()
async def get_subway_realtime_arrival(station_name: str) -> Dict[str, Any]:
    """
    지하철 실시간 도착 정보 조회
    
    Args:
        station_name: 지하철역명 (예: "강남역", "역삼역")
    
    Returns:
        실시간 지하철 도착 정보
    """
    try:
        # API 키가 없으면 mock 데이터 반환
        if not SEOUL_API_KEY:
            raise Exception("API 키 없음")
            
        # 서울시 지하철 실시간 도착정보 API
        url = "http://swopenapi.seoul.go.kr/api/subway"
        params = {
            "key": SEOUL_API_KEY,
            "type": "json",
            "service": "realtimeArrival",
            "station_name": station_name
        }
        
        # 로컬 디버깅용 URL 로깅
        api_url = f"{url}/{SEOUL_API_KEY}/json/realtimeArrival/1/10/{station_name}"
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] 서울시 지하철 API 호출 URL: {api_url}")
            
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("realtimeArrival"):
                arrivals = []
                for arrival in data["realtimeArrival"]:
                    arrival_info = {
                        "line": arrival.get("subwayId", "").replace("1", "1호선").replace("2", "2호선").replace("3", "3호선").replace("4", "4호선"),
                        "direction": arrival.get("trainLineNm", ""),
                        "arrival_message": arrival.get("arvlMsg2", ""),
                        "arrival_code": arrival.get("arvlCd", ""),
                        "current_station": arrival.get("lstcarAt", ""),
                        "train_express": arrival.get("btrainSttus", "")
                    }
                    arrivals.append(arrival_info)
                
                return {
                    "success": True,
                    "data": {
                        "station_name": station_name,
                        "arrivals": arrivals,
                        "update_time": datetime.now().isoformat(),
                        "total_count": len(arrivals)
                    },
                    "message": f"{station_name} 실시간 도착정보를 조회했습니다"
                }
            else:
                return {
                    "success": False,
                    "error": "실시간 도착정보가 없습니다",
                    "message": f"{station_name}의 실시간 정보를 찾을 수 없습니다"
                }
    
    except Exception as e:
        # Mock 데이터 반환
        mock_arrivals = [
            {
                "line": "2호선",
                "direction": "강남방면",
                "arrival_message": "2분 후 도착",
                "arrival_code": "2",
                "current_station": "선릉역",
                "train_express": "일반"
            },
            {
                "line": "2호선", 
                "direction": "을지로입구방면",
                "arrival_message": "5분 후 도착",
                "arrival_code": "5",
                "current_station": "삼성역",
                "train_express": "일반"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "station_name": station_name,
                "arrivals": mock_arrivals,
                "mock_data": True,
                "update_time": datetime.now().isoformat(),
                "total_count": len(mock_arrivals)
            },
            "message": f"{station_name} 실시간 도착정보 (예시 데이터, 실제 API 연동 필요)"
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
- NAVER_CLIENT_ID: 네이버 클라우드 플랫폼 클라이언트 ID 필요
- NAVER_CLIENT_SECRET: 네이버 클라우드 플랫폼 클라이언트 시크릿 필요
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
    print(f"🔑 네이버 API 키: {'✅ 설정됨' if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET else '❌ 미설정'}")
    print(f"🏛️  서울시 API 키: {'✅ 설정됨' if SEOUL_API_KEY else '❌ 미설정'}")
    print("🚀 FastMCP 서버 시작...")
    mcp.run()