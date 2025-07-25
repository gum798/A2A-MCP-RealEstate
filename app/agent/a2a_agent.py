"""
A2A Agent Core Implementation
"""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import httpx

from app.utils.logger import logger


class AgentMessage(BaseModel):
    """에이전트 메시지 모델"""
    id: str
    source_agent_id: str
    target_agent_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str


class AgentConnection(BaseModel):
    """에이전트 연결 정보"""
    agent_id: str
    url: str
    status: str
    last_ping: Optional[datetime] = None


class A2AAgent:
    """A2A 에이전트 핵심 클래스"""
    
    def __init__(self, agent_id: str = None, agent_name: str = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.agent_name = agent_name or "A2A_Python_Agent"
        self.connections: Dict[str, AgentConnection] = {}
        self.message_queue: List[Dict] = []
        self.status = "active"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"A2A Agent initialized: {self.agent_name} ({self.agent_id})")
    
    async def connect(self, target_agent_url: str, target_agent_id: str) -> bool:
        """다른 에이전트와 연결 설정"""
        try:
            handshake_data = {
                "source_agent_id": self.agent_id,
                "source_agent_name": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
            
            response = await self.client.post(
                f"{target_agent_url}/api/agent/handshake",
                json=handshake_data
            )
            
            if response.status_code == 200:
                self.connections[target_agent_id] = AgentConnection(
                    agent_id=target_agent_id,
                    url=target_agent_url,
                    status="connected",
                    last_ping=datetime.now()
                )
                
                logger.info(f"Connected to agent {target_agent_id} at {target_agent_url}")
                return True
            else:
                logger.error(f"Failed to connect to {target_agent_url}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error to {target_agent_url}: {str(e)}")
            return False
    
    async def send_message(self, target_agent_id: str, message_type: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """메시지 전송"""
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
    
    async def receive_message(self, message_data: Dict) -> Dict:
        """메시지 수신 처리"""
        message = AgentMessage(**message_data)
        
        logger.info(f"Received message from {message.source_agent_id}: {message.id}")
        
        # 메시지 큐에 추가
        self.message_queue.append({
            **message.model_dump(),
            "received_at": datetime.now().isoformat()
        })
        
        # 메시지 타입별 처리
        if message.message_type == "ping":
            return await self._handle_ping(message)
        elif message.message_type == "data_request":
            return await self._handle_data_request(message)
        elif message.message_type == "data_response":
            return await self._handle_data_response(message)
        else:
            return {
                "status": "received",
                "message_id": message.id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_ping(self, message: AgentMessage) -> Dict:
        """Ping 메시지 처리"""
        return {
            "status": "pong",
            "message_id": message.id,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_data_request(self, message: AgentMessage) -> Dict:
        """데이터 요청 처리"""
        data_type = message.payload.get("data_type", "unknown")
        sample_data = await self._get_sample_data(data_type)
        
        return {
            "status": "data_response",
            "message_id": message.id,
            "data": sample_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_data_response(self, message: AgentMessage) -> Dict:
        """데이터 응답 처리"""
        logger.info(f"Received data response: {message.payload}")
        return {
            "status": "acknowledged",
            "message_id": message.id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_sample_data(self, data_type: str) -> Dict:
        """샘플 데이터 생성"""
        sample_data = {
            "user_data": [
                {"id": 1, "name": "김철수", "email": "kim@example.com"},
                {"id": 2, "name": "이영희", "email": "lee@example.com"}
            ],
            "order_data": [
                {"order_id": "ORD001", "amount": 100500, "status": "completed"},
                {"order_id": "ORD002", "amount": 250750, "status": "pending"}
            ],
            "system_status": {
                "cpu": "45%",
                "memory": "62%",
                "disk": "34%",
                "uptime": "5 days"
            }
        }
        
        return sample_data.get(data_type, {"message": "No data available for this type"})
    
    async def ping_agent(self, target_agent_id: str) -> Optional[Dict]:
        """에이전트 Ping 테스트"""
        return await self.send_message(
            target_agent_id,
            "ping",
            {"message": "ping test", "timestamp": datetime.now().isoformat()}
        )
    
    def get_status(self) -> Dict:
        """에이전트 상태 반환"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "connections": [conn.model_dump() for conn in self.connections.values()],
            "message_queue_count": len(self.message_queue),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """리소스 정리"""
        await self.client.aclose()
        logger.info(f"Agent {self.agent_id} cleaned up")