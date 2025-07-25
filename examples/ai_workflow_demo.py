#!/usr/bin/env python3
"""
A2A Agent + Gemini AI 워크플로우 데모
"""
import asyncio
import json
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.intelligent_agent import IntelligentA2AAgent
from app.ai.gemini_service import gemini_service
from app.data.sample_data import sample_data


async def demo_ai_chat():
    """AI 채팅 데모"""
    print("🤖 AI 채팅 데모")
    print("=" * 50)
    
    questions = [
        "A2A Agent 시스템이 뭔가요?",
        "Python FastAPI의 장점은?",
        "마이크로서비스 아키텍처에서 중요한 점은?",
        "AI와 Agent의 융합이 왜 중요한가요?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n💬 질문 {i}: {question}")
        response = await gemini_service.chat(question)
        print(f"🤖 답변: {response[:200]}...")
        await asyncio.sleep(1)


async def demo_code_analysis():
    """코드 분석 데모"""
    print("\n\n📊 코드 분석 데모")
    print("=" * 50)
    
    sample_code = '''
async def send_message(self, target_agent_id: str, message_type: str, payload: Dict[str, Any]):
    connection = self.connections.get(target_agent_id)
    
    if not connection:
        raise ValueError(f"No connection found for agent {target_agent_id}")
    
    message = AgentMessage(
        id=str(uuid.uuid4()),
        source_agent_id=self.agent_id,
        target_agent_id=target_agent_id,
        message_type=message_type,
        payload=payload,
        timestamp=datetime.now().isoformat()
    )
    
    try:
        response = await self.client.post(
            f"{connection.url}/api/agent/message",
            json=message.model_dump()
        )
        
        if response.status_code == 200:
            logger.info(f"Message sent to {target_agent_id}: {message.id}")
            return response.json()
        else:
            logger.error(f"Failed to send message: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to send message to {target_agent_id}: {str(e)}")
        raise e
'''
    
    print("📝 분석할 코드:")
    print(sample_code[:200] + "...")
    
    analysis = await gemini_service.analyze_code(sample_code, "python")
    print(f"\n🔍 AI 분석 결과:")
    print(analysis[:500] + "...")


async def demo_data_analysis():
    """데이터 분석 데모"""
    print("\n\n📈 데이터 분석 데모")
    print("=" * 50)
    
    # 샘플 주문 데이터 분석
    orders = sample_data.get_orders()
    print(f"📦 주문 데이터 ({len(orders)}건):")
    for order in orders[:2]:
        print(f"  - {order['order_id']}: {order['total_amount']:,}원 ({order['status']})")
    
    analysis = await gemini_service.analyze_data({"orders": orders}, "business")
    print(f"\n📊 AI 분석 결과:")
    print(analysis[:400] + "...")


async def demo_intelligent_agent():
    """지능형 에이전트 데모"""
    print("\n\n🧠 지능형 에이전트 데모")
    print("=" * 50)
    
    # 지능형 에이전트 생성
    agent = IntelligentA2AAgent("demo-agent", "AI_Demo_Agent")
    
    print(f"🤖 에이전트 생성: {agent.agent_name}")
    print(f"🔌 AI 사용 가능: {agent.ai_enabled}")
    
    if agent.ai_enabled:
        # AI 인사이트 생성
        insights = await agent.get_ai_insights()
        print(f"\n🔮 AI 인사이트:")
        print(insights.get('ai_insights', 'AI 인사이트 생성 실패')[:300] + "...")
    
    # 에이전트 상태
    status = agent.get_intelligent_status()
    print(f"\n📊 에이전트 상태:")
    print(f"  - ID: {status['agent_id']}")
    print(f"  - AI 활성화: {status['ai_enabled']}")
    print(f"  - 지능형 기능: {len(status.get('intelligent_features', []))}개")


async def demo_smart_messaging():
    """스마트 메시징 데모"""
    print("\n\n💌 스마트 메시징 데모")
    print("=" * 50)
    
    agent = IntelligentA2AAgent("smart-agent", "Smart_Messaging_Agent")
    
    # 가상의 메시지 페이로드
    sample_payload = {
        "data_type": "user_analytics",
        "metrics": {
            "active_users": 1250,
            "new_signups": 45,
            "conversion_rate": 0.23
        },
        "time_period": "last_7_days"
    }
    
    print("📤 원본 메시지:")
    print(json.dumps(sample_payload, indent=2, ensure_ascii=False))
    
    if agent.ai_enabled:
        # AI로 메시지 최적화
        optimized = await agent._optimize_message_with_ai("data_request", sample_payload)
        print(f"\n✨ AI 최적화된 메시지:")
        print(json.dumps(optimized, indent=2, ensure_ascii=False)[:400] + "...")


async def demo_documentation_generation():
    """문서 생성 데모"""
    print("\n\n📚 문서 생성 데모")
    print("=" * 50)
    
    sample_function = '''
class A2AAgent:
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.connections = {}
        
    async def connect(self, target_url: str, target_id: str) -> bool:
        """다른 에이전트와 연결을 설정합니다."""
        # 연결 로직 구현
        pass
'''
    
    print("📝 문서화할 코드:")
    print(sample_function)
    
    docs = await gemini_service.generate_documentation(sample_function)
    print(f"\n📖 생성된 문서:")
    print(docs[:400] + "...")


async def demo_improvement_suggestions():
    """개선사항 제안 데모"""
    print("\n\n💡 개선사항 제안 데모")
    print("=" * 50)
    
    current_situation = """
현재 A2A Agent 시스템은 다음과 같습니다:
- FastAPI 기반 REST API
- 에이전트 간 HTTP 통신
- 샘플 데이터 제공
- Gemini AI 통합

하지만 다음과 같은 한계가 있습니다:
- 실시간 통신 부족
- 인증/보안 미흡
- 모니터링 도구 없음
- 테스트 케이스 부족
"""
    
    print("🔍 현재 상황:")
    print(current_situation)
    
    suggestions = await gemini_service.suggest_improvements(current_situation)
    print(f"\n💡 AI 개선 제안:")
    print(suggestions[:500] + "...")


async def main():
    """메인 데모 실행"""
    print("🚀 A2A Agent + Gemini AI 통합 데모")
    print("=" * 70)
    
    if not gemini_service.gemini_available:
        print("❌ Gemini CLI가 설치되지 않았거나 인증되지 않았습니다.")
        print("📖 설정 방법:")
        print("  1. npm install -g @google/gemini-cli")
        print("  2. gemini 명령어로 인증")
        print("  3. 또는 GEMINI_API_KEY 환경변수 설정")
        return
    
    demos = [
        demo_ai_chat,
        demo_code_analysis,
        demo_data_analysis,
        demo_intelligent_agent,
        demo_smart_messaging,
        demo_documentation_generation,
        demo_improvement_suggestions
    ]
    
    for i, demo in enumerate(demos, 1):
        try:
            await demo()
            if i < len(demos):  # 마지막이 아니면 잠시 대기
                print("\n⏳ 3초 후 다음 데모...")
                await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ 데모 오류: {e}")
    
    print("\n\n✅ 모든 데모 완료!")
    print("🌟 이제 실제 서버에서 /api/ai/ 엔드포인트를 사용해보세요!")


if __name__ == "__main__":
    asyncio.run(main())