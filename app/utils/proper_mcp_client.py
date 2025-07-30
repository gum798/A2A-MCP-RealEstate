"""
FastMCP 서버와 표준 MCP 프로토콜로 통신하는 클라이언트
subprocess를 통해 별도 프로세스의 MCP 서버와 JSON-RPC 통신
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from ..utils.logger import logger

class ProperMCPClient:
    """FastMCP 서버와 표준 MCP 프로토콜로 통신하는 클라이언트"""
    
    def __init__(self, server_script_path: str):
        """
        Args:
            server_script_path: MCP 서버 실행 스크립트 경로
        """
        self.server_script_path = server_script_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        
    async def start_server(self):
        """MCP 서버 프로세스 시작"""
        try:
            # 프로젝트 루트 경로 계산
            project_root = Path(__file__).parent.parent.parent
            
            # MCP 서버 실행 명령어
            cmd = ["python", "-m", self.server_script_path]
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root,
                env={**os.environ, "PYTHONPATH": str(project_root)}
            )
            
            # 서버가 시작될 때까지 잠시 대기
            await asyncio.sleep(2)
            
            # 서버 상태 확인
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                raise RuntimeError(f"MCP 서버 시작 실패: {stderr_output}")
            
            logger.info("FastMCP 서버가 성공적으로 시작되었습니다")
            return True
            
        except Exception as e:
            logger.error(f"MCP 서버 시작 실패: {e}")
            if self.process:
                self.process.terminate()
                self.process = None
            return False
    
    def _next_id(self) -> int:
        """다음 요청 ID 생성"""
        self.request_id += 1
        return self.request_id
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        if not self.process:
            if not await self.start_server():
                return {
                    "success": False,
                    "error": "MCP 서버를 시작할 수 없습니다",
                    "message": "서버 프로세스 시작 실패"
                }
        
        try:
            # MCP 도구 호출을 위한 임시 스크립트 생성
            script_content = f'''
import asyncio
import sys
import os
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def main():
    try:
        # MCP 서버 모듈 임포트  
        import importlib
        module = importlib.import_module("{self.server_script_path}")
        mcp = module.mcp
        
        # 도구 실행
        tool = mcp.get_tool("{tool_name}")
        if tool is None:
            print(json.dumps({{"success": False, "error": "도구를 찾을 수 없습니다"}}))
            return
            
        # 도구 실행
        result = await tool(**{arguments})
        print(json.dumps({{"success": True, "data": result}}, ensure_ascii=False, default=str))
        
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e), "message": "MCP 도구 실행 중 오류"}}, ensure_ascii=False))

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
                        response_data = json.loads(result.stdout)
                        return response_data
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "error": "JSON 파싱 오류",
                            "raw_output": result.stdout,
                            "stderr": result.stderr
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
            logger.error(f"MCP 도구 '{tool_name}' 호출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"MCP 도구 '{tool_name}' 호출 중 오류가 발생했습니다"
            }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """MCP 리소스 목록 조회"""
        try:
            # 리소스 목록 조회를 위한 임시 스크립트
            script_content = f'''
import asyncio
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def main():
    try:
        import importlib
        module = importlib.import_module("{self.server_script_path}")
        mcp = module.mcp
        
        # 리소스 목록 조회
        resources = []
        for resource_uri, resource_func in mcp._resources.items():
            resources.append({{
                "uri": resource_uri,
                "name": resource_func.__name__,
                "description": resource_func.__doc__ or ""
            }})
        
        print(json.dumps(resources, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps([], ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            try:
                result = subprocess.run(
                    ['python', temp_script],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    return []
                    
            finally:
                try:
                    os.unlink(temp_script)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"MCP 리소스 목록 조회 실패: {e}")
            return []
    
    async def read_resource(self, uri: str) -> str:
        """MCP 리소스 읽기"""
        try:
            script_content = f'''
import asyncio
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def main():
    try:
        import importlib
        module = importlib.import_module("{self.server_script_path}")
        mcp = module.mcp
        
        # 리소스 읽기
        if "{uri}" in mcp._resources:
            resource_func = mcp._resources["{uri}"]
            content = await resource_func()
            print(content)
        else:
            print("리소스를 찾을 수 없습니다.")
        
    except Exception as e:
        print(f"리소스 읽기 오류: {{e}}")

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            try:
                result = subprocess.run(
                    ['python', temp_script],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=Path(__file__).parent.parent.parent
                )
                
                return result.stdout if result.returncode == 0 else "리소스 읽기 실패"
                    
            finally:
                try:
                    os.unlink(temp_script)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"MCP 리소스 '{uri}' 읽기 실패: {e}")
            return f"리소스 읽기 오류: {e}"
    
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

# 전역 클라이언트 인스턴스들
_real_estate_mcp_client: Optional[ProperMCPClient] = None

async def get_real_estate_mcp_client() -> ProperMCPClient:
    """부동산 MCP 클라이언트 인스턴스 반환"""
    global _real_estate_mcp_client
    
    if _real_estate_mcp_client is None:
        _real_estate_mcp_client = ProperMCPClient("app.mcp.real_estate_recommendation_mcp")
    
    return _real_estate_mcp_client

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

async def cleanup_mcp_clients():
    """MCP 클라이언트들 정리"""
    global _real_estate_mcp_client
    
    if _real_estate_mcp_client:
        await _real_estate_mcp_client.stop_server()
        _real_estate_mcp_client = None