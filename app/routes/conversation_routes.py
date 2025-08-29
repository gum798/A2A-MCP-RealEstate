"""
Multi-Agent Conversation API Routes
다중 에이전트 대화 API 엔드포인트
"""

import asyncio
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.agent.multi_agent_conversation import MultiAgentConversation, ExternalAgent
from app.agent.a2a_agent import A2AAgent
from app.utils.config import settings
from app.utils.logger import logger

router = APIRouter()

# 글로벌 대화 관리자
local_agent = A2AAgent(settings.agent_id, settings.agent_name)
conversation_manager = MultiAgentConversation(local_agent)


class AgentDiscoveryRequest(BaseModel):
    agent_url: str


class ConversationStartRequest(BaseModel):
    title: str
    participant_ids: List[str]


class MessageRequest(BaseModel):
    session_id: str
    content: str
    recipient_id: Optional[str] = None


class BulkAgentAddRequest(BaseModel):
    agents: List[Dict[str, Any]]


@router.post("/agents/discover")
async def discover_agent(request: AgentDiscoveryRequest):
    """새 에이전트 발견 및 추가"""
    try:
        agent = await conversation_manager.discover_and_add_agent(request.agent_url)
        
        if agent:
            return {
                "status": "success",
                "message": f"Agent {agent.name} added successfully",
                "agent": {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": agent.capabilities,
                    "status": agent.status
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to discover or connect to agent"
            )
            
    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/bulk-add")
async def bulk_add_agents(request: BulkAgentAddRequest):
    """여러 에이전트를 한번에 추가"""
    results = []
    
    for agent_data in request.agents:
        try:
            agent_url = agent_data.get('url')
            if not agent_url:
                results.append({
                    "url": agent_data,
                    "status": "failed",
                    "error": "URL is required"
                })
                continue
            
            agent = await conversation_manager.discover_and_add_agent(agent_url)
            if agent:
                results.append({
                    "url": agent_url,
                    "status": "success",
                    "agent_id": agent.agent_id,
                    "name": agent.name
                })
            else:
                results.append({
                    "url": agent_url,
                    "status": "failed",
                    "error": "Connection failed"
                })
                
        except Exception as e:
            results.append({
                "url": agent_data.get('url', 'unknown'),
                "status": "failed",
                "error": str(e)
            })
    
    successful = len([r for r in results if r['status'] == 'success'])
    
    return {
        "total_requested": len(request.agents),
        "successful": successful,
        "failed": len(request.agents) - successful,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/agents")
async def list_agents():
    """등록된 모든 에이전트 목록"""
    try:
        agents = await conversation_manager.list_agents()
        
        return {
            "agents": agents,
            "total_agents": len(agents),
            "local_agent": settings.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/start")
async def start_conversation(request: ConversationStartRequest):
    """새 대화 세션 시작"""
    try:
        session_id = await conversation_manager.start_conversation(
            request.title,
            request.participant_ids
        )
        
        return {
            "session_id": session_id,
            "title": request.title,
            "participants": request.participant_ids,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/message")
async def send_message(request: MessageRequest):
    """대화에 메시지 전송"""
    try:
        message = await conversation_manager.send_message(
            request.session_id,
            request.content,
            request.recipient_id
        )
        
        return {
            "message_id": message.message_id,
            "status": "sent",
            "sender": message.sender_name,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{session_id}/messages")
async def get_conversation_messages(
    session_id: str,
    limit: Optional[int] = Query(None, description="Limit number of messages returned")
):
    """대화 메시지 기록 조회"""
    try:
        messages = await conversation_manager.get_conversation_history(session_id, limit)
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "message_id": msg.message_id,
                    "sender_id": msg.sender_id,
                    "sender_name": msg.sender_name,
                    "recipient_id": msg.recipient_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "message_type": msg.message_type
                }
                for msg in messages
            ],
            "total_messages": len(messages),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations():
    """모든 대화 세션 목록"""
    try:
        conversations = await conversation_manager.list_conversations()
        
        return {
            "conversations": [
                {
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "participants": conv.participants,
                    "status": conv.status,
                    "created_at": conv.created_at.isoformat(),
                    "last_activity": conv.last_activity.isoformat(),
                    "message_count": conv.message_count
                }
                for conv in conversations
            ],
            "total_conversations": len(conversations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{session_id}/summary")
async def get_conversation_summary(session_id: str):
    """대화 세션 요약 정보"""
    try:
        summary = await conversation_manager.get_conversation_summary(session_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{session_id}/end")
async def end_conversation(session_id: str):
    """대화 세션 종료"""
    try:
        await conversation_manager.end_conversation(session_id)
        
        return {
            "session_id": session_id,
            "status": "ended",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-connect")
async def quick_connect():
    """빠른 연결: 알려진 에이전트들과 즉시 대화 시작"""
    try:
        # Socratic Web3 Tutor와 대화 시작
        session_id = await conversation_manager.start_conversation(
            "Quick Chat with AI Agents",
            ["socratic-web3-tutor"]
        )
        
        # 환영 메시지 전송
        welcome_msg = await conversation_manager.send_message(
            session_id,
            "Hello! I'm interested in learning about Web3 and blockchain. Can you help me understand the basics?",
            "socratic-web3-tutor"
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": "Quick conversation started with Socratic Web3 AI Tutor",
            "welcome_message_id": welcome_msg.message_id,
            "chat_url": f"/api/conversations/{session_id}/messages",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick connect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/web3-learning")
async def demo_web3_learning_session():
    """데모: Web3 학습 세션"""
    try:
        # Web3 학습 대화 시작
        session_id = await conversation_manager.start_conversation(
            "Web3 Learning Session",
            ["socratic-web3-tutor"]
        )
        
        # 학습 주제들
        learning_topics = [
            "What is Web3 and how is it different from Web2?",
            "Can you explain blockchain technology in simple terms?",
            "What are smart contracts and why are they important?",
            "How do decentralized applications (dApps) work?"
        ]
        
        responses = []
        for topic in learning_topics:
            message = await conversation_manager.send_message(
                session_id,
                topic,
                "socratic-web3-tutor"
            )
            responses.append({
                "topic": topic,
                "message_id": message.message_id,
                "timestamp": message.timestamp.isoformat()
            })
            
            # 응답 대기 (실제 에이전트 응답을 위해)
            await asyncio.sleep(2)
        
        return {
            "session_id": session_id,
            "title": "Web3 Learning Session",
            "topics_covered": len(learning_topics),
            "responses": responses,
            "status": "completed",
            "view_url": f"/api/conversations/{session_id}/messages",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))