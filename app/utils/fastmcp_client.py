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
    
    async def _get_direct_function_map(self) -> Dict[str, Any]:
        """직접 함수 매핑 - 최후의 수단"""
        if self.module_name == "app.mcp.real_estate_recommendation_mcp":
            from ..mcp import real_estate_recommendation_mcp
            return {
                "get_real_estate_data": real_estate_recommendation_mcp.get_real_estate_data_advanced,
                "analyze_location": real_estate_recommendation_mcp.analyze_location,
                "evaluate_investment_value": real_estate_recommendation_mcp.evaluate_investment_value,
                "evaluate_life_quality": real_estate_recommendation_mcp.evaluate_life_quality,
                "recommend_property": real_estate_recommendation_mcp.recommend_property,
                "get_regional_price_statistics": real_estate_recommendation_mcp.get_regional_price_statistics,
                "compare_similar_properties": real_estate_recommendation_mcp.compare_similar_properties,
                "search_by_road_address": real_estate_recommendation_mcp.search_by_road_address
            }
        elif self.module_name == "app.mcp.location_service":
            from ..mcp import location_service
            return {
                "find_nearest_subway_stations": location_service.find_nearest_subway_stations,
                "address_to_coordinates": location_service.address_to_coordinates,
                "find_nearby_facilities": location_service.find_nearby_facilities,
                "calculate_location_score": location_service.calculate_location_score,
                "get_realtime_traffic_info": location_service.get_realtime_traffic_info,
                "get_subway_realtime_arrival": location_service.get_subway_realtime_arrival
            }
        else:
            return {}
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출 - FastMCP의 실제 구조 확인 후 호출"""
        try:
            await self._ensure_initialized()
            
            logger.info(f"MCP 도구 '{tool_name}' 호출 시작, 인자: {arguments}")
            
            # FastMCP 객체의 실제 속성과 메서드 확인
            mcp_methods = [method for method in dir(self.mcp_server) if not method.startswith('_')]
            logger.info(f"FastMCP 사용 가능한 메서드들: {mcp_methods}")
            
            # FastMCP 도구 호출 - 여러 방법 시도
            result = None
            tool = None
            
            # 1단계: call_tool 메서드가 있는지 확인
            if hasattr(self.mcp_server, 'call_tool'):
                logger.info("방법 1: call_tool 메서드 사용 시도")
                try:
                    result = await self.mcp_server.call_tool(tool_name, arguments)
                except Exception as e:
                    logger.warning(f"call_tool 방법 실패: {e}")
            
            # 2단계: get_tools()로 도구 딕셔너리 접근
            if result is None:
                logger.info("방법 2: get_tools() 메서드로 도구 딕셔너리 접근 시도")
                try:
                    tools_dict = await self.mcp_server.get_tools()
                    if tool_name in tools_dict:
                        tool_func = tools_dict[tool_name]
                        logger.info(f"Tool 객체 타입: {type(tool_func)}")
                        logger.info(f"Tool 객체 속성: {[attr for attr in dir(tool_func) if not attr.startswith('_')]}")
                        
                        # FastMCP FunctionTool 특별 처리 - fn 속성에서 실제 함수 추출
                        if hasattr(tool_func, 'fn'):
                            try:
                                # FunctionTool의 fn 속성은 실제 async 함수
                                actual_func = tool_func.fn
                                logger.info(f"actual_func type: {type(actual_func)}")
                                logger.info(f"actual_func callable: {callable(actual_func)}")
                                logger.info(f"actual_func name: {getattr(actual_func, '__name__', 'No name')}")
                                logger.info(f"arguments: {arguments}")
                                
                                if callable(actual_func):
                                    result = await actual_func(**arguments)
                                    logger.info(f"get_tools()[].fn 방법 성공, result: {result}")
                                else:
                                    logger.warning("tool_func.fn이 callable하지 않음")
                            except Exception as e:
                                logger.error(f"get_tools()[].fn 방법 실패: {e}")
                                import traceback
                                logger.error(f"Full traceback: {traceback.format_exc()}")
                        
                        elif hasattr(tool_func, 'run') and callable(tool_func.run):
                            try:
                                tool_result = await tool_func.run(arguments)
                                # ToolResult 객체를 dict로 변환
                                if hasattr(tool_result, 'content'):
                                    result = {
                                        "success": True,
                                        "data": tool_result.content,
                                        "message": "도구 호출 완료"
                                    }
                                else:
                                    result = {
                                        "success": True,
                                        "data": str(tool_result),
                                        "message": "도구 호출 완료"
                                    }
                                logger.info("get_tools()[].run 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tools()[].run 방법 실패: {e}")
                        
                        elif hasattr(tool_func, 'handler') and callable(tool_func.handler):
                            try:
                                result = await tool_func.handler(**arguments)
                                logger.info("get_tools()[].handler 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tools()[].handler 방법 실패: {e}")
                        
                        elif hasattr(tool_func, 'function') and callable(tool_func.function):
                            try:
                                result = await tool_func.function(**arguments)
                                logger.info("get_tools()[].function 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tools()[].function 방법 실패: {e}")
                        
                        elif hasattr(tool_func, 'func') and callable(tool_func.func):
                            try:
                                result = await tool_func.func(**arguments)
                                logger.info("get_tools()[].func 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tools()[].func 방법 실패: {e}")
                        
                        elif hasattr(tool_func, '__call__'):
                            try:
                                result = await tool_func(**arguments)
                                logger.info("get_tools()[] 직접 호출 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tools()[] 직접 호출 방법 실패: {e}")
                except Exception as e:
                    logger.warning(f"get_tools() 방법 실패: {e}")
            
            # 3단계: get_tool 메서드 사용
            if result is None:
                logger.info("방법 3: get_tool 메서드 사용 시도")
                try:
                    tool = await self.mcp_server.get_tool(tool_name)
                    if tool:
                        logger.info(f"Get_tool 결과 타입: {type(tool)}")
                        logger.info(f"Get_tool 결과 속성: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
                        
                        # fn 속성에서 실제 함수 추출
                        if hasattr(tool, 'fn'):
                            try:
                                actual_func = tool.fn
                                if callable(actual_func):
                                    result = await actual_func(**arguments)
                                    logger.info("get_tool().fn 방법 성공")
                                else:
                                    logger.warning("get_tool().fn이 callable하지 않음")
                            except Exception as e:
                                logger.warning(f"get_tool().fn 방법 실패: {e}")
                        
                        # run 메서드 시도 (ToolResult 반환)
                        elif hasattr(tool, 'run') and callable(tool.run):
                            try:
                                tool_result = await tool.run(arguments)
                                # ToolResult 객체를 dict로 변환
                                if hasattr(tool_result, 'content'):
                                    result = {
                                        "success": True,
                                        "data": tool_result.content,
                                        "message": "도구 호출 완료"
                                    }
                                else:
                                    result = {
                                        "success": True,
                                        "data": str(tool_result),
                                        "message": "도구 호출 완료"
                                    }
                                logger.info("get_tool().run 방법 성공")
                            except Exception as e:
                                logger.warning(f"get_tool().run 방법 실패: {e}")
                        
                        # 다른 속성들 시도
                        elif result is None:
                            for attr_name in ['function', 'handler', 'callback']:
                                if hasattr(tool, attr_name):
                                    attr_func = getattr(tool, attr_name)
                                    if callable(attr_func):
                                        try:
                                            result = await attr_func(**arguments)
                                            logger.info(f"get_tool().{attr_name} 방법 성공")
                                            break
                                        except Exception as e:
                                            logger.warning(f"get_tool().{attr_name} 방법 실패: {e}")
                except Exception as e:
                    logger.warning(f"get_tool 방법 실패: {e}")
            
            # 4단계: 최후의 수단 - 직접 함수 매핑
            if result is None:
                logger.info("방법 4: 직접 함수 매핑 사용")
                function_map = await self._get_direct_function_map()
                if tool_name in function_map:
                    try:
                        func = function_map[tool_name]
                        # FunctionTool 객체인 경우 실제 함수 추출
                        if hasattr(func, 'fn') and callable(func.fn):
                            result = await func.fn(**arguments)
                        else:
                            result = await func(**arguments)
                        logger.info("직접 함수 매핑 방법 성공")
                    except Exception as e:
                        logger.warning(f"직접 함수 매핑 방법 실패: {e}")
            
            if result is None:
                raise Exception(f"모든 방법으로 도구 '{tool_name}' 호출 실패")
            
            logger.info(f"MCP 도구 '{tool_name}' 호출 완료, 결과: {result}")
            
            # 결과가 dict이고 success 키가 있는지 확인
            if isinstance(result, dict):
                return result
            else:
                # 결과가 예상 형식이 아닌 경우 래핑
                return {
                    "success": True,
                    "data": result,
                    "message": "도구 호출 완료"
                }
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"MCP 도구 '{tool_name}' 호출 실패: {e}")
            logger.error(f"상세 오류: {error_traceback}")
            return {
                "success": False,
                "error": str(e),
                "message": f"MCP 도구 '{tool_name}' 호출 중 오류가 발생했습니다",
                "traceback": error_traceback
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