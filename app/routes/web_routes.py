"""
웹 인터페이스 라우트
MCP와 Agent 기능을 테스트할 수 있는 웹페이지 제공
"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from datetime import datetime

from ..utils.logger import logger
from ..utils.fastmcp_client import (
    call_real_estate_mcp_tool,
    get_real_estate_resources,
    read_real_estate_resource,
    get_real_estate_tools,
    call_location_mcp_tool,
    get_location_tools,
    get_location_resources,
    read_location_resource
)
from ..data.region_codes import get_sido_list, get_sigungu_list, get_emd_list, get_complex_list

router = APIRouter(prefix="/web", tags=["web"])
templates = Jinja2Templates(directory="app/templates")

class MCPTestRequest(BaseModel):
    """MCP 테스트 요청 모델"""
    tool_name: str
    parameters: Dict[str, Any]

class AgentTestRequest(BaseModel):
    """Agent 테스트 요청 모델"""
    address: str
    sido_code: Optional[str] = ""
    sigungu_code: Optional[str] = ""
    eupmyeondong: Optional[str] = ""
    complex_name: Optional[str] = ""
    price: int
    area: float
    area_range: Optional[str] = ""
    floor: int
    total_floor: int
    building_year: int
    property_type: str
    deal_type: str
    user_preference: str = "균형"

# 메인 페이지
@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    """메인 웹페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

# MCP 테스트 페이지
@router.get("/mcp", response_class=HTMLResponse)
async def mcp_test_page(request: Request):
    """MCP 기능 테스트 페이지"""
    return templates.TemplateResponse("mcp_test.html", {"request": request})

# Agent 테스트 페이지
@router.get("/agent", response_class=HTMLResponse)
async def agent_test_page(request: Request):
    """Agent 기능 테스트 페이지"""
    return templates.TemplateResponse("agent_test.html", {"request": request})

# 채팅 페이지
@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """투심이와 삼돌이 채팅 페이지"""
    return templates.TemplateResponse("chat.html", {"request": request})

# A2A 에이전트 채팅 페이지
@router.get("/agent-chat", response_class=HTMLResponse)
async def agent_chat_page(request: Request):
    """A2A 다중 에이전트 채팅 페이지"""
    return templates.TemplateResponse("agent_chat.html", {"request": request})

# 지도 페이지
@router.get("/map", response_class=HTMLResponse)
async def map_view_page(request: Request):
    """지도 기반 부동산 검색 페이지"""
    return templates.TemplateResponse("map_view.html", {
        "request": request,
        "naver_client_id": settings.naver_client_id or "demo_client_id"
    })

# 매물 비교 페이지
@router.get("/compare", response_class=HTMLResponse)
async def compare_page(request: Request):
    """매물 비교 페이지"""
    return templates.TemplateResponse("compare.html", {"request": request})

