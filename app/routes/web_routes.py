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
from ..utils.mcp_client import call_real_estate_tool, call_location_tool

router = APIRouter(prefix="/web", tags=["web"])
templates = Jinja2Templates(directory="app/templates")

class MCPTestRequest(BaseModel):
    """MCP 테스트 요청 모델"""
    tool_name: str
    parameters: Dict[str, Any]

class AgentTestRequest(BaseModel):
    """Agent 테스트 요청 모델"""
    address: str
    price: int
    area: float
    floor: int
    total_floor: int
    building_year: int
    property_type: str
    deal_type: str
    user_preference: str

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
        if request.tool_name in ["get_real_estate_data", "analyze_location", "evaluate_investment_value", "evaluate_life_quality", "recommend_property"]:
            # 부동산 MCP 서버 호출
            result = await call_real_estate_tool(request.tool_name, request.parameters)
        elif request.tool_name in ["find_nearest_subway_stations", "address_to_coordinates", "find_nearby_facilities", "calculate_location_score"]:
            # 위치 MCP 서버 호출
            result = await call_location_tool(request.tool_name, request.parameters)
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
    """부동산 추천"""
    try:
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
        
        result = await call_real_estate_tool("recommend_property", arguments)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "message": result.get("message", "부동산 추천이 완료되었습니다")
        }
        
    except Exception as e:
        logger.error(f"부동산 추천 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 투자가치 평가
@router.post("/api/agent/investment")
async def evaluate_investment(request: AgentTestRequest):
    """투자가치 평가"""
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
        
        result = await call_real_estate_tool("evaluate_investment_value", arguments)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "message": result.get("message", "투자가치 평가가 완료되었습니다")
        }
        
    except Exception as e:
        logger.error(f"투자가치 평가 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 삶의질 평가
@router.post("/api/agent/life-quality")
async def evaluate_life_quality(request: AgentTestRequest):
    """삶의질가치 평가"""
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
        
        result = await call_real_estate_tool("evaluate_life_quality", arguments)
        
        return {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "message": result.get("message", "삶의질가치 평가가 완료되었습니다")
        }
        
    except Exception as e:
        logger.error(f"삶의질가치 평가 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        result = await call_real_estate_tool("get_real_estate_data", arguments)
        
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
        
        result = await call_real_estate_tool("recommend_property", arguments)
        
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