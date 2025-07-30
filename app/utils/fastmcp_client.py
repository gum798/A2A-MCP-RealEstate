"""
FastMCP와 직접 통신하는 클라이언트
FastMCP의 내부 API를 활용하여 도구와 리소스에 접근
"""

import asyncio
import json
from typing import Dict, Any, List, Optional

from ..utils.logger import logger

class FastMCPClient:
    """FastMCP 서버와 직접 통신하는 클라이언트"""
    
    def __init__(self, module_name: str = "app.mcp.real_estate_recommendation_mcp"):
        self.module_name = module_name
        self.mcp_server = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """MCP 서버 초기화 보장"""
        if not self._initialized:
            try:
                # MCP 서버 모듈 임포트
                if self.module_name == "app.mcp.real_estate_recommendation_mcp":
                    from ..mcp.real_estate_recommendation_mcp import mcp
                elif self.module_name == "app.mcp.location_service":
                    from ..mcp.location_service import mcp
                else:
                    raise ValueError(f"지원하지 않는 모듈: {self.module_name}")
                    
                self.mcp_server = mcp
                self._initialized = True
                logger.info(f"FastMCP 서버 초기화 완료: {self.module_name}")
            except Exception as e:
                logger.error(f"FastMCP 서버 초기화 실패: {e}")
                raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        try:
            await self._ensure_initialized()
            
            # 도구 가져오기 (FastMCP의 get_tool은 비동기)
            tool = await self.mcp_server.get_tool(tool_name)
            if tool is None:
                return {
                    "success": False,
                    "error": f"도구 '{tool_name}'을 찾을 수 없습니다",
                    "message": "MCP 도구를 찾을 수 없습니다"
                }
            
            # 도구 실행 (FunctionTool의 fn 메서드 직접 호출)
            if hasattr(tool, 'fn') and callable(tool.fn):
                # FastMCP의 FunctionTool.fn을 직접 호출
                result = await tool.fn(**arguments)
            elif hasattr(tool, 'run'):
                tool_result = await tool.run(arguments)
                # ToolResult에서 실제 데이터 추출
                if hasattr(tool_result, 'content'):
                    if isinstance(tool_result.content, list) and tool_result.content:
                        # content가 리스트인 경우 첫 번째 항목의 text 추출
                        first_content = tool_result.content[0]
                        if hasattr(first_content, 'text'):
                            try:
                                result = json.loads(first_content.text)
                            except:
                                result = first_content.text
                        else:
                            result = first_content
                    else:
                        result = tool_result.content
                else:
                    result = tool_result
            else:
                result = await tool(**arguments)
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"MCP 도구 '{tool_name}' 호출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"MCP 도구 '{tool_name}' 호출 중 오류가 발생했습니다"
            }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        try:
            await self._ensure_initialized()
            
            # FastMCP의 get_tools 메서드 사용
            tools_dict = await self.mcp_server.get_tools()
            tools = []
            for tool_name, tool_obj in tools_dict.items():
                tools.append({
                    "name": tool_name,
                    "description": getattr(tool_obj, 'description', ''),
                    "parameters": getattr(tool_obj, 'parameters', {}),
                    "enabled": getattr(tool_obj, 'enabled', True)
                })
            
            return tools
            
        except Exception as e:
            logger.error(f"MCP 도구 목록 조회 실패: {e}")
            return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """사용 가능한 리소스 목록 조회"""
        try:
            await self._ensure_initialized()
            
            # FastMCP의 get_resources 메서드 사용
            resources_dict = await self.mcp_server.get_resources()
            resources = []
            for resource_uri, resource_obj in resources_dict.items():
                resources.append({
                    "uri": resource_uri,
                    "name": getattr(resource_obj, 'name', resource_uri),
                    "description": getattr(resource_obj, 'description', '')
                })
            
            return resources
            
        except Exception as e:
            logger.error(f"MCP 리소스 목록 조회 실패: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """MCP 리소스 읽기"""
        try:
            await self._ensure_initialized()
            
            # FastMCP의 get_resource 메서드로 리소스 객체 가져온 후 실행
            resources_dict = await self.mcp_server.get_resources()
            if uri in resources_dict:
                resource_obj = resources_dict[uri]
                if hasattr(resource_obj, 'fn') and callable(resource_obj.fn):
                    content = await resource_obj.fn()
                    return content
                else:
                    return f"리소스 '{uri}'를 실행할 수 없습니다."
            else:
                return f"리소스 '{uri}'를 찾을 수 없습니다."
                
        except Exception as e:
            logger.error(f"MCP 리소스 '{uri}' 읽기 실패: {e}")
            return f"리소스 읽기 오류: {e}"

# 전역 클라이언트 인스턴스들
_real_estate_mcp_client: Optional[FastMCPClient] = None
_location_mcp_client: Optional[FastMCPClient] = None

async def get_real_estate_mcp_client() -> FastMCPClient:
    """부동산 MCP 클라이언트 인스턴스 반환"""
    global _real_estate_mcp_client
    
    if _real_estate_mcp_client is None:
        _real_estate_mcp_client = FastMCPClient("app.mcp.real_estate_recommendation_mcp")
    
    return _real_estate_mcp_client

async def get_location_mcp_client() -> FastMCPClient:
    """위치 MCP 클라이언트 인스턴스 반환"""
    global _location_mcp_client
    
    if _location_mcp_client is None:
        _location_mcp_client = FastMCPClient("app.mcp.location_service")
    
    return _location_mcp_client

async def call_real_estate_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """부동산 MCP 도구 호출"""
    try:
        client = await get_real_estate_mcp_client()
        return await client.call_tool(tool_name, arguments)
        
    except Exception as e:
        logger.error(f"부동산 MCP 도구 호출 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"MCP 도구 '{tool_name}' 호출 실패"
        }

async def get_real_estate_tools() -> List[Dict[str, Any]]:
    """부동산 MCP 도구 목록 조회"""
    try:
        client = await get_real_estate_mcp_client()
        return await client.list_tools()
    except Exception as e:
        logger.error(f"MCP 도구 목록 조회 실패: {e}")
        return []

async def get_real_estate_resources() -> List[Dict[str, Any]]:
    """부동산 MCP 리소스 목록 조회"""
    try:
        client = await get_real_estate_mcp_client()
        return await client.list_resources()
    except Exception as e:
        logger.error(f"MCP 리소스 목록 조회 실패: {e}")
        return []

async def read_real_estate_resource(uri: str) -> str:
    """부동산 MCP 리소스 읽기"""
    try:
        client = await get_real_estate_mcp_client()
        return await client.read_resource(uri)
    except Exception as e:
        logger.error(f"MCP 리소스 읽기 실패: {e}")
        return f"리소스 읽기 오류: {e}"

async def call_location_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """위치 MCP 도구 호출"""
    try:
        client = await get_location_mcp_client()
        return await client.call_tool(tool_name, arguments)
        
    except Exception as e:
        logger.error(f"위치 MCP 도구 호출 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"MCP 도구 '{tool_name}' 호출 실패"
        }

async def get_location_tools() -> List[Dict[str, Any]]:
    """위치 MCP 도구 목록 조회"""
    try:
        client = await get_location_mcp_client()
        return await client.list_tools()
    except Exception as e:
        logger.error(f"위치 MCP 도구 목록 조회 실패: {e}")
        return []

async def get_location_resources() -> List[Dict[str, Any]]:
    """위치 MCP 리소스 목록 조회"""
    try:
        client = await get_location_mcp_client()
        return await client.list_resources()
    except Exception as e:
        logger.error(f"위치 MCP 리소스 목록 조회 실패: {e}")
        return []

async def read_location_resource(uri: str) -> str:
    """위치 MCP 리소스 읽기"""
    try:
        client = await get_location_mcp_client()
        return await client.read_resource(uri)
    except Exception as e:
        logger.error(f"위치 MCP 리소스 읽기 실패: {e}")
        return f"리소스 읽기 오류: {e}"

async def cleanup_mcp_clients():
    """MCP 클라이언트들 정리"""
    global _real_estate_mcp_client, _location_mcp_client
    
    if _real_estate_mcp_client:
        _real_estate_mcp_client = None
    if _location_mcp_client:
        _location_mcp_client = None
        
    logger.info("FastMCP 클라이언트들이 정리되었습니다")