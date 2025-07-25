#!/usr/bin/env python3
"""
한국 부동산 가격 조회 MCP 서버 테스트 스크립트
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# 테스트 API 서버 URL
BASE_URL = "http://localhost:8080"

async def test_mcp_endpoints():
    """MCP 엔드포인트 테스트"""
    
    async with httpx.AsyncClient() as client:
        print("=== 한국 부동산 가격 조회 MCP 서버 테스트 ===\n")
        
        # 1. MCP 상태 확인
        print("1. MCP 서버 상태 확인")
        try:
            response = await client.get(f"{BASE_URL}/api/mcp/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 상태: {data['success']}")
                print(f"   📝 메시지: {data['message']}")
                print(f"   🔑 API 키 설정: {data['data']['api_key_configured']}")
                print(f"   🛠️  사용 가능한 도구: {', '.join(data['data']['available_tools'])}")
            else:
                print(f"   ❌ 오류: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 연결 오류: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 2. 지역 코드 조회
        print("2. 지역 코드 정보 조회")
        try:
            response = await client.get(f"{BASE_URL}/api/mcp/regions")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 상태: {data['success']}")
                print("   📍 주요 지역 코드:")
                regions = data['data']
                for city, districts in regions.items():
                    print(f"      {city}:")
                    for district, code in list(districts.items())[:3]:  # 처음 3개만 표시
                        print(f"        - {district}: {code}")
                    if len(districts) > 3:
                        print(f"        - ... (총 {len(districts)}개 지역)")
            else:
                print(f"   ❌ 오류: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 연결 오류: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 3. 사용 가능한 도구 목록 조회
        print("3. 사용 가능한 MCP 도구 목록")
        try:
            response = await client.get(f"{BASE_URL}/api/mcp/tools")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 상태: {data['success']}")
                tools = data['data']['tools']
                for tool in tools:
                    print(f"   🔧 {tool['name']}: {tool['description']}")
                    for param, desc in tool['parameters'].items():
                        print(f"      - {param}: {desc}")
            else:
                print(f"   ❌ 오류: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 연결 오류: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 4. 아파트 매매 실거래가 조회 테스트 (서울 강남구)
        print("4. 아파트 매매 실거래가 조회 테스트")
        print("   📍 지역: 서울 강남구 (11680)")
        
        # 이전 달 조회 (데이터가 있을 가능성이 높음)
        last_month = (datetime.now() - timedelta(days=30)).strftime("%Y%m")
        print(f"   📅 조회 월: {last_month}")
        
        try:
            test_data = {
                "lawd_cd": "11680",  # 서울 강남구
                "deal_ymd": last_month
            }
            
            response = await client.post(
                f"{BASE_URL}/api/mcp/apartment/trade",
                json=test_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 상태: {data['success']}")
                print(f"   📝 메시지: {data['message']}")
                
                if data['success'] and data['data']:
                    items = data['data'].get('items', [])
                    total_count = data['data'].get('total_count', 0)
                    print(f"   📊 조회 건수: {total_count}건")
                    
                    if items:
                        print("   💰 최근 거래 예시 (최대 3건):")
                        for i, item in enumerate(items[:3], 1):
                            apt_name = item.get('아파트명', 'N/A')
                            dong = item.get('법정동', 'N/A')
                            price = item.get('거래금액', 'N/A')
                            area = item.get('전용면적', 'N/A')
                            floor = item.get('층', 'N/A')
                            build_year = item.get('건축년도', 'N/A')
                            deal_day = item.get('거래일', 'N/A')
                            
                            print(f"      {i}. {apt_name} ({dong})")
                            print(f"         💰 거래가: {price}만원")
                            print(f"         📐 전용면적: {area}㎡")
                            print(f"         🏢 층수: {floor}층")
                            print(f"         🏗️  건축년도: {build_year}년")
                            print(f"         📅 거래일: {deal_day}일")
                            print()
                else:
                    print("   ℹ️  해당 기간의 거래 데이터가 없습니다.")
                    
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 오류 메시지: {error_data}")
                except:
                    print(f"   📝 응답: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 연결 오류: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 5. 아파트 전월세 실거래가 조회 테스트
        print("5. 아파트 전월세 실거래가 조회 테스트")
        print("   📍 지역: 서울 강남구 (11680)")
        print(f"   📅 조회 월: {last_month}")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/mcp/apartment/rent",
                json=test_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 상태: {data['success']}")
                print(f"   📝 메시지: {data['message']}")
                
                if data['success'] and data['data']:
                    total_count = data['data'].get('total_count', 0)
                    print(f"   📊 조회 건수: {total_count}건")
                else:
                    print("   ℹ️  해당 기간의 전월세 데이터가 없습니다.")
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 연결 오류: {e}")
        
        print("\n" + "="*70)
        print("테스트 완료!")
        print("="*70)
        
        # API 키 설정 안내
        print("\n📋 사용 안내:")
        print("1. 실제 데이터를 조회하려면 국토교통부 공공데이터포털에서 API 키를 발급받아야 합니다.")
        print("2. 발급받은 API 키를 .env 파일에 MOLIT_API_KEY=your_api_key 형식으로 설정하세요.")
        print("3. 지역코드는 행정표준코드관리시스템의 법정동 코드 앞 5자리를 사용합니다.")
        print("4. 계약년월은 YYYYMM 형식으로 입력합니다.")
        print("\n🔗 공공데이터포털: https://www.data.go.kr/dataset/3050988/openapi.do")

if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints())