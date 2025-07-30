"""
MCP 클라이언트 유틸리티
FastMCP 서버와 통신하기 위한 클라이언트
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.logger import logger

class MCPClient:
    """MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.logger = logger.bind(client="MCP")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        try:
            # MCP 서버 실행 및 도구 호출을 위한 임시 스크립트 생성
            # 프로젝트 루트 경로 계산
            project_root = Path(__file__).parent.parent.parent
            mcp_module_path = self.server_script_path.replace("/", ".").replace(".py", "")
            
            script_content = f'''
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path("{project_root}")
sys.path.insert(0, str(project_root))

import json

async def main():
    try:
        # MCP 서버 모듈 동적 임포트
        from {mcp_module_path} import mcp
        
        # 도구 실행
        result = await mcp.get_tool("{tool_name}")(**{arguments})
        print(json.dumps(result, ensure_ascii=False, default=str))
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            # 임시 파일 생성 및 실행
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            try:
                # Python 스크립트 실행
                result = subprocess.run(
                    ['python', temp_script],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                if result.returncode == 0:
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "error": "JSON 파싱 오류",
                            "raw_output": result.stdout
                        }
                else:
                    return {
                        "success": False,
                        "error": f"스크립트 실행 오류: {result.stderr}",
                        "return_code": result.returncode
                    }
                    
            finally:
                # 임시 파일 삭제
                try:
                    os.unlink(temp_script)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"MCP 도구 호출 중 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "MCP 클라이언트 오류"
            }
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """MCP 리소스 목록 조회"""
        # 실제 구현에서는 MCP 프로토콜을 사용해야 하지만
        # 여기서는 간단한 목 데이터 반환
        return [
            {
                "uri": "realestate://regions",
                "name": "지역 코드 정보",
                "description": "부동산 조회를 위한 행정구역 코드 정보"
            },
            {
                "uri": "realestate://guide", 
                "name": "사용 가이드",
                "description": "부동산 추천 시스템 사용 방법"
            }
        ]
    
    async def read_resource(self, uri: str) -> str:
        """MCP 리소스 읽기"""
        # 실제 구현에서는 MCP 프로토콜을 사용해야 하지만
        # 여기서는 간단한 구현
        if uri == "realestate://regions":
            return json.dumps({
                "서울특별시": {
                    "강남구": "11680",
                    "강서구": "11500",
                    "관악구": "11620"
                }
            }, ensure_ascii=False, indent=2)
        
        return "리소스를 찾을 수 없습니다."

# 전역 MCP 클라이언트 인스턴스들
real_estate_client = MCPClient("app.mcp.real_estate_recommendation_mcp")
location_client = MCPClient("app.mcp.location_service")

async def call_real_estate_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """부동산 MCP 도구 호출 (직접 함수 호출 방식)"""
    try:
        # 도구별 직접 함수 호출
        if tool_name == "get_real_estate_data":
            from ..mcp.real_estate_recommendation_mcp import get_real_estate_data
            result = await get_real_estate_data(**arguments)
        elif tool_name == "analyze_location":
            from ..mcp.real_estate_recommendation_mcp import analyze_location
            result = await analyze_location(**arguments)
        elif tool_name == "evaluate_investment_value":
            from ..mcp.real_estate_recommendation_mcp import evaluate_investment_value
            result = await evaluate_investment_value(**arguments)
        elif tool_name == "evaluate_life_quality":
            from ..mcp.real_estate_recommendation_mcp import evaluate_life_quality
            result = await evaluate_life_quality(**arguments)
        elif tool_name == "recommend_property":
            from ..mcp.real_estate_recommendation_mcp import recommend_property
            result = await recommend_property(**arguments)
        else:
            return {"success": False, "error": f"도구 '{tool_name}'을 찾을 수 없습니다"}
            
        return {"success": True, "data": result}
            
    except Exception as e:
        logger.error(f"부동산 MCP 도구 호출 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"MCP 도구 '{tool_name}' 호출 실패"
        }

async def call_location_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """위치 MCP 도구 호출 (직접 함수 호출 방식)"""
    try:
        # 도구별 직접 함수 호출
        if tool_name == "find_nearest_subway_stations":
            from ..mcp.location_service import find_nearest_subway_stations
            result = await find_nearest_subway_stations(**arguments)
        elif tool_name == "address_to_coordinates":
            from ..mcp.location_service import address_to_coordinates
            result = await address_to_coordinates(**arguments)
        elif tool_name == "find_nearby_facilities":
            from ..mcp.location_service import find_nearby_facilities
            result = await find_nearby_facilities(**arguments)
        elif tool_name == "calculate_location_score":
            from ..mcp.location_service import calculate_location_score
            result = await calculate_location_score(**arguments)
        else:
            return {"success": False, "error": f"도구 '{tool_name}'을 찾을 수 없습니다"}
            
        return {"success": True, "data": result}
            
    except Exception as e:
        logger.error(f"위치 MCP 도구 호출 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"MCP 도구 '{tool_name}' 호출 실패"
        }