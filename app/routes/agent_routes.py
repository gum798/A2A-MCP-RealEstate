"""
Agent 통신 라우트
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from app.agent.a2a_agent import A2AAgent
from app.agent.agent_discovery import agent_discovery
from app.agent.json_rpc import rpc_processor
from app.agent.streaming import stream_manager, create_stream_response
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


# Agent Card 관련 엔드포인트
@router.get("/.well-known/agent.json")
async def get_agent_card():
    """Agent Card 조회 (Well-known 엔드포인트)"""
    from fastapi.responses import JSONResponse
    import json
    
    try:
        agent_card = await agent_discovery.load_agent_card()
        # UTF-8 인코딩으로 JSON 응답 반환
        return JSONResponse(
            content=agent_card,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        logger.error(f"Failed to load agent card: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load agent card"
        )


@router.get("/discovery")
async def get_discovery_info():
    """에이전트 디스커버리 정보 조회"""
    try:
        discovery_info = await agent_discovery.get_discovery_info()
        return discovery_info
    except Exception as e:
        logger.error(f"Failed to get discovery info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get discovery info"
        )


@router.post("/discovery/register")
async def register_agent(agent_data: Dict[str, Any]):
    """에이전트 등록"""
    try:
        agent_id = agent_data.get('agent_id')
        if not agent_id:
            raise HTTPException(
                status_code=400,
                detail="agent_id is required"
            )
        
        await agent_discovery.register_agent(agent_id, agent_data)
        return {
            "status": "registered",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register agent: {str(e)}"
        )


@router.post("/discovery/find")
async def find_agents_by_capability(capability_request: Dict[str, str]):
    """기능별 에이전트 검색"""
    try:
        capability = capability_request.get('capability')
        if not capability:
            raise HTTPException(
                status_code=400,
                detail="capability is required"
            )
        
        matching_agents = await agent_discovery.find_agents_by_capability(capability)
        return {
            "capability": capability,
            "matching_agents": matching_agents,
            "count": len(matching_agents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to find agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find agents: {str(e)}"
        )


# JSON-RPC 엔드포인트
@router.post("/rpc")
async def json_rpc_endpoint(request_data: Dict[str, Any]):
    """JSON-RPC 엔드포인트"""
    try:
        response = await rpc_processor.process_request(request_data)
        return response
    except Exception as e:
        logger.error(f"RPC processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RPC processing error: {str(e)}"
        )


# 스트리밍 엔드포인트
@router.get("/stream/{stream_id}")
async def get_stream(stream_id: str, request: Request):
    """스트림 데이터 수신"""
    try:
        return await create_stream_response(stream_id, request)
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Stream error: {str(e)}"
        )


@router.post("/stream/create")
async def create_stream():
    """새 스트림 생성"""
    try:
        stream_id = await stream_manager.create_stream()
        return {
            "stream_id": stream_id,
            "stream_url": f"/api/agent/stream/{stream_id}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to create stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stream: {str(e)}"
        )


@router.post("/stream/{stream_id}/send")
async def send_stream_message(stream_id: str, message_data: Dict[str, Any]):
    """스트림에 메시지 전송"""
    try:
        event = message_data.get('event', 'message')
        data = message_data.get('data', {})
        
        success = await stream_manager.send_message(stream_id, event, data)
        
        if success:
            return {
                "status": "message_sent",
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Stream not found"
            )
    except Exception as e:
        logger.error(f"Failed to send stream message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send stream message: {str(e)}"
        )


@router.get("/stream/{stream_id}/info")
async def get_stream_info(stream_id: str):
    """스트림 정보 조회"""
    try:
        stream_info = stream_manager.get_stream_info(stream_id)
        if stream_info:
            return stream_info
        else:
            raise HTTPException(
                status_code=404,
                detail="Stream not found"
            )
    except Exception as e:
        logger.error(f"Failed to get stream info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stream info: {str(e)}"
        )


@router.get("/streams")
async def get_all_streams():
    """모든 스트림 정보 조회"""
    try:
        streams_info = stream_manager.get_all_streams_info()
        return streams_info
    except Exception as e:
        logger.error(f"Failed to get streams info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streams info: {str(e)}"
        )