"""
AI 기능이 통합된 지능형 A2A Agent
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from app.agent.a2a_agent import A2AAgent, AgentMessage
from app.ai.gemini_service import gemini_service
from app.utils.logger import logger


class IntelligentMessage(BaseModel):
    """AI 분석이 포함된 메시지"""
    original_message: AgentMessage
    ai_analysis: Optional[str] = None
    ai_suggestions: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class IntelligentA2AAgent(A2AAgent):
    """AI 기능이 통합된 지능형 A2A 에이전트"""
    
    def __init__(self, agent_id: str = None, agent_name: str = None):
        super().__init__(agent_id, agent_name)
        self.ai_enabled = gemini_service.gemini_available
        self.intelligent_message_queue: List[IntelligentMessage] = []
        
        logger.info(f"Intelligent A2A Agent initialized (AI: {'enabled' if self.ai_enabled else 'disabled'})")
    
    async def smart_send_message(self, target_agent_id: str, message_type: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """AI가 메시지를 분석하고 최적화해서 전송"""
        try:
            # 1. AI가 메시지 분석 및 최적화
            if self.ai_enabled:
                optimized_payload = await self._optimize_message_with_ai(message_type, payload)
            else:
                optimized_payload = payload
            
            # 2. 기본 전송 로직 실행
            response = await self.send_message(target_agent_id, message_type, optimized_payload)
            
            # 3. AI가 응답 분석
            if self.ai_enabled and response:
                await self._analyze_response_with_ai(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Smart message sending failed: {e}")
            # AI 실패 시 기본 전송으로 폴백
            return await self.send_message(target_agent_id, message_type, payload)
    
    async def _optimize_message_with_ai(self, message_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """AI가 메시지를 분석하고 최적화"""
        try:
            analysis_prompt = f"""
A2A Agent 시스템에서 '{message_type}' 타입의 메시지를 전송하려고 합니다.

메시지 페이로드:
{payload}

다음을 분석해서 JSON으로 답변해주세요:
1. 메시지의 우선순위 (1-10)
2. 추가하면 좋을 메타데이터
3. 최적화된 페이로드 구조

형식:
{{
    "priority": 숫자,
    "suggested_metadata": {{}},
    "optimized_payload": {{}}
}}
"""
            
            ai_response = await gemini_service.chat(analysis_prompt)
            
            # AI 응답에서 JSON 파싱 시도
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_analysis = json.loads(json_match.group())
                
                # AI 제안사항 적용
                optimized_payload = payload.copy()
                
                if 'suggested_metadata' in ai_analysis:
                    optimized_payload.update(ai_analysis['suggested_metadata'])
                
                if 'optimized_payload' in ai_analysis:
                    optimized_payload.update(ai_analysis['optimized_payload'])
                
                # 메타데이터 추가
                optimized_payload['_ai_metadata'] = {
                    'priority': ai_analysis.get('priority', 5),
                    'optimized_at': datetime.now().isoformat(),
                    'ai_processed': True
                }
                
                logger.info(f"Message optimized by AI (priority: {ai_analysis.get('priority', 5)})")
                return optimized_payload
            
        except Exception as e:
            logger.warning(f"AI optimization failed: {e}")
        
        return payload
    
    async def _analyze_response_with_ai(self, response: Dict) -> None:
        """AI가 응답을 분석해서 인사이트 생성"""
        try:
            analysis_prompt = f"""
A2A Agent로부터 다음 응답을 받았습니다:

{response}

이 응답을 분석해서 다음을 제공해주세요:
1. 응답의 성공/실패 여부
2. 중요한 정보나 패턴
3. 후속 조치 제안
4. 시스템 상태에 대한 인사이트

한국어로 답변해주세요.
"""
            
            analysis = await gemini_service.chat(analysis_prompt)
            
            # 분석 결과를 로그에 기록
            logger.info(f"AI Response Analysis: {analysis[:200]}...")
            
            # 분석 결과를 메시지 큐에 저장
            self.message_queue.append({
                'type': 'ai_analysis',
                'response_data': response,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.warning(f"AI response analysis failed: {e}")
    
    async def receive_intelligent_message(self, message_data: Dict) -> Dict:
        """AI 분석이 포함된 메시지 수신"""
        # 기본 메시지 처리
        base_response = await self.receive_message(message_data)
        
        if not self.ai_enabled:
            return base_response
        
        try:
            message = AgentMessage(**message_data)
            
            # AI가 메시지 분석
            analysis_prompt = f"""
