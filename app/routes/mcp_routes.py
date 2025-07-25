"""
MCP (Model Context Protocol) 관련 라우트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

from ..mcp.real_estate_server import real_estate_api, RealEstateAPI
from ..utils.logger import logger
from ..utils.config import settings
router = APIRouter(prefix="/api/mcp", tags=["MCP"])

class RealEstateQuery(BaseModel):
    """부동산 조회 요청 모델"""
    lawd_cd: str  # 지역코드 (5자리)
    deal_ymd: str  # 계약년월 (YYYYMM)

class MCPResponse(BaseModel):
    """MCP 응답 모델"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

@router.get("/status")
async def get_mcp_status():
    """MCP 서버 상태 확인"""
    try:
        has_api_key = bool(settings.molit_api_key)
        return MCPResponse(
            success=True,
            data={
                "server_name": "korean-realestate",
                "version": "1.0.0",
                "api_key_configured": has_api_key,
                "available_tools": [
                    "get_apartment_trade",
                    "get_apartment_rent", 
                    "get_officetel_trade"
                ]
            },
            message="MCP 서버가 정상적으로 작동 중입니다."
        )
    except Exception as e:
        logger.error(f"MCP 상태 확인 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions")
async def get_region_codes():
    """지역 코드 정보 조회"""
    try:
        regions = {
            "서울특별시": {
                "강남구": "11680",
                "강동구": "11740", 
                "강북구": "11305",
                "강서구": "11500",
                "관악구": "11620",
                "광진구": "11215",
                "구로구": "11530",
                "금천구": "11545",
                "노원구": "11350",
                "도봉구": "11320",
                "동대문구": "11230",
                "동작구": "11590",
                "마포구": "11440",
                "서대문구": "11410",
                "서초구": "11650",
                "성동구": "11200",
                "성북구": "11290",
                "송파구": "11710",
                "양천구": "11470",
                "영등포구": "11560",
                "용산구": "11170",
                "은평구": "11380",
                "종로구": "11110",
                "중구": "11140",
                "중랑구": "11260"
            },
            "경기도": {
                "수원시": "41110",
                "성남시": "41130",
                "고양시": "41280",
                "용인시": "41460",
                "부천시": "41190",
                "안산시": "41270",
                "안양시": "41170",
                "남양주시": "41360",
                "화성시": "41590",
                "평택시": "41220"
            }
        }
        
        return MCPResponse(
            success=True,
            data=regions,
            message="지역 코드 정보를 성공적으로 조회했습니다."
        )
    except Exception as e:
        logger.error(f"지역 코드 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apartment/trade")
async def get_apartment_trade(query: RealEstateQuery):
    """아파트 매매 실거래가 조회"""
    try:
        if not settings.molit_api_key:
            raise HTTPException(
                status_code=400, 
                detail="국토교통부 API 키가 설정되지 않았습니다. MOLIT_API_KEY 환경변수를 설정해주세요."
            )
        
        result = await real_estate_api.get_apartment_trade(
            query.lawd_cd, 
            query.deal_ymd
        )
        
        if "error" in result:
            return MCPResponse(
                success=False,
                error=result["error"],
                message="아파트 매매 실거래가 조회 중 오류가 발생했습니다."
            )
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"아파트 매매 실거래가 조회 완료 ({query.lawd_cd}, {query.deal_ymd})"
        )
        
    except Exception as e:
        logger.error(f"아파트 매매 실거래가 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apartment/rent") 
async def get_apartment_rent(query: RealEstateQuery):
    """아파트 전월세 실거래가 조회"""
    try:
        if not settings.molit_api_key:
            raise HTTPException(
                status_code=400,
                detail="국토교통부 API 키가 설정되지 않았습니다. MOLIT_API_KEY 환경변수를 설정해주세요."
            )
        
        result = await real_estate_api.get_apartment_rent(
            query.lawd_cd,
            query.deal_ymd
        )
        
        if "error" in result:
            return MCPResponse(
                success=False,
                error=result["error"], 
                message="아파트 전월세 실거래가 조회 중 오류가 발생했습니다."
            )
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"아파트 전월세 실거래가 조회 완료 ({query.lawd_cd}, {query.deal_ymd})"
        )
        
    except Exception as e:
        logger.error(f"아파트 전월세 실거래가 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/officetel/trade")
async def get_officetel_trade(query: RealEstateQuery):
    """오피스텔 매매 실거래가 조회"""
    try:
        if not settings.molit_api_key:
            raise HTTPException(
                status_code=400,
                detail="국토교통부 API 키가 설정되지 않았습니다. MOLIT_API_KEY 환경변수를 설정해주세요."
            )
        
        result = await real_estate_api.get_officetel_trade(
            query.lawd_cd,
            query.deal_ymd
        )
        
        if "error" in result:
            return MCPResponse(
                success=False,
                error=result["error"],
                message="오피스텔 매매 실거래가 조회 중 오류가 발생했습니다."
            )
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"오피스텔 매매 실거래가 조회 완료 ({query.lawd_cd}, {query.deal_ymd})"
        )
        
    except Exception as e:
        logger.error(f"오피스텔 매매 실거래가 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_available_tools():
    """사용 가능한 MCP 도구 목록"""
    try:
        tools = [
            {
                "name": "get_apartment_trade",
                "description": "아파트 매매 실거래가 조회",
                "parameters": {
                    "lawd_cd": "지역코드 (5자리, 예: 11680)",
                    "deal_ymd": "계약년월 (YYYYMM, 예: 202401)"
                }
            },
            {
                "name": "get_apartment_rent", 
                "description": "아파트 전월세 실거래가 조회",
                "parameters": {
                    "lawd_cd": "지역코드 (5자리, 예: 11680)",
                    "deal_ymd": "계약년월 (YYYYMM, 예: 202401)"
                }
            },
            {
                "name": "get_officetel_trade",
                "description": "오피스텔 매매 실거래가 조회", 
                "parameters": {
                    "lawd_cd": "지역코드 (5자리, 예: 11680)",
                    "deal_ymd": "계약년월 (YYYYMM, 예: 202401)"
                }
            }
        ]
        
        return MCPResponse(
            success=True,
            data={"tools": tools},
            message="사용 가능한 MCP 도구 목록을 조회했습니다."
        )
        
    except Exception as e:
        logger.error(f"MCP 도구 목록 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))