# MCP API 엔드포인트
@router.post("/api/mcp/test")
async def test_mcp_tool(request: MCPTestRequest):
    """MCP 도구 테스트"""
    try:
        # 실제 MCP 서버 호출
        if request.tool_name in ["get_real_estate_data", "get_real_estate_data_advanced", "analyze_location", "evaluate_investment_value", "evaluate_life_quality", "recommend_property", "get_regional_price_statistics", "compare_similar_properties", "search_by_road_address"]:
            # 부동산 MCP 서버 호출 (진정한 MCP 프로토콜)
            result = await call_real_estate_mcp_tool(request.tool_name, request.parameters)
        elif request.tool_name in ["find_nearest_subway_stations", "address_to_coordinates", "find_nearby_facilities", "calculate_location_score", "get_realtime_traffic_info", "get_subway_realtime_arrival"]:
            # 위치 MCP 서버 호출 (진정한 MCP 프로토콜)
            result = await call_location_mcp_tool(request.tool_name, request.parameters)
        else:
            result = {
                "success": False,
                "error": "지원하지 않는 도구입니다",
                "message": f"'{request.tool_name}' 도구를 찾을 수 없습니다"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"MCP 도구 테스트 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent API 엔드포인트
@router.post("/api/agent/recommend")
async def recommend_property(request: AgentTestRequest):
    """부동산 추천 - 디버깅 강화 버전"""
    try:
        logger.info(f"부동산 추천 요청 시작: {request.address}")
        
        # MCP 서버의 recommend_property 도구 호출
        arguments = {
            "address": request.address,
            "price": request.price,
            "area": request.area,
            "floor": request.floor,
            "total_floor": request.total_floor,
            "building_year": request.building_year,
            "property_type": request.property_type,
            "deal_type": request.deal_type,
            "user_preference": request.user_preference
        }
        
        logger.info(f"MCP 도구 호출 시작, 인자: {arguments}")
        
        # FastMCP 클라이언트를 통한 올바른 MCP 도구 호출
        result = await call_real_estate_mcp_tool("recommend_property", arguments)
        
        logger.info(f"MCP 도구 호출 결과: success={result.get('success')}, message={result.get('message')}")
        
        if result.get("success"):
            return {
                "success": True,
                "data": result.get("data", {}),
                "message": result.get("message", "부동산 추천이 완료되었습니다")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": result.get("message", "MCP 도구 호출 실패"),
                "mcp_result": result  # 원본 MCP 결과도 포함
            }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"부동산 추천 중 오류: {e}")
        logger.error(f"상세 오류: {error_traceback}")
        return {
            "success": False,
            "error": str(e),
            "message": f"부동산 추천 중 오류가 발생했습니다: {str(e)}",
            "traceback": error_traceback,
            "request_data": {
                "address": request.address,
                "price": request.price,
                "area": request.area,
                "floor": request.floor,
                "total_floor": request.total_floor,
                "building_year": request.building_year,
                "property_type": request.property_type,
                "deal_type": request.deal_type,
                "user_preference": request.user_preference
            }
        }

# 투자가치 평가
@router.post("/api/agent/investment")
async def evaluate_investment(request: AgentTestRequest):
    """투자가치 평가 - MCP 방식 사용"""
    try:
        arguments = {
            "address": request.address,
            "price": request.price,
            "area": request.area,
            "floor": request.floor,
            "total_floor": request.total_floor,
            "building_year": request.building_year,
            "property_type": request.property_type,
            "deal_type": request.deal_type
        }
        
        result = await call_real_estate_mcp_tool("evaluate_investment_value", arguments)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "message": result.get("message", "투자가치 평가가 완료되었습니다")
        }
        
    except Exception as e:
        logger.error(f"투자가치 평가 중 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"투자가치 평가 중 오류가 발생했습니다: {str(e)}"
        }

# 삶의질 평가
@router.post("/api/agent/life-quality")
async def evaluate_life_quality(request: AgentTestRequest):
    """삶의질가치 평가 - MCP 방식 사용"""
    try:
        arguments = {
            "address": request.address,
            "price": request.price,
            "area": request.area,
            "floor": request.floor,
            "total_floor": request.total_floor,
            "building_year": request.building_year,
            "property_type": request.property_type,
            "deal_type": request.deal_type
        }
        
        result = await call_real_estate_mcp_tool("evaluate_life_quality", arguments)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "message": result.get("message", "삶의질가치 평가가 완료되었습니다")
        }
        
    except Exception as e:
        logger.error(f"삶의질가치 평가 중 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"삶의질가치 평가 중 오류가 발생했습니다: {str(e)}"
        }

