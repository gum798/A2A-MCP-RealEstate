"""
Character Agent Routes
투심이와 삼돌이 캐릭터 에이전트 API 라우트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from app.agent.character_agents import character_manager
from app.agent.llm_character_agents import llm_character_manager
from app.utils.logger import logger

router = APIRouter()

class PropertyAnalysisRequest(BaseModel):
    property_data: Dict[str, Any]
    user_message: Optional[str] = ""

class ChatRequest(BaseModel):
    message: str
    property_data: Optional[Dict[str, Any]] = None

@router.post("/analyze")
async def analyze_property_with_characters(request: PropertyAnalysisRequest):
    """투심이와 삼돌이가 함께 부동산 분석"""
    try:
        # LLM 기반 분석 사용
        analysis = await llm_character_manager.analyze_property_with_llm(
            request.property_data, 
            request.user_message
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Character analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/chat")
async def chat_with_characters(request: ChatRequest):
    """캐릭터들과 대화"""
    try:
        if request.property_data:
            # 부동산 데이터가 있으면 LLM 기반 분석과 함께 대화
            analysis = await llm_character_manager.analyze_property_with_llm(
                request.property_data,
                request.message
            )
            
            return {
                "status": "success",
                "type": "analysis_chat",
                "투심이": analysis["투심이_분석"]["comment"],
                "삼돌이": analysis["삼돌이_분석"]["comment"],
                "투심이_질문": analysis["투심이_분석"]["questions"],
                "삼돌이_질문": analysis["삼돌이_분석"]["questions"],
                "종합의견": analysis["종합_의견"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 일반 대화 - LLM 기반으로 개선
            sample_property = {
                "address": "사용자가 제공한 주소가 없습니다",
                "message": request.message
            }
            analysis = await llm_character_manager.analyze_property_with_llm(
                sample_property, 
                request.message
            )
            
            return {
                "status": "success",
                "type": "general_chat",
                "투심이": analysis["투심이_분석"]["comment"],
                "삼돌이": analysis["삼돌이_분석"]["comment"],
                "투심이_질문": analysis["투심이_분석"]["questions"],
                "삼돌이_질문": analysis["삼돌이_분석"]["questions"],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Character chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )

@router.get("/characters")
async def get_character_info():
    """캐릭터 정보 조회"""
    return {
        "투심이": {
            "name": "투심이",
            "role": "투자가치 평가",
            "personality": "투자 중심적, 현실적, 수익성 추구",
            "focus_areas": ["가격", "면적", "층수", "교통", "미래가치"],
            "description": "부동산을 투자 관점에서 분석하고 수익성을 중시하는 캐릭터"
        },
        "삼돌이": {
            "name": "삼돌이", 
            "role": "삶의질가치 평가",
            "personality": "생활 중심적, 감성적, 편안함 추구",
            "focus_areas": ["환경", "편의성", "안전", "교육", "문화"],
            "description": "실제 거주할 때의 생활 편의성과 환경을 중시하는 캐릭터"
        },
        "interaction_style": "서로 친한 척 하지만 약간 견제하며 각자의 관점에서 사용자를 설득하려 함"
    }

@router.get("/conversation-history")
async def get_conversation_history():
    """대화 기록 조회"""
    try:
        return {
            "status": "success",
            "history": llm_character_manager.conversation_history[-10:],  # 최근 10개
            "total_conversations": len(llm_character_manager.conversation_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )

@router.delete("/conversation-history")
async def clear_conversation_history():
    """대화 기록 초기화"""
    try:
        llm_character_manager.conversation_history.clear()
        return {
            "status": "success",
            "message": "대화 기록이 초기화되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )