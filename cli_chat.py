#!/usr/bin/env python3
"""
A2A Agent CLI Chat Interface
자연어로 등록된 에이전트들과 대화할 수 있는 CLI 인터페이스
"""

import asyncio
import httpx
import json
import sys
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

console = Console()

class A2AChatCLI:
    def __init__(self, base_url: str = "http://localhost:28000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.current_agent: Optional[str] = None
        self.conversation_history = []
        
    async def start_chat(self):
        """채팅 세션 시작"""
        console.clear()
        
        # 환영 메시지
        welcome_panel = Panel(
            Text("🤖 A2A Agent CLI Chat\n자연어로 다양한 전문 에이전트와 대화해보세요!", 
                 style="bold blue"),
            title="Welcome", 
            border_style="blue"
        )
        console.print(welcome_panel)
        
        # 등록된 에이전트 목록 표시
        await self.show_available_agents()
        
        console.print("\n💡 사용법:")
        console.print("  • '소크라테스와 이야기하고 싶어' - 특정 에이전트와 대화")
        console.print("  • '부동산 투자 도움' - 주제별 에이전트 추천")
        console.print("  • '/agents' - 에이전트 목록 보기")
        console.print("  • '/help' - 도움말")
        console.print("  • '/exit' - 종료")
        console.print()
        
        # 메인 채팅 루프
        await self.chat_loop()
    
    async def show_available_agents(self):
        """등록된 에이전트 목록 표시"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/registry/agents")
                
                if response.status_code == 200:
                    agents_data = response.json()
                    
                    table = Table(title="등록된 에이전트 목록", show_header=True)
                    table.add_column("이름", style="cyan")
                    table.add_column("전문분야", style="green")
                    table.add_column("별명", style="yellow")
                    table.add_column("상태", justify="center")
                    
                    for agent in agents_data['agents']:
                        status = "🟢 활성" if agent['status'] == 'active' else "🔴 비활성"
                        aliases = ", ".join(agent['aliases'][:3])
                        if len(agent['aliases']) > 3:
                            aliases += "..."
                        
                        table.add_row(
                            agent['name'],
                            agent['specialty'],
                            aliases,
                            status
                        )
                    
                    console.print(table)
                else:
                    console.print("❌ 에이전트 목록을 가져올 수 없습니다.", style="red")
                    
        except Exception as e:
            console.print(f"❌ 에이전트 목록 조회 오류: {e}", style="red")
    
    async def chat_loop(self):
        """메인 채팅 루프"""
        while True:
            try:
                # 사용자 입력
                if self.current_agent:
                    prompt_text = f"[{self.current_agent}] 💬 "
                else:
                    prompt_text = "💬 "
                
                user_input = Prompt.ask(prompt_text).strip()
                
                if not user_input:
                    continue
                
                # 명령어 처리
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue
                
                # 메시지 처리
                await self.process_message(user_input)
                
            except KeyboardInterrupt:
                console.print("\n👋 채팅을 종료합니다.", style="yellow")
                break
            except Exception as e:
                console.print(f"❌ 오류 발생: {e}", style="red")
    
    async def handle_command(self, command: str):
        """명령어 처리"""
        cmd = command.lower().strip()
        
        if cmd in ['/exit', '/quit']:
            console.print("👋 채팅을 종료합니다.", style="yellow")
            sys.exit(0)
            
        elif cmd == '/agents':
            await self.show_available_agents()
            
        elif cmd == '/help':
            help_text = """
🤖 A2A Agent CLI Chat 도움말

명령어:
  /agents  - 등록된 에이전트 목록 보기
  /help    - 이 도움말 표시
  /clear   - 화면 정리
  /reset   - 대화 세션 초기화
  /exit    - 프로그램 종료

자연어 대화:
  '소크라테스와 이야기하고 싶어' - 특정 에이전트 선택
  '부동산 투자 도움이 필요해'   - 주제별 에이전트 추천
  '취업 준비를 도와줘'         - 업무별 에이전트 자동 연결
"""
            console.print(Panel(help_text, title="도움말", border_style="green"))
            
        elif cmd == '/clear':
            console.clear()
            
        elif cmd == '/reset':
            self.session_id = None
            self.current_agent = None
            self.conversation_history.clear()
            console.print("✅ 대화 세션이 초기화되었습니다.", style="green")
            
        else:
            console.print(f"❌ 알 수 없는 명령어: {command}", style="red")
    
    async def process_message(self, message: str):
        """메시지 처리 및 에이전트와 대화"""
        # 로딩 스피너 표시
        with console.status("[bold green]에이전트와 연결 중...") as status:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # 스마트 채팅 API 호출
                    response = await client.post(
                        f"{self.base_url}/api/smart-chat/chat",
                        json={
                            "message": message,
                            "auto_switch": True,
                            "session_id": self.session_id
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        await self.display_chat_result(message, result)
                        
                        # 세션 ID 저장
                        if 'session_id' in result:
                            self.session_id = result['session_id']
                        
                        # 현재 에이전트 업데이트
                        if result['action'] == 'agent_switched':
                            self.current_agent = result.get('switched_to', 'Unknown')
                            
                    else:
                        console.print(f"❌ 서버 오류: {response.status_code}", style="red")
                        
            except httpx.TimeoutException:
                console.print("⏰ 응답 시간 초과. 다시 시도해주세요.", style="yellow")
            except Exception as e:
                console.print(f"❌ 통신 오류: {e}", style="red")
    
    async def display_chat_result(self, user_message: str, result: dict):
        """채팅 결과 표시"""
        # 사용자 메시지
        console.print(Panel(
            user_message,
            title="You",
            title_align="left",
            border_style="blue",
            padding=(0, 1)
        ))
        
        # 액션에 따른 시스템 메시지
        if result['action'] == 'agent_switched':
            switch_msg = f"🔄 {result.get('switch_message', '에이전트가 전환되었습니다.')}"
            console.print(f"[bold green]{switch_msg}[/bold green]")
            
        elif result['action'] == 'agent_recommended':
            rec_msg = f"💡 {result.get('recommendation_message', '에이전트를 추천합니다.')}"
            console.print(f"[bold yellow]{rec_msg}[/bold yellow]")
        
        # 에이전트 응답
        if 'agent_response' in result:
            agent_resp = result['agent_response']
            sender_name = agent_resp.get('sender', 'Assistant')
            content = agent_resp.get('content', '')
            
            # 에이전트 응답을 패널로 표시
            agent_panel = Panel(
                content,
                title=f"🤖 {sender_name}",
                title_align="left",
                border_style="green",
                padding=(0, 1)
            )
            console.print(agent_panel)
            
            # 대화 히스토리에 추가
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user': user_message,
                'agent': sender_name,
                'response': content
            })
        
        console.print()  # 줄바꿈

async def main():
    """메인 함수"""
    # 서버 연결 확인
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:28000/health")
            if response.status_code != 200:
                console.print("❌ A2A Agent 서버에 연결할 수 없습니다.", style="red")
                console.print("서버를 먼저 시작해주세요:", style="yellow")
                console.print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 28000")
                return
    except Exception:
        console.print("❌ A2A Agent 서버에 연결할 수 없습니다.", style="red")
        console.print("서버를 먼저 시작해주세요:", style="yellow")
        console.print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 28000")
        return
    
    # CLI 채팅 시작
    cli = A2AChatCLI()
    await cli.start_chat()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 프로그램을 종료합니다.", style="yellow")