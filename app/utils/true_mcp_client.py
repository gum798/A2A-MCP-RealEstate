"""
진정한 MCP 클라이언트 구현
표준 MCP 프로토콜을 사용하여 별도 프로세스의 MCP 서버와 통신
"""

import asyncio
import json
import subprocess
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from ..utils.logger import logger

class TrueMCPClient:
    """표준 MCP 프로토콜을 사용하는 클라이언트"""
    
    def __init__(self, server_command: List[str]):
        """
        Args:
            server_command: MCP 서버 실행 명령어 리스트
        """
        self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        
    async def start_server(self):
        """MCP 서버 프로세스 시작"""
        try:
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # 서버가 시작될 때까지 잠시 대기
            await asyncio.sleep(1)
            
            # 초기화 요청 보내기
            await self._send_initialize()
            
            logger.info("MCP 서버가 성공적으로 시작되었습니다")
            return True
            
        except Exception as e:
            logger.error(f"MCP 서버 시작 실패: {e}")
            return False
    
    async def _send_initialize(self):
        """MCP 서버 초기화"""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "A2A-Real-Estate-Client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_request)
        
        # initialized 알림 보내기
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        await self._send_notification(initialized_notification)
        
        return response
    
    def _next_id(self) -> int:
        """다음 요청 ID 생성"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 요청 보내기"""
        if not self.process:
            raise RuntimeError("MCP 서버가 시작되지 않았습니다")
        
        try:
            # 요청 전송
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # 응답 받기
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("MCP 서버로부터 응답을 받지 못했습니다")
                
            response = json.loads(response_line.strip())
            
            if "error" in response:
                raise RuntimeError(f"MCP 서버 오류: {response['error']}")
                
            return response
            
        except Exception as e:
            logger.error(f"MCP 요청 전송 실패: {e}")
            raise
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """JSON-RPC 알림 보내기"""
        if not self.process:
            raise RuntimeError("MCP 서버가 시작되지 않았습니다")
        
        try:
            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()
            
        except Exception as e:
            logger.error(f"MCP 알림 전송 실패: {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await self._send_request(request)
            
            # MCP 응답 구조에서 실제 데이터 추출
            result = response.get("result", {})
            
            # content가 리스트인 경우 첫 번째 항목의 text 추출
            if "content" in result and isinstance(result["content"], list):
                if result["content"] and "text" in result["content"][0]:
                    try:
                        # JSON 문자열을 파싱
                        content_data = json.loads(result["content"][0]["text"])
                        return {"success": True, "data": content_data}
                    except json.JSONDecodeError:
                        return {"success": True, "data": result["content"][0]["text"]}
            
            return {"success": True, "data": result}
            
        except Exception as e:
            logger.error(f"MCP 도구 '{tool_name}' 호출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"MCP 도구 '{tool_name}' 호출 중 오류가 발생했습니다"
            }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """사용 가능한 리소스 목록 조회"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/list"
        }
        
        response = await self._send_request(request)
        return response.get("result", {}).get("resources", [])
    
    async def read_resource(self, uri: str) -> str:
        """리소스 읽기"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        response = await self._send_request(request)
        result = response.get("result", {})
        
        if "contents" in result and result["contents"]:
            return result["contents"][0].get("text", "")
        
        return ""
    
    async def stop_server(self):
        """MCP 서버 프로세스 종료"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None
                
            logger.info("MCP 서버가 종료되었습니다")

# 전역 클라이언트 인스턴스
_real_estate_mcp_client: Optional[TrueMCPClient] = None

async def get_real_estate_mcp_client() -> TrueMCPClient:
    """부동산 MCP 클라이언트 인스턴스 반환"""
    global _real_estate_mcp_client
    
    if _real_estate_mcp_client is None:
        # MCP 서버 명령어 구성
        project_root = Path(__file__).parent.parent.parent
        server_script = project_root / "scripts" / "start_mcp_server.py"
        
        server_command = ["python", str(server_script)]
        
        _real_estate_mcp_client = TrueMCPClient(server_command)
        
        # 서버 시작
        success = await _real_estate_mcp_client.start_server()
        if not success:
            raise RuntimeError("MCP 서버 시작에 실패했습니다")
    
    return _real_estate_mcp_client

async def call_real_estate_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """부동산 MCP 도구 호출 (진정한 MCP 프로토콜 사용)"""
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

async def cleanup_mcp_clients():
    """MCP 클라이언트들 정리"""
    global _real_estate_mcp_client
    
    if _real_estate_mcp_client:
        await _real_estate_mcp_client.stop_server()
        _real_estate_mcp_client = None