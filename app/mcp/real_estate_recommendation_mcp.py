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
import csv
import io
import re

load_dotenv()

# FastMCP 서버 생성
mcp = FastMCP("Real Estate Recommendation System")

def parse_csv_data(csv_content: str, region_name: str, from_date: str, to_date: str, property_type: str) -> List[Dict[str, Any]]:
    """
    CSV 데이터를 파싱하여 필요한 정보만 추출
    """
    transactions = []
    
    # CSV 헤더 확인 (실제 데이터인지 알림 메시지인지)
    if "실거래가 데이터가 없습니다" in csv_content or len(csv_content.strip()) < 100:
        return []
    
    try:
        # CSV 파싱 시작점 찾기 (헤더가 있는 줄)
        lines = csv_content.split('\n')
        header_line_idx = -1
        
        for i, line in enumerate(lines):
            if 'NO' in line and '거래금액' in line and '전용면적' in line:
                header_line_idx = i
                break
        
        if header_line_idx == -1:
            return []
        
        # 헤더 이후의 데이터만 파싱
        csv_data = '\n'.join(lines[header_line_idx:])
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        for row in csv_reader:
            # 거래금액이 있는 유효한 데이터만 처리
            price_str = row.get('거래금액(만원)', '').strip().replace(',', '').replace('-', '')
            if not price_str or not price_str.isdigit():
                continue
            
            # 전용면적 처리
            area_str = row.get('전용면적(㎡)', '').strip()
            area_float = 0.0
            if area_str:
                try:
                    area_float = float(area_str)
                except:
                    area_float = 0.0
            
            # 층수 처리
            floor_str = row.get('층', '').strip()
            floor_int = 0
            if floor_str and floor_str.isdigit():
                floor_int = int(floor_str)
            
            # 건축년도 처리
            year_str = row.get('건축년도', '').strip()
            year_int = 0
            if year_str and year_str.isdigit():
                year_int = int(year_str)
            
            # 평당 가격 계산 (3.3058㎡ = 1평)
            price_per_pyeong = 0
            if area_float > 0:
                price_per_pyeong = int((int(price_str) * 10000) / (area_float / 3.3058))
            
            transaction = {
                "아파트명": row.get('아파트', '').strip(),
                "전용면적": f"{area_float:.2f}㎡" if area_float > 0 else "",
                "거래금액": f"{int(price_str):,}만원",
                "거래금액_숫자": int(price_str),
                "평당가격": f"{price_per_pyeong:,}원/평" if price_per_pyeong > 0 else "",
                "평당가격_숫자": price_per_pyeong,
                "층": f"{floor_int}층" if floor_int > 0 else "",
                "건축년도": str(year_int) if year_int > 0 else "",
                "건물연식": f"{2025 - year_int}년" if year_int > 0 else "",
                "계약년월": row.get('계약년월', '').strip(),
                "계약일": row.get('계약일', '').strip(),
                "법정동": row.get('법정동', '').strip(),
                "도로명": row.get('도로명', '').strip()
            }
            transactions.append(transaction)
    
    except Exception as e:
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] CSV 파싱 오류: {e}")
        return []
    
    # 거래금액 기준으로 내림차순 정렬
    transactions.sort(key=lambda x: x.get('거래금액_숫자', 0), reverse=True)
    
    return transactions

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
async def get_real_estate_data(lawd_cd: str, deal_ymd: str, property_type: str = "아파트", emd_name: str = "", date_range: str = "", use_xml_api: bool = True) -> Dict[str, Any]:
    """
    부동산 실거래가 데이터 조회 (CSV 다운로드 방식)
    
    Args:
        lawd_cd: 지역코드 (5자리, 예: 11680 - 서울 강남구)
        deal_ymd: 계약년월 (YYYYMM, 예: 202401) 또는 날짜 범위가 있으면 시작년월
        property_type: 부동산 유형 (아파트, 오피스텔, 연립다세대)
        emd_name: 읍면동명 (예: "개포동") - 선택사항
        date_range: 날짜 범위 (예: "2025.06.01~2025.07.30") - 선택사항
    
    Returns:
        실거래가 데이터
    """
    # CSV 다운로드는 API 키가 필요하지 않음
    
    # 부동산 유형별 코드 매핑 (실제 웹페이지 기준)
    thing_codes = {
        "아파트": "A",
        "연립다세대": "B", 
        "오피스텔": "D"
    }
    
    thing_code = thing_codes.get(property_type, "A")
    
    try:
        # XML API 폴백 옵션
        if use_xml_api:
            # 기존 XML API 사용 (API 키 필요)
            api_key = os.getenv("MOLIT_API_KEY")
            if not api_key:
                return {
                    "success": False,
                    "error": "API 키가 설정되지 않았습니다",
                    "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
                }
            
            # XML API 엔드포인트 및 파라미터
            base_url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc"
            
            # 부동산 유형별 서비스 매핑
            service_map = {
                "아파트": "getRTMSDataSvcAptTradeDev",
                "오피스텔": "getRTMSDataSvcOffiTrade", 
                "연립다세대": "getRTMSDataSvcRHTrade"
            }
            service_name = service_map.get(property_type, "getRTMSDataSvcAptTradeDev")
            
            url = f"{base_url}/{service_name}"
            params = {
                "serviceKey": api_key,
                "LAWD_CD": lawd_cd,
                "DEAL_YMD": deal_ymd,
                "numOfRows": 1000,
                "pageNo": 1
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                import xml.etree.ElementTree as ET
                
                # XML 파싱
                root = ET.fromstring(response.text)
                header = root.find('.//header')
                body = root.find('.//body')
                
                if header is not None:
                    result_code = header.find('resultCode')
                    result_msg = header.find('resultMsg')
                    
                    if result_code is not None and result_code.text != "00":
                        return {
                            "success": False,
                            "error": f"API 오류: {result_msg.text if result_msg is not None else 'Unknown error'}",
                            "message": f"{property_type} 실거래가 조회 실패"
                        }
                
                items = []
                if body is not None:
                    items_element = body.find('items')
                    if items_element is not None:
                        for item in items_element.findall('item'):
                            item_data = {}
                            for child in item:
                                if child.text:
                                    item_data[child.tag] = child.text.strip()
                            if item_data:
                                items.append(item_data)
                
                return {
                    "success": True,
                    "data": {
                        "response": {
                            "header": {
                                "resultCode": "00",
                                "resultMsg": "정상"
                            },
                            "body": {
                                "items": items,
                                "numOfRows": len(items),
                                "pageNo": 1,
                                "totalCount": len(items)
                            }
                        }
                    },
                    "message": f"{property_type} {len(items)}건 조회 완료 (XML API)",
                    "source": "XML API"
                }
        
        # 3단계 접근: 세션 설정 -> 데이터 확인 -> CSV 다운로드
        session_url = "https://rt.molit.go.kr/pt/xls/xls.do?mobileAt="
        check_url = "https://rt.molit.go.kr/pt/xls/ptXlsDownDataCheck.do"
        download_url = "https://rt.molit.go.kr/pt/xls/ptXlsCSVDown.do"
        
        # 지역코드와 이름 매핑
        region_mapping = {
            "11680": {
                "sido_code": "11000",
                "sgg_code": "11680", 
                "sido_name": "서울특별시",
                "sgg_name": "강남구",
                "emd_mapping": {
                    "개포동": "10300",
                    "논현동": "10500",
                    "대치동": "10700", 
                    "도곡동": "10800",
                    "삼성동": "11000",
                    "신사동": "11300",
                    "압구정동": "11700",
                    "역삼동": "12000",
                    "청담동": "12200"
                }
            },
            "11500": {
                "sido_code": "11000",
                "sgg_code": "11500",
                "sido_name": "서울특별시", 
                "sgg_name": "강서구",
                "emd_mapping": {}
            }
        }
        
        region_info = region_mapping.get(lawd_cd, {
            "sido_code": lawd_cd[:5] + "0",
            "sgg_code": lawd_cd,
            "sido_name": "서울특별시",
            "sgg_name": "기타",
            "emd_mapping": {}
        })
        
        sido_code = region_info["sido_code"] 
        sgg_code = region_info["sgg_code"]
        sido_name = region_info["sido_name"]
        sgg_name = region_info["sgg_name"]
        
        # EMD 코드와 이름 처리
        emd_code = ""
        emd_name_param = emd_name or ""
        if emd_name and emd_name in region_info["emd_mapping"]:
            emd_code = region_info["emd_mapping"][emd_name]
        
        # 날짜 범위 처리
        if date_range and "~" in date_range:
            # 날짜 범위가 있는 경우 (예: "2025.06.01~2025.07.30")
            start_date, end_date = date_range.split("~")
            from_date = start_date.replace(".", "")  # "20250601"
            to_date = end_date.replace(".", "")      # "20250730"
        else:
            # 기존 방식: 해당 년월의 전체 기간
            year = deal_ymd[:4]
            month = deal_ymd[4:6]
            from_date = f"{year}{month}01"  # 월 첫째 날
            
            # 월의 마지막 날 계산
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            to_date = f"{year}{month}{last_day:02d}"  # 월 마지막 날
        
        # 실제 브라우저와 동일한 파라미터 구성
        params = {
            'srhThingNo': thing_code,  # A: 아파트, B: 연립다세대, D: 오피스텔
            'srhDelngSecd': '1',  # 1: 매매, 2: 전월세
            'srhAddrGbn': '1',  # 1: 지번주소, 2: 도로명주소
            'srhLfstsSecd': '1',  # 누락되었던 파라미터
            'sidoNm': sido_name,  # 시도명 (한글)
            'sggNm': sgg_name,  # 시군구명 (한글)
            'emdNm': emd_name_param,  # 읍면동명 (한글)
            'loadNm': '전체',  # 도로명
            'areaNm': '전체',  # 면적
            'hsmpNm': '전체',  # 단지명
            'mobileAt': '',  # 모바일 구분자
            'srhFromDt': f"{from_date[:4]}-{from_date[4:6]}-{from_date[6:8]}",  # YYYY-MM-DD 형식
            'srhToDt': f"{to_date[:4]}-{to_date[4:6]}-{to_date[6:8]}",  # YYYY-MM-DD 형식  
            'srhNewRonSecd': '',  # 신구분
            'srhSidoCd': sido_code,  # 시도코드
            'srhSggCd': sgg_code,  # 시군구코드
            'srhEmdCd': emd_code,  # 읍면동코드
            'srhRoadNm': '',  # 도로명
            'srhLoadCd': '',  # 도로코드
            'srhHsmpCd': '',  # 단지코드
            'srhArea': '',  # 면적
            'srhFromAmount': '',  # 최소 금액
            'srhToAmount': ''  # 최대 금액
        }
        
        # 로컬 디버깅용 URL 로깅
        if os.getenv("ENVIRONMENT", "production") == "development":
            print(f"[DEBUG] 입력받은 deal_ymd: {deal_ymd}")
            print(f"[DEBUG] date_range: {date_range}")
            print(f"[DEBUG] 계산된 from_date: {from_date}")
            print(f"[DEBUG] 계산된 to_date: {to_date}")
            print(f"[DEBUG] 세션 URL: {session_url}")
            print(f"[DEBUG] 다운로드 URL: {download_url}")
            print(f"[DEBUG] POST 파라미터: {params}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            # 1단계: 메인 페이지 방문하여 세션 설정
            session_response = await client.get(session_url, headers=headers)
            if os.getenv("ENVIRONMENT", "production") == "development":
                print(f"[DEBUG] 1단계 세션 설정 완료: {session_response.status_code}")
            
            # 2단계: 데이터 확인 요청 (실제 브라우저와 동일)
            check_headers = headers.copy()
            check_headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': session_url,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            check_response = await client.post(check_url, data=params, headers=check_headers)
            if os.getenv("ENVIRONMENT", "production") == "development":
                print(f"[DEBUG] 2단계 데이터 확인 완료: {check_response.status_code}")
                print(f"[DEBUG] 확인 응답: {check_response.text[:200]}")
            
            # 3단계: 실제 CSV 다운로드 요청
            download_headers = headers.copy()
            download_headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': session_url,
                'Accept': 'application/octet-stream,text/csv,*/*'
            })
            
            response = await client.post(download_url, data=params, headers=download_headers)
            response.raise_for_status()
            
            # CSV 응답 처리 (인코딩 자동 감지)
            try:
                # 먼저 CP949로 디코딩 시도 (국토교통부 CSV는 보통 CP949)
                csv_content = response.content.decode('cp949')
            except UnicodeDecodeError:
                try:
                    # CP949 실패 시 EUC-KR 시도
                    csv_content = response.content.decode('euc-kr')
                except UnicodeDecodeError:
                    # 그래도 실패하면 UTF-8 사용
                    csv_content = response.text
            
            # 로컬 디버깅용 응답 내용 확인
            if os.getenv("ENVIRONMENT", "production") == "development":
                print(f"[DEBUG] 응답 상태코드: {response.status_code}")
                print(f"[DEBUG] 응답 헤더: {dict(response.headers)}")
                print(f"[DEBUG] 응답 내용 전체 길이: {len(csv_content)}")
                print(f"[DEBUG] Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # 응답이 파일 다운로드인지 확인
                content_disposition = response.headers.get('content-disposition', '')
                if 'attachment' in content_disposition:
                    print(f"[DEBUG] 파일 다운로드 감지: {content_disposition}")
                else:
                    print(f"[DEBUG] 응답 내용 (처음 1000자): {csv_content[:1000]}")
            
            # 응답이 HTML 에러 페이지인지 확인
            if '<html>' in csv_content.lower() or '<!doctype html>' in csv_content.lower():
                return {
                    "success": False,
                    "error": "HTML 에러 페이지 응답",
                    "message": f"{property_type} CSV 다운로드 실패 - 서버에서 HTML 페이지를 반환했습니다"
                }
            
            # CSV 데이터 파싱 및 필터링
            try:
                if csv_content.startswith('\ufeff'):  # BOM 제거
                    csv_content = csv_content[1:]
                
                # 개선된 파싱 함수 사용
                items = parse_csv_data(csv_content, sgg_name, from_date, to_date, property_type)
                        
            except Exception as parse_error:
                if os.getenv("ENVIRONMENT", "production") == "development":
                    print(f"[DEBUG] CSV 파싱 오류: {parse_error}")
                    print(f"[DEBUG] 원본 내용: {csv_content[:500]}")
                
                return {
                    "success": False,
                    "error": f"CSV 파싱 오류: {str(parse_error)}",
                    "message": f"{property_type} CSV 파싱 중 오류가 발생했습니다"
                }
            
            return {
                "success": True,
                "data": {
                    "response": {
                        "header": {
                            "resultCode": "00",
                            "resultMsg": "정상"
                        },
                        "body": {
                            "items": items,
                            "numOfRows": len(items),
                            "pageNo": 1,
                            "totalCount": len(items)
                        }
                    }
                },
                "message": f"{property_type} {len(items)}건 조회 완료 (CSV 방식)",
                "source": "CSV 직접 다운로드"
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

@mcp.tool()
async def get_regional_price_statistics(lawd_cd: str, property_type: str = "아파트", months: int = 12) -> Dict[str, Any]:
    """
    지역별 가격 통계 및 트렌드 분석
    
    Args:
        lawd_cd: 지역코드 (5자리)
        property_type: 부동산 유형 (아파트, 오피스텔, 연립다세대)
        months: 분석할 개월 수 (기본 12개월)
    
    Returns:
        지역별 가격 통계 데이터
    """
    if not MOLIT_API_KEY:
        return {
            "success": False,
            "error": "국토교통부 API 키가 설정되지 않았습니다",
            "message": "MOLIT_API_KEY 환경변수를 설정해주세요"
        }
    
    try:
        from datetime import datetime, timedelta
        import statistics
        
        # 최근 N개월 데이터 수집
        end_date = datetime.now()
        monthly_data = []
        price_data = []
        
        for i in range(months):
            target_date = end_date - timedelta(days=30 * i)
            deal_ymd = target_date.strftime("%Y%m")
            
            # 실거래가 데이터 조회 (MCP 도구에서 원본 함수 호출)
            tool = await mcp.get_tool("get_real_estate_data")
            monthly_result = await tool.fn(lawd_cd, deal_ymd, property_type)
            
            if monthly_result.get("success") and monthly_result.get("data", {}).get("items"):
                items = monthly_result["data"]["items"]
                
                # 가격 데이터 추출 및 정제
                month_prices = []
                for item in items:
                    try:
                        # 거래금액에서 쉼표 제거 후 숫자 변환
                        price_str = item.get("거래금액", "0").replace(",", "").replace(" ", "")
                        if price_str.isdigit():
                            price = int(price_str)
                            if price > 0:  # 유효한 가격만
                                month_prices.append(price)
                                price_data.append({"price": price, "month": deal_ymd})
                    except (ValueError, KeyError):
                        continue
                
                if month_prices:
                    monthly_data.append({
                        "month": deal_ymd,
                        "transaction_count": len(month_prices),
                        "average_price": statistics.mean(month_prices),
                        "median_price": statistics.median(month_prices),
                        "min_price": min(month_prices),
                        "max_price": max(month_prices),
                        "price_std": statistics.stdev(month_prices) if len(month_prices) > 1 else 0
                    })
        
        if not monthly_data:
            return {
                "success": False,
                "error": "분석할 데이터가 없습니다",
                "message": f"{months}개월 기간 내 거래 데이터가 없습니다"
            }
        
        # 전체 통계 계산
        all_prices = [price["price"] for price in price_data]
        total_transactions = len(all_prices)
        
        # 가격 변동률 계산 (최신 월 vs 1년 전)
        price_change_rate = 0
        if len(monthly_data) >= 2:
            latest_avg = monthly_data[0]["average_price"]
            oldest_avg = monthly_data[-1]["average_price"]
            price_change_rate = ((latest_avg - oldest_avg) / oldest_avg) * 100
        
        # 가격 구간별 분포
        price_ranges = {
            "1억 미만": 0,
            "1-3억": 0,
            "3-5억": 0,
            "5-10억": 0,
            "10억 초과": 0
        }
        
        for price in all_prices:
            price_eok = price / 10000  # 만원 -> 억원
            if price_eok < 1:
                price_ranges["1억 미만"] += 1
            elif price_eok < 3:
                price_ranges["1-3억"] += 1
            elif price_eok < 5:
                price_ranges["3-5억"] += 1
            elif price_eok < 10:
                price_ranges["5-10억"] += 1
            else:
                price_ranges["10억 초과"] += 1
        
        # 최신 트렌드 분석 (최근 3개월)
        recent_trend = "안정"
        if len(monthly_data) >= 3:
            recent_prices = [data["average_price"] for data in monthly_data[:3]]
            if recent_prices[0] > recent_prices[2] * 1.05:
                recent_trend = "상승"
            elif recent_prices[0] < recent_prices[2] * 0.95:
                recent_trend = "하락"
        
        return {
            "success": True,
            "data": {
                "region_code": lawd_cd,
                "property_type": property_type,
                "analysis_period": f"{months}개월",
                "summary": {
                    "total_transactions": total_transactions,
                    "average_price": statistics.mean(all_prices) if all_prices else 0,
                    "median_price": statistics.median(all_prices) if all_prices else 0,
                    "price_change_rate": round(price_change_rate, 2),
                    "recent_trend": recent_trend
                },
                "monthly_data": monthly_data,
                "price_distribution": price_ranges,
                "market_analysis": {
                    "volatility": statistics.stdev(all_prices) if len(all_prices) > 1 else 0,
                    "price_stability": "높음" if len(all_prices) > 0 and statistics.stdev(all_prices) / statistics.mean(all_prices) < 0.3 else "보통"
                }
            },
            "message": f"{property_type} {months}개월 시세 분석이 완료되었습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "지역별 가격 통계 분석 중 오류가 발생했습니다"
        }

@mcp.tool()  
async def compare_similar_properties(
    address: str, 
    area: float, 
    building_year: int,
    lawd_cd: str,
    tolerance_area: float = 10.0,
    tolerance_year: int = 5
) -> Dict[str, Any]:
    """
    유사한 조건의 매물 가격 비교 분석
    
    Args:
        address: 비교 대상 주소
        area: 전용면적 (㎡)
        building_year: 건축년도
        lawd_cd: 지역코드
        tolerance_area: 면적 허용 오차 (㎡)
        tolerance_year: 건축년도 허용 오차 (년)
    
    Returns:
        유사 매물 가격 비교 결과
    """
    try:
        from datetime import datetime
        
        # 최근 6개월 데이터 조회
        current_date = datetime.now()
        similar_properties = []
        
        for i in range(6):
            target_date = datetime(current_date.year, current_date.month - i, 1) if current_date.month > i else datetime(current_date.year - 1, current_date.month - i + 12, 1)
            deal_ymd = target_date.strftime("%Y%m")
            
            # 실거래가 데이터 조회
            # MCP 도구에서 원본 함수 호출
            tool = await mcp.get_tool("get_real_estate_data")
            result = await tool.fn(lawd_cd, deal_ymd, "아파트")
            
            if result.get("success") and result.get("data", {}).get("items"):
                items = result["data"]["items"]
                
                for item in items:
                    try:
                        # 면적 비교 (전용면적)
                        item_area = float(item.get("전용면적", "0").replace(",", ""))
                        if abs(item_area - area) <= tolerance_area:
                            
                            # 건축년도 비교
                            item_year = int(item.get("건축년도", "0"))
                            if abs(item_year - building_year) <= tolerance_year:
                                
                                # 가격 정보
                                price_str = item.get("거래금액", "0").replace(",", "").replace(" ", "")
                                if price_str.isdigit():
                                    price = int(price_str)
                                    
                                    similar_properties.append({
                                        "address": item.get("시군구", "") + " " + item.get("번지", ""),
                                        "price": price,
                                        "area": item_area,
                                        "building_year": item_year,
                                        "floor": item.get("층", ""),
                                        "deal_date": item.get("년", "") + "." + item.get("월", "") + "." + item.get("일", ""),
                                        "price_per_pyeong": round(price / (item_area / 3.3)) if item_area > 0 else 0
                                    })
                    except (ValueError, KeyError):
                        continue
        
        if not similar_properties:
            return {
                "success": False,
                "error": "유사한 조건의 매물을 찾을 수 없습니다",
                "message": f"면적 {area}±{tolerance_area}㎡, 건축년도 {building_year}±{tolerance_year}년 조건에 맞는 매물이 없습니다"
            }
        
        # 가격 통계 계산
        prices = [prop["price"] for prop in similar_properties]
        prices_per_pyeong = [prop["price_per_pyeong"] for prop in similar_properties if prop["price_per_pyeong"] > 0]
        
        import statistics
        
        price_stats = {
            "count": len(similar_properties),
            "average_price": statistics.mean(prices),
            "median_price": statistics.median(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "average_price_per_pyeong": statistics.mean(prices_per_pyeong) if prices_per_pyeong else 0,
            "price_range": max(prices) - min(prices)
        }
        
        # 가격 구간별 분포
        price_quartiles = statistics.quantiles(prices, n=4) if len(prices) >= 4 else prices
        
        return {
            "success": True,
            "data": {
                "search_criteria": {
                    "target_area": area,
                    "target_building_year": building_year,
                    "area_tolerance": tolerance_area,
                    "year_tolerance": tolerance_year
                },
                "statistics": price_stats,
                "similar_properties": similar_properties[:10],  # 최대 10개만 반환
                "market_position": {
                    "low_25": price_quartiles[0] if len(price_quartiles) > 0 else prices[0],
                    "median": price_stats["median_price"],
                    "high_75": price_quartiles[2] if len(price_quartiles) > 2 else prices[-1],
                    "recommendation": "시세 대비 적정" if len(prices) > 0 else "데이터 부족"
                }
            },
            "message": f"유사 조건 매물 {len(similar_properties)}건의 비교 분석이 완료되었습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "유사 매물 비교 분석 중 오류가 발생했습니다"
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
    import sys
    print("🏠 부동산 추천 시스템 MCP 서버", file=sys.stderr)
    print(f"🔑 국토교통부 API 키: {'✅ 설정됨' if MOLIT_API_KEY else '❌ 미설정'}", file=sys.stderr)
    print(f"🗺️  네이버 API 키: {'✅ 설정됨' if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET else '❌ 미설정'}", file=sys.stderr)
    print("🚀 FastMCP JSON-RPC 서버 시작 (stdin/stdout)...", file=sys.stderr)
    
    # FastMCP 서버 실행
    mcp.run()