A2A Agent로부터 '{message.message_type}' 메시지를 받았습니다:

발신자: {message.source_agent_id}
내용: {message.payload}

이 메시지를 분석해서 다음을 제공해주세요:
1. 메시지의 중요도 (1-10)
2. 필요한 액션
3. 자동화 가능한 응답
4. 경고사항 (있다면)

한국어로 답변해주세요.
"""
            
            ai_analysis = await gemini_service.chat(analysis_prompt)
            
            # 지능형 메시지 객체 생성
            intelligent_msg = IntelligentMessage(
                original_message=message,
                ai_analysis=ai_analysis
            )
            
            self.intelligent_message_queue.append(intelligent_msg)
            
            # AI 분석 결과를 응답에 추가
            enhanced_response = base_response.copy()
            enhanced_response['ai_analysis'] = ai_analysis
            enhanced_response['intelligent_processing'] = True
            
            logger.info(f"Message processed with AI analysis: {message.id}")
            return enhanced_response
            
        except Exception as e:
            logger.warning(f"AI message analysis failed: {e}")
            return base_response
    
    async def get_ai_insights(self) -> Dict:
        """AI가 분석한 시스템 인사이트 제공"""
        if not self.ai_enabled:
            return {"error": "AI not available"}
        
        try:
            # 최근 메시지들과 연결 상태 분석
            insights_prompt = f"""
A2A Agent 시스템 상태를 분석해주세요:

연결된 에이전트 수: {len(self.connections)}
메시지 큐 크기: {len(self.message_queue)}
지능형 메시지 수: {len(self.intelligent_message_queue)}

최근 활동:
{self.message_queue[-5:] if self.message_queue else "활동 없음"}

다음을 분석해서 제공해주세요:
1. 시스템 건강 상태
2. 성능 지표
3. 개선 제안
4. 잠재적 이슈

한국어로 답변해주세요.
"""
            
            insights = await gemini_service.chat(insights_prompt)
            
            return {
                "ai_insights": insights,
                "system_stats": {
                    "connections": len(self.connections),
                    "message_queue": len(self.message_queue),
                    "intelligent_messages": len(self.intelligent_message_queue),
                    "ai_enabled": self.ai_enabled
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {"error": f"AI 인사이트 생성 실패: {str(e)}"}
    
    async def auto_respond_with_ai(self, message: AgentMessage) -> Optional[Dict]:
        """AI가 자동으로 적절한 응답 생성"""
        if not self.ai_enabled:
            return None
        
        try:
            auto_response_prompt = f"""
A2A Agent 시스템에서 다음 메시지에 대한 자동 응답을 생성해주세요:

메시지 타입: {message.message_type}
발신자: {message.source_agent_id}
내용: {message.payload}

적절한 자동 응답을 JSON 형태로 생성해주세요:
{{
    "should_auto_respond": true/false,
    "response_type": "응답 타입",
    "response_payload": {{}},
    "confidence": 0.0-1.0
}}
"""
            
            ai_response = await gemini_service.chat(auto_response_prompt)
            
            # JSON 파싱 시도
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                auto_response_data = json.loads(json_match.group())
                
                if auto_response_data.get('should_auto_respond', False):
                    # AI가 제안한 자동 응답 전송
                    response = await self.send_message(
                        message.source_agent_id,
                        auto_response_data.get('response_type', 'auto_response'),
                        auto_response_data.get('response_payload', {})
                    )
                    
                    logger.info(f"AI auto-response sent to {message.source_agent_id}")
                    return response
            
        except Exception as e:
            logger.warning(f"AI auto-response failed: {e}")
        
        return None
    
    def get_intelligent_status(self) -> Dict:
        """지능형 에이전트 상태 반환"""
        base_status = self.get_status()
        
        base_status.update({
            "ai_enabled": self.ai_enabled,
            "intelligent_features": [
                "smart_messaging", "ai_analysis", "auto_response", 
                "insights_generation", "message_optimization"
            ] if self.ai_enabled else [],
            "intelligent_message_count": len(self.intelligent_message_queue),
            "ai_service_status": "active" if gemini_service.gemini_available else "unavailable"
        })
        
        return base_status