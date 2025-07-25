#!/usr/bin/env python3
"""
AI 엔드포인트 테스트 스크립트
"""
import asyncio
import httpx
import json


async def test_ai_endpoints():
    """AI API 엔드포인트들 테스트"""
    base_url = "http://localhost:28000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 AI API 엔드포인트 테스트")
        print("=" * 50)
        
        # 1. AI 서비스 상태 확인
        try:
            response = await client.get(f"{base_url}/api/ai/status")
            if response.status_code == 200:
                status = response.json()
                print(f"✅ AI 서비스 상태: {status['service_status']}")
                print(f"🔧 사용 가능한 기능: {len(status.get('capabilities', []))}개")
            else:
                print(f"❌ 상태 확인 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            print("💡 서버가 실행 중인지 확인하세요: ./run_dev.sh")
            return
        
        # 2. AI 채팅 테스트
        print(f"\n💬 AI 채팅 테스트")
        chat_data = {
            "prompt": "A2A Agent 시스템의 장점을 3가지만 간단히 설명해주세요.",
            "context": "마이크로서비스 아키텍처 환경"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/chat", json=chat_data)
            if response.status_code == 200:
                chat_result = response.json()
                print(f"🤖 AI 응답: {chat_result['response'][:200]}...")
            else:
                print(f"❌ 채팅 테스트 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 채팅 오류: {e}")
        
        # 3. 코드 분석 테스트
        print(f"\n📊 코드 분석 테스트")
        code_data = {
            "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 사용 예시
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
""",
            "language": "python"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/analyze-code", json=code_data)
            if response.status_code == 200:
                analysis = response.json()
                print(f"🔍 코드 분석: {analysis['analysis'][:200]}...")
            else:
                print(f"❌ 코드 분석 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 코드 분석 오류: {e}")
        
        # 4. 데이터 분석 테스트
        print(f"\n📈 데이터 분석 테스트")
        data_analysis_data = {
            "data": {
                "sales": [
                    {"month": "2024-01", "amount": 1200000, "orders": 45},
                    {"month": "2024-02", "amount": 1350000, "orders": 52},
                    {"month": "2024-03", "amount": 1180000, "orders": 41}
                ],
                "customers": {
                    "new": 23,
                    "returning": 34,
                    "churned": 8
                }
            },
            "analysis_type": "business"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/analyze-data", json=data_analysis_data)
            if response.status_code == 200:
                analysis = response.json()
                print(f"📊 데이터 분석: {analysis['analysis'][:200]}...")
            else:
                print(f"❌ 데이터 분석 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 데이터 분석 오류: {e}")
        
        # 5. 문서 생성 테스트
        print(f"\n📚 문서 생성 테스트")
        doc_data = {
            "code": """
class UserService:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, user_data: dict) -> dict:
        user_id = await self.db.insert_user(user_data)
        return {"user_id": user_id, "status": "created"}
    
    async def get_user(self, user_id: str) -> dict:
        return await self.db.get_user(user_id)
""",
            "doc_type": "api"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/generate-docs", json=doc_data)
            if response.status_code == 200:
                docs = response.json()
                print(f"📖 생성된 문서: {docs['documentation'][:200]}...")
            else:
                print(f"❌ 문서 생성 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 문서 생성 오류: {e}")
        
        # 6. 개선사항 제안 테스트
        print(f"\n💡 개선사항 제안 테스트")
        improvement_data = {
            "description": "현재 API 응답 시간이 평균 200ms인데, 사용자들이 느리다고 불만을 제기하고 있습니다.",
            "current_data": "FastAPI + PostgreSQL 환경, 동시 사용자 약 100명"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/suggest-improvements", json=improvement_data)
            if response.status_code == 200:
                suggestions = response.json()
                print(f"💡 개선 제안: {suggestions['suggestions'][:200]}...")
            else:
                print(f"❌ 개선사항 제안 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 개선사항 제안 오류: {e}")
        
        # 7. 번역 테스트
        print(f"\n🌍 번역 테스트")
        translation_data = {
            "message": "Hello, this is A2A Agent system. It provides intelligent communication between microservices.",
            "target_lang": "ko"
        }
        
        try:
            response = await client.post(f"{base_url}/api/ai/translate", json=translation_data)
            if response.status_code == 200:
                translation = response.json()
                print(f"🌍 번역 결과: {translation['translation']}")
            else:
                print(f"❌ 번역 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 번역 오류: {e}")
        
        # 8. 프로젝트 분석 테스트
        print(f"\n🏗️ 프로젝트 분석 테스트")
        try:
            response = await client.post(f"{base_url}/api/ai/analyze-project")
            if response.status_code == 200:
                project_analysis = response.json()
                print(f"🏗️ 프로젝트 분석: {project_analysis['analysis'][:200]}...")
            else:
                print(f"❌ 프로젝트 분석 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 프로젝트 분석 오류: {e}")
        
        print(f"\n✅ 모든 AI 엔드포인트 테스트 완료!")
        print(f"🌐 API 문서: {base_url}/docs")


if __name__ == "__main__":
    asyncio.run(test_ai_endpoints())