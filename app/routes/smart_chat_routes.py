"""
Smart Chat Routes
자연어 에이전트 전환이 가능한 스마트 채팅 API
"""

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.agent.smart_agent_router import SmartAgentRouter
from app.agent.multi_agent_conversation import MultiAgentConversation
from app.agent.a2a_agent import A2AAgent
from app.utils.config import settings
from app.utils.logger import logger

router = APIRouter()

# 글로벌 스마트 라우터
local_agent = A2AAgent(settings.agent_id, settings.agent_name)
conversation_manager = MultiAgentConversation(local_agent)
smart_router = SmartAgentRouter(conversation_manager)


class ChatMessage(BaseModel):
    message: str
    auto_switch: bool = True  # 자동 에이전트 전환 허용


class AgentSwitchRequest(BaseModel):
    agent_id: str
    initial_message: Optional[str] = None


@router.post("/chat")
async def smart_chat(chat_request: ChatMessage):
    """스마트 채팅 - 자연어로 에이전트 전환 및 대화"""
    try:
        user_message = chat_request.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # 1. 메시지 분석 (에이전트 전환 필요성 판단)
        needs_switch, target_agent, switch_message = await smart_router.process_message(user_message)
        
        response_data = {
            "user_message": user_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # 2. 에이전트 전환이 필요한 경우
        if needs_switch and target_agent and chat_request.auto_switch:
            logger.info(f"Switching to agent: {target_agent}")
            
            switch_result = await smart_router.switch_to_agent(target_agent, user_message)
            
            if switch_result["success"]:
                response_data.update({
                    "action": "agent_switched",
                    "switched_to": switch_result["agent_name"],
                    "switch_message": switch_result["message"],
                    "session_id": switch_result["session_id"]
                })
                
                # 응답 기다리기 (타임아웃 늘림)
                agent_response = await smart_router.get_latest_response(timeout_seconds=35)
                if agent_response:
                    response_data["agent_response"] = {
                        "sender": agent_response.sender_name,
                        "content": agent_response.content,
                        "timestamp": agent_response.timestamp.isoformat()
                    }
                else:
                    response_data["agent_response"] = {
                        "sender": switch_result["agent_name"],
                        "content": "안녕하세요! 무엇을 도와드릴까요?",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                response_data.update({
                    "action": "switch_failed",
                    "error": switch_result["error"],
                    "fallback_message": "죄송합니다. 에이전트 전환에 실패했습니다."
                })
        
        # 3. 기존 에이전트와 계속 대화
        elif smart_router.current_agent_id:
            send_result = await smart_router.send_message_to_current_agent(user_message)
            
            if send_result["success"]:
                response_data["action"] = "message_sent"
                response_data["session_id"] = send_result["session_id"]
                
                # 에이전트 응답 기다리기
                agent_response = await smart_router.get_latest_response(timeout_seconds=35)
                if agent_response:
                    response_data["agent_response"] = {
                        "sender": agent_response.sender_name,
                        "content": agent_response.content,
                        "timestamp": agent_response.timestamp.isoformat()
                    }
                else:
                    response_data["agent_response"] = {
                        "content": "응답을 기다리는 중입니다...",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                response_data.update({
                    "action": "send_failed",
                    "error": send_result["error"]
                })
        
        # 4. 추천 에이전트가 있지만 자동 전환이 비활성화된 경우
        elif target_agent and not chat_request.auto_switch:
            response_data.update({
                "action": "agent_recommended",
                "recommended_agent": target_agent,
                "recommendation_message": switch_message,
                "auto_switch": False
            })
        
        # 5. 첫 대화이거나 적절한 에이전트가 없는 경우
        else:
            response_data.update({
                "action": "general_response",
                "message": "안녕하세요! 어떤 도움이 필요하신가요?",
                "available_agents": smart_router.list_available_agents(),
                "examples": smart_router.get_switch_examples()
            })
        
        return response_data
        
    except Exception as e:
        logger.error(f"Smart chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-agent")
async def manual_agent_switch(switch_request: AgentSwitchRequest):
    """수동 에이전트 전환"""
    try:
        switch_result = await smart_router.switch_to_agent(
            switch_request.agent_id,
            switch_request.initial_message
        )
        
        if switch_result["success"]:
            response = {
                "success": True,
                "agent_name": switch_result["agent_name"],
                "session_id": switch_result["session_id"],
                "message": switch_result["message"],
                "timestamp": datetime.now().isoformat()
            }
            
            # 초기 메시지가 있었다면 응답 기다리기
            if switch_request.initial_message:
                agent_response = await smart_router.get_latest_response(timeout_seconds=10)
                if agent_response:
                    response["initial_response"] = {
                        "content": agent_response.content,
                        "timestamp": agent_response.timestamp.isoformat()
                    }
            
            return response
        else:
            raise HTTPException(
                status_code=400,
                detail=switch_result["error"]
            )
            
    except Exception as e:
        logger.error(f"Manual agent switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-agent")
async def get_current_agent():
    """현재 활성 에이전트 정보"""
    agent_info = smart_router.get_current_agent_info()
    
    if agent_info:
        return {
            "has_active_agent": True,
            **agent_info,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "has_active_agent": False,
            "available_agents": smart_router.list_available_agents(),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/available-agents")
async def get_available_agents():
    """사용 가능한 에이전트 목록"""
    return {
        "agents": smart_router.list_available_agents(),
        "switch_examples": smart_router.get_switch_examples(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/reset-session")
async def reset_chat_session():
    """채팅 세션 리셋"""
    try:
        await smart_router.reset_session()
        
        return {
            "success": True,
            "message": "채팅 세션이 리셋되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation-history")
async def get_conversation_history(limit: Optional[int] = 10):
    """현재 대화 기록"""
    if not smart_router.current_session_id:
        return {
            "has_conversation": False,
            "message": "활성 대화가 없습니다."
        }
    
    try:
        messages = await smart_router.conversation_manager.get_conversation_history(
            smart_router.current_session_id,
            limit
        )
        
        return {
            "has_conversation": True,
            "session_id": smart_router.current_session_id,
            "messages": [
                {
                    "sender": msg.sender_name,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_user": msg.sender_id == smart_router.conversation_manager.local_agent.agent_id
                }
                for msg in messages
            ],
            "total_messages": len(messages),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get conversation history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-socrates")
async def quick_connect_socrates():
    """소크라테스 튜터와 빠른 연결"""
    try:
        switch_result = await smart_router.switch_to_agent(
            "socratic-web3-tutor",
            "안녕하세요! Web3와 블록체인에 대해 배우고 싶습니다."
        )
        
        if switch_result["success"]:
            # 응답 기다리기
            agent_response = await smart_router.get_latest_response(timeout_seconds=15)
            
            return {
                "success": True,
                "agent_name": "Socratic Web3 AI Tutor",
                "session_id": switch_result["session_id"],
                "welcome_message": "소크라테스 Web3 튜터와 연결되었습니다!",
                "agent_response": {
                    "content": agent_response.content if agent_response else "안녕하세요! Web3에 대해 무엇이든 물어보세요.",
                    "timestamp": agent_response.timestamp.isoformat() if agent_response else datetime.now().isoformat()
                },
                "suggestions": [
                    "Web3가 무엇인가요?",
                    "블록체인의 핵심 개념을 설명해주세요",
                    "스마트 컨트랙트는 어떻게 작동하나요?",
                    "DeFi의 장점은 무엇인가요?"
                ]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"소크라테스 튜터 연결 실패: {switch_result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Quick Socrates connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-message")
async def analyze_user_message(message: str):
    """사용자 메시지 분석 (에이전트 전환 의도 파악)"""
    try:
        needs_switch, target_agent, switch_message = await smart_router.process_message(message)
        
        return {
            "message": message,
            "needs_agent_switch": needs_switch,
            "recommended_agent": target_agent,
            "switch_message": switch_message,
            "analysis": {
                "detected_keywords": smart_router._recommend_agent_by_keywords(message),
                "detected_agent": smart_router._identify_target_agent(message)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Message analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))