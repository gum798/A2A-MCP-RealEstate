"""
Smart Agent Router
자연어로 에이전트 전환 및 대화 라우팅
"""

import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pydantic import BaseModel
import httpx
from loguru import logger

from .multi_agent_conversation import MultiAgentConversation, ConversationMessage
from .a2a_agent import A2AAgent
from .agent_registry import agent_registry, RegistryAgent


class AgentProfile(BaseModel):
    """에이전트 프로필"""
    agent_id: str
    name: str
    aliases: List[str]  # 별명들
    keywords: List[str]  # 관련 키워드들
    description: str
    url: str
    capabilities: List[str]
    personality_traits: List[str] = []


class SmartAgentRouter:
    """스마트 에이전트 라우터"""
    
    def __init__(self, conversation_manager: MultiAgentConversation):
        self.conversation_manager = conversation_manager
        self.current_session_id: Optional[str] = None
        self.current_agent_id: Optional[str] = None
        
        # 미리 정의된 에이전트 프로필들
        self.agent_profiles: Dict[str, AgentProfile] = self._initialize_agent_profiles()
        
        # 자연어 패턴들
        self.switch_patterns = [
            # 직접 이름 언급
            r"(.*?)(소크라테스|socrates|socratic)(.*)이야기.*하고?\s*싶",
            r"(.*?)(소크라테스|socrates|socratic)(.*)대화.*하고?\s*싶",
            r"(.*?)(소크라테스|socrates|socratic)(.*)말.*하고?\s*싶",
            r"(.*?)(소크라테스|socrates|socratic)(.*)와\s*함께",
            r"(.*?)(소크라테스|socrates|socratic)(.*)에게.*물어",
            
            # 전환 표현
            r"(.*)에이전트(.*)바꿔",
            r"(.*)다른(.*)에이전트",
            r"(.*)전환.*해",
            r"(.*)바꿔.*줘",
            
            # 주제별 전환
            r"(.*)(웹3|web3|블록체인|blockchain)(.*)배우고?\s*싶",
            r"(.*)(웹3|web3|블록체인|blockchain)(.*)알고?\s*싶",
            r"(.*)(웹3|web3|블록체인|blockchain)(.*)질문",
            r"(.*)(ai|인공지능)(.*)배우고?\s*싶",
            
            # 튜터/선생님 요청
            r"(.*)선생님(.*)바꿔",
            r"(.*)튜터(.*)바꿔",
            r"(.*)가르쳐(.*)줄(.*)에이전트"
        ]
    
    def _initialize_agent_profiles(self) -> Dict[str, AgentProfile]:
        """에이전트 프로필 초기화 (레지스트리에서 로드)"""
        profiles = {}
        
        # 레지스트리에서 모든 활성 에이전트 로드
        for registry_agent in agent_registry.get_all_agents(active_only=True):
            profile = AgentProfile(
                agent_id=registry_agent.agent_id,
                name=registry_agent.name,
                aliases=registry_agent.aliases,
                keywords=registry_agent.keywords,
                description=registry_agent.description,
                url=registry_agent.base_url,
                capabilities=registry_agent.capabilities,
                personality_traits=registry_agent.personality_traits
            )
            profiles[profile.agent_id] = profile
        
        logger.info(f"Initialized {len(profiles)} agent profiles from registry")
        return profiles
    
    async def process_message(self, user_message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        사용자 메시지를 분석해서 에이전트 전환이 필요한지 판단
        
        Returns:
            (agent_switch_needed, target_agent_id, response_message)
        """
        
        # 1. 직접적인 에이전트 전환 요청 감지
        switch_result = self._detect_agent_switch_request(user_message)
        if switch_result[0]:
            return switch_result
        
        # 2. 레지스트리 기반 에이전트 추천
        recommended_agents = agent_registry.get_recommended_agents(user_message, limit=1)
        if recommended_agents:
            best_agent = recommended_agents[0]
            if best_agent.agent_id in self.agent_profiles:
                return False, best_agent.agent_id, f"이 주제는 {best_agent.name}이 전문이에요. 전환할까요?"
        
        # 3. 기본적으로 전환 없음
        return False, None, None
    
    def _detect_agent_switch_request(self, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """직접적인 에이전트 전환 요청 감지"""
        message_lower = message.lower().strip()
        
        for pattern in self.switch_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                logger.info(f"Agent switch pattern matched: {pattern}")
                
                # 어떤 에이전트를 원하는지 분석
                target_agent = self._identify_target_agent(message)
                if target_agent:
                    agent_profile = self.agent_profiles[target_agent]
                    return True, target_agent, f"네! {agent_profile.name}와 대화해드릴게요. 잠시만 기다려주세요..."
                else:
                    return True, "socratic-web3-tutor", "소크라테스 튜터와 연결해드릴게요!"
        
        return False, None, None
    
    def _identify_target_agent(self, message: str) -> Optional[str]:
        """메시지에서 대상 에이전트 식별 (레지스트리 사용)"""
        message_lower = message.lower()
        
        # 레지스트리에서 별명으로 검색
        for word in message_lower.split():
            agent = agent_registry.get_agent_by_alias(word)
            if agent and agent.agent_id in self.agent_profiles:
                return agent.agent_id
        
        # 기존 프로필에서도 검색 (백업)
        for agent_id, profile in self.agent_profiles.items():
            for alias in profile.aliases:
                if alias.lower() in message_lower:
                    return agent_id
            if profile.name.lower() in message_lower:
                return agent_id
        
        return None
    
    def _recommend_agent_by_keywords(self, message: str) -> Optional[str]:
        """키워드 기반 에이전트 추천"""
        message_lower = message.lower()
        
        agent_scores = {}
        
        for agent_id, profile in self.agent_profiles.items():
            score = 0
            for keyword in profile.keywords:
                if keyword.lower() in message_lower:
                    score += 1
            
            if score > 0:
                agent_scores[agent_id] = score
        
        if agent_scores:
            # 가장 높은 점수의 에이전트 반환
            best_agent = max(agent_scores, key=agent_scores.get)
            return best_agent
        
        return None
    
    async def switch_to_agent(self, agent_id: str, initial_message: str = None) -> Dict[str, Any]:
        """지정된 에이전트로 전환"""
        try:
            # 1. 에이전트가 등록되어 있는지 확인
            if agent_id not in self.agent_profiles:
                return {"success": False, "error": f"Unknown agent: {agent_id}"}
            
            profile = self.agent_profiles[agent_id]
            
            # 2. 에이전트 발견 및 연결
            agent = await self.conversation_manager.discover_and_add_agent(profile.url)
            if not agent:
                return {"success": False, "error": f"Failed to connect to {profile.name}"}
            
            # 3. 새 대화 세션 시작
            session_id = await self.conversation_manager.start_conversation(
                f"{profile.name}와의 대화",
                [agent_id]
            )
            
            self.current_session_id = session_id
            self.current_agent_id = agent_id
            
            # 4. 초기 메시지가 있다면 전송
            if initial_message:
                await self.conversation_manager.send_message(
                    session_id,
                    initial_message,
                    agent_id
                )
            
            return {
                "success": True,
                "session_id": session_id,
                "agent_id": agent_id,
                "agent_name": profile.name,
                "message": f"{profile.name}와 연결되었습니다!"
            }
            
        except Exception as e:
            logger.error(f"Agent switch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message_to_current_agent(self, message: str) -> Dict[str, Any]:
        """현재 활성화된 에이전트에게 메시지 전송"""
        if not self.current_session_id or not self.current_agent_id:
            return {"success": False, "error": "No active agent session"}
        
        try:
            sent_message = await self.conversation_manager.send_message(
                self.current_session_id,
                message,
                self.current_agent_id
            )
            
            return {
                "success": True,
                "message_id": sent_message.message_id,
                "session_id": self.current_session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send message to current agent: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_latest_response(self, timeout_seconds: int = 10) -> Optional[ConversationMessage]:
        """현재 세션에서 최신 응답 가져오기"""
        if not self.current_session_id:
            return None
        
        try:
            # 응답 대기
            for _ in range(timeout_seconds):
                messages = await self.conversation_manager.get_conversation_history(
                    self.current_session_id, limit=5
                )
                
                if messages:
                    # 에이전트의 최신 메시지 찾기
                    for msg in reversed(messages):
                        if (msg.sender_id == self.current_agent_id or 
                            msg.sender_id != self.conversation_manager.local_agent.agent_id):
                            return msg
                
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to get latest response: {e}")
        
        return None
    
    def get_current_agent_info(self) -> Optional[Dict[str, Any]]:
        """현재 활성 에이전트 정보"""
        if not self.current_agent_id:
            return None
        
        if self.current_agent_id in self.agent_profiles:
            profile = self.agent_profiles[self.current_agent_id]
            return {
                "agent_id": profile.agent_id,
                "name": profile.name,
                "description": profile.description,
                "capabilities": profile.capabilities,
                "session_id": self.current_session_id
            }
        
        return None
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 에이전트 목록"""
        return [
            {
                "agent_id": profile.agent_id,
                "name": profile.name,
                "aliases": profile.aliases,
                "keywords": profile.keywords[:5],  # 처음 5개만
                "description": profile.description
            }
            for profile in self.agent_profiles.values()
        ]
    
    async def reset_session(self):
        """현재 세션 리셋"""
        if self.current_session_id:
            await self.conversation_manager.end_conversation(self.current_session_id)
        
        self.current_session_id = None
        self.current_agent_id = None
    
    def get_switch_examples(self) -> List[str]:
        """에이전트 전환 예시 문장들"""
        return [
            "소크라테스와 이야기하고 싶어",
            "Web3에 대해 배우고 싶어",
            "블록체인 튜터로 바꿔줘",
            "다른 에이전트와 대화하고 싶어",
            "AI 전문가에게 질문하고 싶어"
        ]