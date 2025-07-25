"""
AI 기능 API 라우트
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.ai.gemini_service import gemini_service
from app.utils.logger import logger

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"


class DataAnalysisRequest(BaseModel):
    data: Dict[str, Any]
    analysis_type: str = "general"


class DocumentationRequest(BaseModel):
    code: str
    doc_type: str = "api"


class ImprovementRequest(BaseModel):
    description: str
    current_data: Optional[str] = None


class TranslationRequest(BaseModel):
    message: str
    target_lang: str = "ko"


@router.get("/")
async def ai_info():
    """AI API 정보"""
    return {
        "message": "A2A Agent AI Services",
        "powered_by": "Google Gemini CLI",
        "available": gemini_service.gemini_available,
        "endpoints": [
            "/api/ai/chat",
            "/api/ai/analyze-code",
            "/api/ai/analyze-data", 
            "/api/ai/generate-docs",
            "/api/ai/suggest-improvements",
            "/api/ai/translate",
            "/api/ai/status"
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/chat")
async def ai_chat(request: ChatRequest):
    """AI와 자유 대화"""
    try:
        response = await gemini_service.chat(request.prompt, request.context)
        
        return {
            "prompt": request.prompt,
            "response": response,
            "context_provided": request.context is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=f"AI 채팅 오류: {str(e)}")


@router.post("/analyze-code")
async def analyze_code(request: CodeAnalysisRequest):
    """코드 분석"""
    try:
        analysis = await gemini_service.analyze_code(request.code, request.language)
        
        return {
            "language": request.language,
            "code_length": len(request.code),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"코드 분석 오류: {str(e)}")


@router.post("/analyze-data")
async def analyze_data(request: DataAnalysisRequest):
    """데이터 분석"""
    try:
        analysis = await gemini_service.analyze_data(request.data, request.analysis_type)
        
        return {
            "analysis_type": request.analysis_type,
            "data_keys": list(request.data.keys()),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Data analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 분석 오류: {str(e)}")


@router.post("/generate-docs")
async def generate_documentation(request: DocumentationRequest):
    """문서 생성"""
    try:
        documentation = await gemini_service.generate_documentation(request.code, request.doc_type)
        
        return {
            "doc_type": request.doc_type,
            "code_length": len(request.code),
            "documentation": documentation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Documentation generation error: {e}")
        raise HTTPException(status_code=500, detail=f"문서 생성 오류: {str(e)}")


@router.post("/suggest-improvements")
async def suggest_improvements(request: ImprovementRequest):
    """개선사항 제안"""
    try:
        suggestions = await gemini_service.suggest_improvements(
            request.description, 
            request.current_data
        )
        
        return {
            "description": request.description,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Improvement suggestion error: {e}")
        raise HTTPException(status_code=500, detail=f"개선사항 제안 오류: {str(e)}")


@router.post("/translate")
async def translate_message(request: TranslationRequest):
    """텍스트 번역"""
    try:
        translation = await gemini_service.translate_message(request.message, request.target_lang)
        
        return {
            "original": request.message,
            "target_language": request.target_lang,
            "translation": translation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"번역 오류: {str(e)}")


@router.get("/status")
async def ai_status():
    """AI 서비스 상태"""
    return {
        "gemini_cli_available": gemini_service.gemini_available,
        "service_status": "active" if gemini_service.gemini_available else "unavailable",
        "capabilities": [
            "chat", "code_analysis", "data_analysis", 
            "documentation", "improvements", "translation"
        ] if gemini_service.gemini_available else [],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/analyze-project")
async def analyze_current_project():
    """현재 프로젝트 분석"""
    try:
        # 현재 프로젝트의 주요 파일들 분석
        analysis_prompt = """
현재 A2A Agent 프로젝트를 분석해주세요.

프로젝트 구조와 주요 구성요소:
1. FastAPI 기반 웹 서버
2. A2A Agent 통신 기능
3. 샘플 데이터 제공
4. AI 통합 (Gemini CLI)

분석 요청:
1. 현재 프로젝트의 강점
2. 개선할 수 있는 부분
3. 추가할 수 있는 기능들
4. 아키텍처 개선 제안

한국어로 답변해주세요.
"""
        
        analysis = await gemini_service.chat(analysis_prompt)
        
        return {
            "project": "A2A Agent",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Project analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"프로젝트 분석 오류: {str(e)}")


@router.post("/smart-response")
async def smart_agent_response(agent_data: Dict[str, Any]):
    """에이전트 데이터를 AI가 분석해서 지능형 응답 생성"""
    try:
        prompt = f"""
A2A Agent 시스템에서 다음 데이터를 받았습니다:

{agent_data}

이 데이터를 분석하고 다음을 제공해주세요:
1. 데이터의 의미와 중요성
2. 다른 에이전트들에게 전달할 핵심 정보
3. 필요한 후속 조치
4. 비즈니스적 인사이트

JSON 형태로 구조화해서 한국어로 답변해주세요.
"""
        
        smart_response = await gemini_service.chat(prompt)
        
        return {
            "input_data": agent_data,
            "ai_analysis": smart_response,
            "response_type": "smart_agent_response",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Smart response error: {e}")
        raise HTTPException(status_code=500, detail=f"지능형 응답 생성 오류: {str(e)}")