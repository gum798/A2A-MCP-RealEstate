"""
Multi-Agent Conversation System
여러 에이전트와의 대화 및 협업 시스템
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import httpx
from loguru import logger

from .agent_discovery import agent_discovery
from .a2a_agent import A2AAgent


class ExternalAgent(BaseModel):
    """외부 에이전트 정보"""
    agent_id: str
    name: str
    description: str
    url: str
    capabilities: Dict[str, Any]
    protocol_version: str = "0.3.0"
    status: str = "unknown"
    last_contact: Optional[datetime] = None


class ConversationMessage(BaseModel):
    """대화 메시지"""
    message_id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    recipient_id: Optional[str] = None  # None이면 모든 에이전트에게
    message_type: str = "chat"
    content: str
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class ConversationSession(BaseModel):
    """대화 세션"""
    session_id: str
    title: str
    participants: List[str]
    created_at: datetime = datetime.now()
    status: str = "active"  # active, paused, ended
    message_count: int = 0
    last_activity: datetime = datetime.now()


class MultiAgentConversation:
    """다중 에이전트 대화 관리자"""
    
    def __init__(self, local_agent: A2AAgent):
        self.local_agent = local_agent
        self.external_agents: Dict[str, ExternalAgent] = {}
        self.conversations: Dict[str, ConversationSession] = {}
        self.messages: Dict[str, List[ConversationMessage]] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # 알려진 에이전트들 미리 등록
        self._register_known_agents()
    
    def _register_known_agents(self):
        """알려진 에이전트들을 미리 등록"""
        known_agents = [
            {
                "agent_id": "socratic-web3-tutor",
                "name": "Socratic Web3 AI Tutor",
                "description": "Step-by-step guidance on Web3, AI, and blockchain topics",
                "url": "https://socratic-web3-ai-tutor.vercel.app/api/a2a",
                "capabilities": {
                    "input_mode": "text",
                    "output_mode": "text",
                    "skills": ["Socratic Dialogue", "Web3", "AI", "Blockchain"]
                }
            }
        ]
        
        for agent_info in known_agents:
            agent = ExternalAgent(**agent_info)
            self.external_agents[agent.agent_id] = agent
            logger.info(f"Registered known agent: {agent.name}")
    
    async def discover_and_add_agent(self, agent_url: str) -> Optional[ExternalAgent]:
        """새 에이전트 발견 및 추가"""
        try:
            # .well-known/agent.json 엔드포인트에서 에이전트 정보 가져오기
            well_known_url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
            
            async with self.client as client:
                response = await client.get(well_known_url)
                response.raise_for_status()
                agent_data = response.json()
            
            # 에이전트 ID 생성 (URL 기반)
            agent_id = agent_data.get('id') or f"agent-{hash(agent_url) % 10000}"
            
            agent = ExternalAgent(
                agent_id=agent_id,
                name=agent_data.get('name', 'Unknown Agent'),
                description=agent_data.get('description', ''),
                url=agent_data.get('url', agent_url),
                capabilities=agent_data.get('capabilities', {}),
                protocol_version=agent_data.get('protocolVersion', '0.3.0')
            )
            
            # 연결 테스트
            if await self._test_agent_connection(agent):
                self.external_agents[agent_id] = agent
                logger.info(f"Added new agent: {agent.name} ({agent_id})")
                return agent
            else:
                logger.warning(f"Failed to connect to agent: {agent_url}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to discover agent at {agent_url}: {e}")
            return None
    
    async def _test_agent_connection(self, agent: ExternalAgent) -> bool:
        """에이전트 연결 테스트"""
        try:
            # 간단한 ping 메시지 전송
            test_message = {
                "id": str(uuid.uuid4()),
                "source_agent_id": self.local_agent.agent_id,
                "target_agent_id": agent.agent_id,
                "message_type": "ping",
                "payload": {"message": "connection_test"},
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.client as client:
                response = await client.post(
                    f"{agent.url}/message",
                    json=test_message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    agent.status = "connected"
                    agent.last_contact = datetime.now()
                    return True
                    
        except Exception as e:
            logger.debug(f"Connection test failed for {agent.name}: {e}")
            agent.status = "disconnected"
        
        return False
    
    async def start_conversation(self, title: str, participant_ids: List[str]) -> str:
        """새 대화 세션 시작"""
        session_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 참여자 검증
        valid_participants = [self.local_agent.agent_id]
        for participant_id in participant_ids:
            if participant_id in self.external_agents:
                valid_participants.append(participant_id)
            else:
                logger.warning(f"Unknown participant: {participant_id}")
        
        session = ConversationSession(
            session_id=session_id,
            title=title,
            participants=valid_participants
        )
        
        self.conversations[session_id] = session
        self.messages[session_id] = []
        
        logger.info(f"Started conversation: {title} with {len(valid_participants)} participants")
        return session_id
    
    async def send_message(self, session_id: str, content: str, recipient_id: Optional[str] = None) -> ConversationMessage:
        """대화에 메시지 전송"""
        if session_id not in self.conversations:
            raise ValueError(f"Conversation {session_id} not found")
        
        session = self.conversations[session_id]
        
        # 메시지 생성
        message = ConversationMessage(
            message_id=str(uuid.uuid4()),
            conversation_id=session_id,
            sender_id=self.local_agent.agent_id,
            sender_name=self.local_agent.agent_name,
            recipient_id=recipient_id,
            content=content
        )
        
        # 로컬에 메시지 저장
        self.messages[session_id].append(message)
        session.message_count += 1
        session.last_activity = datetime.now()
        
        # 참여자들에게 메시지 전송
        responses = []
        recipients = [recipient_id] if recipient_id else [p for p in session.participants if p != self.local_agent.agent_id]
        
        for participant_id in recipients:
            if participant_id in self.external_agents:
                response = await self._send_message_to_external_agent(participant_id, message)
                if response:
                    responses.append(response)
        
        return message
    
    async def _send_message_to_external_agent(self, agent_id: str, message: ConversationMessage) -> Optional[ConversationMessage]:
        """외부 에이전트에게 메시지 전송"""
        if agent_id not in self.external_agents:
            return None
        
        agent = self.external_agents[agent_id]
        
        try:
            # A2A 프로토콜 메시지 구성
            a2a_message = {
                "id": message.message_id,
                "source_agent_id": self.local_agent.agent_id,
                "target_agent_id": agent_id,
                "message_type": "conversation",
                "payload": {
                    "conversation_id": message.conversation_id,
                    "content": message.content,
                    "sender_name": message.sender_name,
                    "message_type": message.message_type,
                    "timestamp": message.timestamp.isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.client as client:
                response = await client.post(
                    f"{agent.url}/message",
                    json=a2a_message,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # 응답 메시지 생성
                    response_message = ConversationMessage(
                        message_id=str(uuid.uuid4()),
                        conversation_id=message.conversation_id,
                        sender_id=agent_id,
                        sender_name=agent.name,
                        recipient_id=self.local_agent.agent_id,
                        content=response_data.get('response', response_data.get('message', str(response_data))),
                        timestamp=datetime.now()
                    )
                    
                    # 응답을 대화에 추가
                    self.messages[message.conversation_id].append(response_message)
                    self.conversations[message.conversation_id].message_count += 1
                    
                    agent.last_contact = datetime.now()
                    agent.status = "connected"
                    
                    return response_message
                    
        except Exception as e:
            logger.error(f"Failed to send message to {agent.name}: {e}")
            agent.status = "error"
        
        return None
    
    async def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        """대화 기록 조회"""
        if session_id not in self.messages:
            return []
        
        messages = self.messages[session_id]
        if limit:
            return messages[-limit:]
        return messages
    
    async def list_conversations(self) -> List[ConversationSession]:
        """모든 대화 세션 목록"""
        return list(self.conversations.values())
    
    async def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """등록된 모든 에이전트 목록"""
        agents = {
            "local": {
                "agent_id": self.local_agent.agent_id,
                "name": self.local_agent.agent_name,
                "status": self.local_agent.status,
                "type": "local"
            }
        }
        
        for agent_id, agent in self.external_agents.items():
            agents[agent_id] = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "url": agent.url,
                "capabilities": agent.capabilities,
                "status": agent.status,
                "last_contact": agent.last_contact.isoformat() if agent.last_contact else None,
                "type": "external"
            }
        
        return agents
    
    async def end_conversation(self, session_id: str):
        """대화 세션 종료"""
        if session_id in self.conversations:
            self.conversations[session_id].status = "ended"
            logger.info(f"Conversation ended: {session_id}")
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """대화 세션 요약"""
        if session_id not in self.conversations:
            return {}
        
        session = self.conversations[session_id]
        messages = self.messages.get(session_id, [])
        
        # 참여자별 메시지 수 계산
        participant_stats = {}
        for msg in messages:
            if msg.sender_id not in participant_stats:
                participant_stats[msg.sender_id] = {"count": 0, "name": msg.sender_name}
            participant_stats[msg.sender_id]["count"] += 1
        
        return {
            "session_id": session_id,
            "title": session.title,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "total_messages": len(messages),
            "participants": len(session.participants),
            "participant_stats": participant_stats,
            "duration_minutes": (session.last_activity - session.created_at).total_seconds() / 60
        }