"""
JSON-RPC Communication Protocol
에이전트 간 JSON-RPC 통신 프로토콜 구현
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import asyncio
from loguru import logger
from pydantic import BaseModel, Field

class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 요청 모델"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name to call")
    params: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="Method parameters")
    id: Optional[Union[str, int]] = Field(default_factory=lambda: str(uuid.uuid4()), description="Request ID")

class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 응답 모델"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Optional[Any] = Field(default=None, description="Method result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error object")
    id: Optional[Union[str, int]] = Field(..., description="Request ID")

class JsonRpcError(BaseModel):
    """JSON-RPC 에러 모델"""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message") 
    data: Optional[Any] = Field(default=None, description="Additional error data")

class JsonRpcProcessor:
    """JSON-RPC 요청 처리기"""
    
    def __init__(self):
        self.methods: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        
        # 기본 메소드 등록
        self.register_method("ping", self._ping)
        self.register_method("get_capabilities", self._get_capabilities)
        self.register_method("get_status", self._get_status)
        
    def register_method(self, name: str, func: Callable):
        """RPC 메소드 등록"""
        self.methods[name] = func
        logger.debug(f"Registered RPC method: {name}")
        
    def add_middleware(self, middleware: Callable):
        """미들웨어 추가"""
        self.middleware.append(middleware)
        
    async def process_request(self, request_data: Union[str, Dict]) -> Dict:
        """JSON-RPC 요청 처리"""
        try:
            # 요청 데이터 파싱
            if isinstance(request_data, str):
                request_data = json.loads(request_data)
                
            # 배치 요청 처리
            if isinstance(request_data, list):
                return await self._process_batch(request_data)
                
            # 단일 요청 처리
            return await self._process_single_request(request_data)
            
        except json.JSONDecodeError as e:
            return self._create_error_response(
                None, -32700, "Parse error", str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in process_request: {e}")
            return self._create_error_response(
                None, -32603, "Internal error", str(e)
            )
    
    async def _process_batch(self, requests: List[Dict]) -> List[Dict]:
        """배치 요청 처리"""
        if not requests:
            return self._create_error_response(
                None, -32600, "Invalid Request", "Empty batch"
            )
            
        tasks = [self._process_single_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                valid_responses.append(
                    self._create_error_response(
                        requests[i].get('id'), -32603, "Internal error", str(response)
                    )
                )
            else:
                valid_responses.append(response)
                
        return valid_responses
    
    async def _process_single_request(self, request_data: Dict) -> Dict:
        """단일 요청 처리"""
        try:
            # 요청 검증
            request = JsonRpcRequest(**request_data)
            
            # 미들웨어 실행
            for middleware in self.middleware:
                result = await middleware(request)
                if result is not None:
                    return result
            
            # 메소드 존재 확인
            if request.method not in self.methods:
                return self._create_error_response(
                    request.id, -32601, "Method not found", request.method
                )
            
            # 메소드 실행
            method = self.methods[request.method]
            
            if request.params is None:
                result = await self._call_method(method)
            elif isinstance(request.params, list):
                result = await self._call_method(method, *request.params)
            elif isinstance(request.params, dict):
                result = await self._call_method(method, **request.params)
            else:
                return self._create_error_response(
                    request.id, -32602, "Invalid params", "Params must be array or object"
                )
            
            # 알림 요청인 경우 응답 없음
            if request.id is None:
                return None
                
            # 성공 응답
            return JsonRpcResponse(result=result, id=request.id).dict()
            
        except ValueError as e:
            # Pydantic 검증 에러
            return self._create_error_response(
                request_data.get('id'), -32600, "Invalid Request", str(e)
            )
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return self._create_error_response(
                request_data.get('id'), -32603, "Internal error", str(e)
            )
    
    async def _call_method(self, method: Callable, *args, **kwargs) -> Any:
        """메소드 호출"""
        try:
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Method execution error: {e}")
            raise
    
    def _create_error_response(self, request_id: Optional[Union[str, int]], 
                             code: int, message: str, data: Any = None) -> Dict:
        """에러 응답 생성"""
        error = JsonRpcError(code=code, message=message, data=data)
        return JsonRpcResponse(error=error.dict(), id=request_id).dict()
    
    # 기본 RPC 메소드들
    async def _ping(self) -> Dict[str, Any]:
        """핑 메소드"""
        return {
            "pong": True,
            "timestamp": datetime.now().isoformat(),
            "agent_id": "agent-py-001"
        }
    
    async def _get_capabilities(self) -> Dict[str, Any]:
        """기능 목록 조회"""
        from .agent_discovery import agent_discovery
        agent_card = await agent_discovery.load_agent_card()
        return agent_card.get('capabilities', {})
    
    async def _get_status(self) -> Dict[str, Any]:
        """상태 조회"""
        return {
            "status": "active",
            "uptime": 0,  # 실제 구현 시 계산
            "registered_methods": list(self.methods.keys()),
            "timestamp": datetime.now().isoformat()
        }

# 글로벌 RPC 프로세서
rpc_processor = JsonRpcProcessor()

# 부동산 관련 RPC 메소드 등록
async def analyze_investment_value(property_data: Dict) -> Dict[str, Any]:
    """투자가치 분석 RPC 메소드"""
    # 실제 분석 로직은 기존 코드 활용
    return {
        "investment_score": 85.0,
        "grade": "A",
        "factors": {
            "price": 80,
            "area": 90,
            "floor": 85,
            "transport": 90,
            "future_value": 85
        }
    }

async def analyze_quality_of_life(property_data: Dict) -> Dict[str, Any]:
    """삶의질 분석 RPC 메소드"""
    return {
        "life_quality_score": 72.0,
        "grade": "B+",
        "factors": {
            "environment": 70,
            "convenience": 75,
            "safety": 70,
            "education": 75,
            "culture": 70
        }
    }

async def search_real_estate(location: str, property_type: str = "아파트") -> Dict[str, Any]:
    """부동산 검색 RPC 메소드"""
    return {
        "results": [
            {
                "address": location,
                "property_type": property_type,
                "price": 50000,
                "area": 84.5,
                "floor": 15
            }
        ],
        "total_count": 1
    }

# 부동산 관련 메소드 등록
rpc_processor.register_method("analyze_investment_value", analyze_investment_value)
rpc_processor.register_method("analyze_quality_of_life", analyze_quality_of_life)
rpc_processor.register_method("search_real_estate", search_real_estate)