# 실거래가 조회 (폼 기반)
@router.post("/mcp/apartment-trade", response_class=HTMLResponse)
async def get_apartment_trade_form(
    request: Request,
    lawd_cd: str = Form(...),
    deal_ymd: str = Form(...)
):
    """아파트 실거래가 조회 (폼)"""
    try:
        # MCP 서버 호출
        arguments = {
            "lawd_cd": lawd_cd,
            "deal_ymd": deal_ymd,
            "property_type": "아파트"
        }
        
        result = await call_real_estate_mcp_tool("get_real_estate_data", arguments)
        
        return templates.TemplateResponse("mcp_result.html", {
            "request": request,
            "result": result,
            "tool_name": "아파트 매매 실거래가 조회"
        })
        
    except Exception as e:
        logger.error(f"아파트 실거래가 조회 중 오류: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# 부동산 추천 (폼 기반)
@router.post("/agent/recommend", response_class=HTMLResponse)
async def recommend_property_form(
    request: Request,
    address: str = Form(...),
    price: int = Form(...),
    area: float = Form(...),
    floor: int = Form(...),
    total_floor: int = Form(...),
    building_year: int = Form(...),
    property_type: str = Form(...),
    deal_type: str = Form(...),
    user_preference: str = Form(...)
):
    """부동산 추천 (폼)"""
    try:
        arguments = {
            "address": address,
            "price": price,
            "area": area,
            "floor": floor,
            "total_floor": total_floor,
            "building_year": building_year,
            "property_type": property_type,
            "deal_type": deal_type,
            "user_preference": user_preference
        }
        
        result = await call_real_estate_mcp_tool("recommend_property", arguments)
        
        return templates.TemplateResponse("agent_result.html", {
            "request": request,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"부동산 추천 중 오류: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# MCP 관련 엔드포인트
@router.get("/api/mcp/tools")
async def list_mcp_tools():
    """MCP 도구 목록 조회"""
    try:
        tools = await get_real_estate_tools()
        return {
            "success": True,
            "data": tools,
            "message": f"{len(tools)}개의 MCP 도구를 찾았습니다"
        }
    except Exception as e:
        logger.error(f"MCP 도구 목록 조회 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "MCP 도구 목록 조회 실패"
        }

@router.get("/api/mcp/resources")
async def list_mcp_resources():
    """MCP 리소스 목록 조회"""
    try:
        resources = await get_real_estate_resources()
        return {
            "success": True,
            "data": resources,
            "message": f"{len(resources)}개의 MCP 리소스를 찾았습니다"
        }
    except Exception as e:
        logger.error(f"MCP 리소스 목록 조회 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "MCP 리소스 목록 조회 실패"
        }

@router.get("/api/mcp/resources/{uri:path}")
async def read_mcp_resource(uri: str):
    """MCP 리소스 읽기"""
    try:
        content = await read_real_estate_resource(uri)
        return {
            "success": True,
            "data": {
                "uri": uri,
                "content": content
            },
            "message": "MCP 리소스를 성공적으로 읽었습니다"
        }
    except Exception as e:
        logger.error(f"MCP 리소스 읽기 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"MCP 리소스 '{uri}' 읽기 실패"
        }

# 지역코드 관련 API
@router.get("/api/regions/sido")
async def get_sido():
    """시도 목록 조회"""
    try:
        sido_list = get_sido_list()
        return {
            "success": True,
            "data": sido_list,
            "message": f"{len(sido_list)}개의 시도를 조회했습니다"
        }
    except Exception as e:
        logger.error(f"시도 목록 조회 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "시도 목록 조회 실패"
        }

@router.get("/api/regions/sigungu/{sido_code}")
async def get_sigungu(sido_code: str):
    """시군구 목록 조회"""
    try:
        sigungu_list = get_sigungu_list(sido_code)
        return {
            "success": True,
            "data": sigungu_list,
            "message": f"{len(sigungu_list)}개의 시군구를 조회했습니다"
        }
    except Exception as e:
        logger.error(f"시군구 목록 조회 오류: {e}")
        return {
            "success": False, 
            "error": str(e),
            "message": "시군구 목록 조회 실패"
        }

@router.get("/api/regions/emd/{sigungu_code}")
async def get_emd(sigungu_code: str):
    """읍면동 목록 조회"""
    try:
        emd_list = get_emd_list(sigungu_code)
        return {
            "success": True,
            "data": emd_list,
            "message": f"{len(emd_list)}개의 읍면동을 조회했습니다"
        }
    except Exception as e:
        logger.error(f"읍면동 목록 조회 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "읍면동 목록 조회 실패"
        }

@router.get("/api/regions/complex/{sigungu_code}")
async def get_complex(sigungu_code: str, emd_name: str = ""):
    """아파트 단지명 목록 조회"""
    try:
        complex_list = get_complex_list(sigungu_code, emd_name)
        return {
            "success": True,
            "data": complex_list,
            "message": f"{len(complex_list)}개의 단지를 조회했습니다"
        }
    except Exception as e:
        logger.error(f"단지 목록 조회 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "단지 목록 조회 실패"
        }