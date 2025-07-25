"""
Agent 통신 라우트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from app.agent.a2a_agent import A2AAgent
from app.utils.config import settings
from app.utils.logger import logger

router = APIRouter()

# 전역 에이전트 인스턴스
agent = A2AAgent(
    agent_id=settings.agent_id,
    agent_name=settings.agent_name
)


class HandshakeRequest(BaseModel):
    source_agent_id: str
    source_agent_name: str
    timestamp: str


class MessageRequest(BaseModel):
    id: str
    source_agent_id: str
    target_agent_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: str


class ConnectionRequest(BaseModel):
    target_agent_url: str
    target_agent_id: str


class SendMessageRequest(BaseModel):
    target_agent_id: str
    message_type: str
    payload: Dict[str, Any]


@router.post("/handshake")
async def handshake(request: HandshakeRequest):
    """핸드셰이크 엔드포인트"""
    logger.info(f"Handshake request from {request.source_agent_name} ({request.source_agent_id})")
    
    return {
        "status": "handshake_accepted",
        "target_agent_id": agent.agent_id,
        "target_agent_name": agent.agent_name,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/message")
async def receive_message(message: MessageRequest):
    """메시지 수신 엔드포인트"""
    try:
        response = await agent.receive_message(message.model_dump())
        return response
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/connect")
async def connect_to_agent(request: ConnectionRequest):
    """연결 설정 엔드포인트"""
    try:
        success = await agent.connect(request.target_agent_url, request.target_agent_id)
        
        if success:
            return {
                "status": "connection_established",
                "target_agent_id": request.target_agent_id,
                "target_agent_url": request.target_agent_url,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to establish connection with {request.target_agent_id}"
            )
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(e)}"
        )


@router.post("/send")
async def send_message(request: SendMessageRequest):
    """메시지 전송 엔드포인트"""
    try:
        response = await agent.send_message(
            request.target_agent_id,
            request.message_type,
            request.payload
        )
        
        return {
            "status": "message_sent",
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/status")
async def get_agent_status():
    """에이전트 상태 조회"""
    return agent.get_status()


@router.post("/ping/{target_agent_id}")
async def ping_agent(target_agent_id: str):
    """Ping 테스트"""
    try:
        response = await agent.ping_agent(target_agent_id)
        
        if response:
            return {
                "status": "ping_sent",
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to send ping"
            )
    except Exception as e:
        logger.error(f"Ping failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ping failed: {str(e)}"
        )


@router.get("/connections")
async def get_connections():
    """연결된 에이전트 목록"""
    return {
        "agent_id": agent.agent_id,
        "connections": [conn.model_dump() for conn in agent.connections.values()],
        "count": len(agent.connections),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/messages")
async def get_message_queue():
    """메시지 큐 조회"""
    return {
        "agent_id": agent.agent_id,
        "messages": agent.message_queue,
        "count": len(agent.message_queue),
        "timestamp": datetime.now().isoformat()
    }