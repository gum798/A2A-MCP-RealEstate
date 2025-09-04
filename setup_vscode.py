#!/usr/bin/env python3
"""
VS Code 설정을 위한 스크립트
venv가 자동으로 활성화되도록 VS Code 설정을 생성합니다.
"""

import json
import os
from pathlib import Path

def create_vscode_settings():
    """VS Code 설정 파일 생성"""
    
    # 프로젝트 루트 경로
    project_root = Path(__file__).parent
    vscode_dir = project_root / ".vscode"
    settings_file = vscode_dir / "settings.json"
    
    # .vscode 디렉토리 생성
    vscode_dir.mkdir(exist_ok=True)
    
    # Python 인터프리터 경로
    venv_python = project_root / "venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ venv/bin/python을 찾을 수 없습니다.")
        print("먼저 가상환경을 생성하세요:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        return False
    
    # VS Code 설정
    settings = {
        "python.pythonPath": str(venv_python),
        "python.defaultInterpreterPath": str(venv_python),
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True,
        "terminal.integrated.env.osx": {
            "PYTHONPATH": str(project_root)
        },
        "terminal.integrated.env.linux": {
            "PYTHONPATH": str(project_root)
        },
        "files.associations": {
            "*.py": "python"
        },
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": True,
        "python.formatting.provider": "black",
        "editor.formatOnSave": True,
        "[python]": {
            "editor.tabSize": 4,
            "editor.insertSpaces": True,
            "editor.defaultFormatter": "ms-python.black-formatter"
        }
    }
    
    # 설정 파일 저장
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
    
    print(f"✅ VS Code 설정이 생성되었습니다: {settings_file}")
    return True

def create_launch_config():
    """디버그 설정 생성"""
    
    project_root = Path(__file__).parent
    vscode_dir = project_root / ".vscode"
    launch_file = vscode_dir / "launch.json"
    
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "A2A Agent Server",
                "type": "python",
                "request": "launch",
                "module": "uvicorn",
                "args": [
                    "app.main:app",
                    "--reload",
                    "--host", "0.0.0.0",
                    "--port", "28000"
                ],
                "console": "integratedTerminal",
                "justMyCode": True,
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            },
            {
                "name": "CLI Chat",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/cli_chat.py",
                "console": "integratedTerminal",
                "justMyCode": True,
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            },
            {
                "name": "Multi-Agent Demo",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/examples/multi_agent_chat_demo.py",
                "console": "integratedTerminal",
                "justMyCode": True,
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            }
        ]
    }
    
    with open(launch_file, 'w', encoding='utf-8') as f:
        json.dump(launch_config, f, indent=4, ensure_ascii=False)
    
    print(f"✅ VS Code 디버그 설정이 생성되었습니다: {launch_file}")

def create_tasks_config():
    """작업 설정 생성"""
    
    project_root = Path(__file__).parent
    vscode_dir = project_root / ".vscode"
    tasks_file = vscode_dir / "tasks.json"
    
    tasks_config = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Start A2A Server",
                "type": "shell",
                "command": "uvicorn",
                "args": [
                    "app.main:app",
                    "--reload",
                    "--host", "0.0.0.0",
                    "--port", "28000"
                ],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "new"
                },
                "problemMatcher": []
            },
            {
                "label": "Run CLI Chat",
                "type": "shell",
                "command": "python",
                "args": ["cli_chat.py"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": True,
                    "panel": "new"
                },
                "problemMatcher": []
            },
            {
                "label": "Install Dependencies",
                "type": "shell",
                "command": "pip",
                "args": ["install", "-r", "requirements.txt"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared"
                },
                "problemMatcher": []
            }
        ]
    }
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_config, f, indent=4, ensure_ascii=False)
    
    print(f"✅ VS Code 작업 설정이 생성되었습니다: {tasks_file}")

def main():
    """메인 함수"""
    print("🔧 VS Code 개발환경 설정을 시작합니다...")
    
    if create_vscode_settings():
        create_launch_config()
        create_tasks_config()
        
        print("\n✅ VS Code 설정이 완료되었습니다!")
        print("\n📝 사용법:")
        print("1. VS Code에서 이 프로젝트 폴더를 다시 열어주세요")
        print("2. 터미널이 자동으로 venv를 활성화합니다")
        print("3. F5로 디버깅 시작 또는 Ctrl+Shift+P -> 'Tasks: Run Task'")
        print("\n🚀 서버 시작:")
        print("  • Ctrl+Shift+P -> 'Tasks: Run Task' -> 'Start A2A Server'")
        print("  • 또는 F5로 디버깅 모드 시작")
        print("\n💬 CLI 채팅:")
        print("  • python cli_chat.py")
        print("  • 또는 Ctrl+Shift+P -> 'Tasks: Run Task' -> 'Run CLI Chat'")
        print("\n🌐 웹 채팅:")
        print("  • 서버 시작 후 http://localhost:28000/web/agent-chat 접속")
        
    else:
        print("\n❌ 설정 실패. venv를 먼저 생성해주세요.")

if __name__ == "__main__":
    main()