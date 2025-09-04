"""
External Agent Adapter
외부 에이전트와의 통신을 위한 어댑터 시스템
다양한 API 형식을 A2A 프로토콜로 변환
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger

from ..utils.config import settings


class BaseAgentAdapter(ABC):
    """외부 에이전트 어댑터 기본 클래스"""
    
    def __init__(self, base_url: str, agent_info: Dict[str, Any]):
        self.base_url = base_url.rstrip('/')
        self.agent_info = agent_info
        self.session_id: Optional[str] = None
        
    @abstractmethod
    async def send_message(self, message: str) -> Dict[str, Any]:
        """메시지 전송"""
        pass
    
    @abstractmethod
    async def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 조회"""
        pass


class SocraticWebAdapter(BaseAgentAdapter):
    """소크라테스 Web3 AI Tutor 어댑터"""
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """소크라테스 에이전트에게 메시지 전송"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 여러 가능한 엔드포인트 시도
                endpoints_to_try = [
                    f"{self.base_url}/api/chat",
                    f"{self.base_url}/chat",
                    f"{self.base_url}/api/message",
                    f"{self.base_url}/api/a2a/message"
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        # 다양한 요청 형식 시도
                        request_formats = [
                            {"message": message},
                            {"content": message, "sender": "A2A_Agent"},
                            {"prompt": message},
                            {"query": message}
                        ]
                        
                        for request_data in request_formats:
                            response = await client.post(
                                endpoint,
                                json=request_data,
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # 응답 형식 정규화
                                content = self._extract_content_from_response(result)
                                if content:
                                    return {
                                        "success": True,
                                        "content": content,
                                        "sender": self.agent_info.get("name", "Socratic Tutor"),
                                        "timestamp": datetime.now().isoformat(),
                                        "endpoint_used": endpoint,
                                        "raw_response": result
                                    }
                                    
                    except Exception as e:
                        logger.debug(f"Failed endpoint {endpoint}: {e}")
                        continue
                
                # 모든 시도 실패 시 기본 응답 생성
                return await self._generate_fallback_response(message)
                
        except Exception as e:
            logger.error(f"Socratic adapter error: {e}")
            return await self._generate_fallback_response(message)
    
    def _extract_content_from_response(self, response: Dict) -> Optional[str]:
        """다양한 응답 형식에서 컨텐츠 추출"""
        # 가능한 응답 키들
        content_keys = ["response", "content", "message", "text", "answer", "reply"]
        
        for key in content_keys:
            if key in response and response[key]:
                return str(response[key])
        
        # 직접 문자열인 경우
        if isinstance(response, str):
            return response
            
        return None
    
    async def _generate_fallback_response(self, message: str) -> Dict[str, Any]:
        """연결 실패 시 대체 응답 생성"""
        
        # 키워드 기반 간단한 응답
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["안녕", "hello", "hi"]):
            content = """안녕하세요! 저는 소크라테스식 대화법으로 Web3와 블록체인을 가르치는 AI 튜터입니다. 

🤔 오늘은 어떤 것이 궁금하신가요?
• Web3의 기본 개념
• 블록체인 기술
• 스마트 컨트랙트
• DeFi와 NFT
• 암호화폐의 원리

질문해주시면 단계별로 쉽게 설명해드리겠습니다!"""

        elif any(keyword in message_lower for keyword in ["web3", "웹3", "블록체인", "blockchain"]):
            content = """좋은 질문입니다! 🧐

Web3에 대해 함께 탐구해보죠. 먼저 질문하나 해보겠습니다:

💭 **당신은 지금 인터넷을 어떻게 사용하고 계신가요?**

웹사이트에 접속해서 정보를 보고, SNS에 글을 올리고, 온라인 쇼핑을 하시죠? 이것이 바로 Web2입니다.

그렇다면 Web3는 무엇이 다를까요? 🤔

가장 큰 차이점을 생각해보세요: **누가 당신의 데이터를 소유하고 있을까요?**"""

        elif any(keyword in message_lower for keyword in ["스마트컨트랙트", "smart contract"]):
            content = """스마트 컨트랙트에 대해 알고 싶으시군요! 🤖

먼저 이렇게 생각해보세요:

💡 **자판기를 사용할 때 어떤 일이 일어날까요?**

1. 동전을 넣고
2. 버튼을 누르면
3. 자동으로 음료가 나옵니다

여기서 중요한 것은 **중간에 사람이 개입하지 않는다는 점**입니다.

스마트 컨트랙트도 이와 비슷합니다. 조건이 충족되면 자동으로 실행되는 프로그램이죠.

🤔 **그렇다면 이것이 왜 혁신적일까요?** 어떤 장점이 있을 것 같나요?"""

        else:
            content = f"""흥미로운 질문이네요! 🤔

'{message}'에 대해 함께 생각해봅시다.

소크라테스식 방법으로 접근해보겠습니다:

💭 **먼저, 이 주제에 대해 당신이 이미 알고 있는 것은 무엇인가요?**

그리고 **어떤 부분이 가장 궁금하신가요?**

당신의 생각을 들려주시면, 함께 단계별로 탐구해보겠습니다!

*참고: 현재 외부 연결 문제로 기본 모드로 응답하고 있습니다. 더 깊은 대화를 위해서는 시스템 관리자에게 문의해주세요.*"""

        return {
            "success": True,
            "content": content,
            "sender": "Socrates (Fallback Mode)",
            "timestamp": datetime.now().isoformat(),
            "mode": "fallback",
            "original_message": message
        }
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 조회"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                well_known_url = f"{self.base_url}/api/a2a/.well-known/agent.json"
                response = await client.get(well_known_url)
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.debug(f"Failed to get agent info: {e}")
        
        # 기본 정보 반환
        return {
            "name": "Socrates Web3 AI Tutor",
            "description": "Web3와 블록체인을 소크라테스식 대화법으로 가르치는 AI 튜터",
            "capabilities": ["socratic_dialogue", "web3_education", "blockchain_explanation"],
            "status": "fallback_mode"
        }


class RealEstateAgentAdapter(BaseAgentAdapter):
    """부동산 에이전트 어댑터"""
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """부동산 에이전트에게 메시지 전송"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                endpoint = f"{self.base_url}/api/chat"
                
                response = await client.post(
                    endpoint,
                    json={"message": message},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = self._extract_content_from_response(result)
                    
                    if content:
                        return {
                            "success": True,
                            "content": content,
                            "sender": self.agent_info.get("name", "Real Estate Agent"),
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            logger.error(f"Real estate adapter error: {e}")
        
        # 부동산 관련 기본 응답
        return {
            "success": True,
            "content": f"""안녕하세요! 부동산 전문 상담사입니다. 🏠

'{message}'에 대해 도움드리겠습니다.

📊 **부동산 투자나 매물 상담**을 원하시나요?

• 투자가치 분석
• 지역별 시세 정보  
• 생활환경 평가
• 매물 추천

구체적인 지역이나 조건을 알려주시면 더 정확한 상담이 가능합니다!

*참고: 현재 외부 연결 문제로 기본 모드로 응답하고 있습니다.*""",
            "sender": "Real Estate Agent (Fallback Mode)",
            "timestamp": datetime.now().isoformat(),
            "mode": "fallback"
        }
    
    def _extract_content_from_response(self, response: Dict) -> Optional[str]:
        """응답에서 컨텐츠 추출"""
        content_keys = ["response", "content", "message", "text", "answer"]
        
        for key in content_keys:
            if key in response and response[key]:
                return str(response[key])
                
        return None
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """부동산 에이전트 정보"""
        return {
            "name": "Real Estate Investment Advisor",
            "description": "부동산 투자 및 매물 상담 전문 에이전트",
            "capabilities": ["investment_analysis", "property_recommendation", "market_analysis"],
            "status": "available"
        }


class ExternalAgentManager:
    """외부 에이전트 관리자"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseAgentAdapter] = {}
        self.adapter_mapping = {
            "socratic-web3-tutor": SocraticWebAdapter,
            "a2a-mcp-realestate": RealEstateAgentAdapter,
            # 추가 에이전트들을 여기에 매핑
        }
    
    async def get_adapter(self, agent_id: str, base_url: str, agent_info: Dict[str, Any]) -> BaseAgentAdapter:
        """에이전트 ID에 해당하는 어댑터 반환"""
        
        if agent_id not in self.adapters:
            adapter_class = self.adapter_mapping.get(agent_id, SocraticWebAdapter)
            self.adapters[agent_id] = adapter_class(base_url, agent_info)
            
        return self.adapters[agent_id]
    
    async def send_message(self, agent_id: str, base_url: str, agent_info: Dict[str, Any], message: str) -> Dict[str, Any]:
        """지정된 외부 에이전트에게 메시지 전송"""
        try:
            adapter = await self.get_adapter(agent_id, base_url, agent_info)
            result = await adapter.send_message(message)
            
            logger.info(f"Message sent to {agent_id}: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message to {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "연결 오류가 발생했습니다. 나중에 다시 시도해주세요."
            }
    
    async def get_agent_info(self, agent_id: str, base_url: str, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """외부 에이전트 정보 조회"""
        try:
            adapter = await self.get_adapter(agent_id, base_url, agent_info)
            return await adapter.get_agent_info()
            
        except Exception as e:
            logger.error(f"Failed to get info from {agent_id}: {e}")
            return {
                "name": agent_info.get("name", "Unknown Agent"),
                "description": agent_info.get("description", "외부 에이전트"),
                "status": "connection_error"
            }


# 글로벌 인스턴스
external_agent_manager = ExternalAgentManager()