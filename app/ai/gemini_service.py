"""
Gemini CLI 래퍼 서비스
"""
import asyncio
import subprocess
import json
import tempfile
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.utils.logger import logger


class GeminiService:
    """Gemini CLI를 Python에서 사용하기 위한 래퍼 클래스"""
    
    def __init__(self):
        self.gemini_available = self._check_gemini_cli()
        
    def _check_gemini_cli(self) -> bool:
        """Gemini CLI가 설치되어 있는지 확인"""
        try:
            result = subprocess.run(
                ["gemini", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info("Gemini CLI detected and available")
                return True
            else:
                logger.debug("Gemini CLI not available or not authenticated")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Gemini CLI not found: {e}")
            return False
    
    async def chat(self, prompt: str, context: Optional[str] = None) -> str:
        """Gemini와 채팅"""
        if not self.gemini_available:
            return "❌ Gemini CLI가 설치되지 않았거나 인증되지 않았습니다."
        
        try:
            # 컨텍스트가 있으면 프롬프트에 추가
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            # Gemini CLI 실행
            process = await asyncio.create_subprocess_exec(
                "gemini", full_prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                logger.info(f"Gemini response received (length: {len(response)})")
                return response
            else:
                error_msg = stderr.decode('utf-8').strip()
                logger.error(f"Gemini CLI error: {error_msg}")
                return f"❌ Gemini 오류: {error_msg}"
                
        except asyncio.TimeoutError:
            logger.error("Gemini CLI timeout")
            return "❌ Gemini 응답 시간 초과"
        except Exception as e:
            logger.error(f"Gemini service error: {e}")
            return f"❌ Gemini 서비스 오류: {str(e)}"
    
    async def analyze_code(self, code: str, language: str = "python") -> str:
        """코드 분석"""
        prompt = f"""
다음 {language} 코드를 분석해주세요:

```{language}
{code}
```

분석 내용:
1. 코드의 주요 기능
2. 잠재적 개선점
3. 보안 이슈 (있다면)
4. 성능 최적화 제안

한국어로 답변해주세요.
"""
        return await self.chat(prompt)
    
    async def analyze_data(self, data: Dict[str, Any], analysis_type: str = "general") -> str:
        """데이터 분석"""
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        prompt = f"""
다음 데이터를 {analysis_type} 관점에서 분석해주세요:

```json
{data_str}
```

분석 요청:
1. 데이터 패턴과 트렌드
2. 주요 인사이트
3. 이상치나 특이점 (있다면)
4. 비즈니스 관점에서의 제안

한국어로 답변해주세요.
"""
        return await self.chat(prompt)
    
    async def generate_documentation(self, code: str, doc_type: str = "api") -> str:
        """문서 생성"""
        prompt = f"""
다음 코드에 대한 {doc_type} 문서를 생성해주세요:

```python
{code}
```

문서 요구사항:
1. 명확한 설명
2. 매개변수 및 반환값 설명
3. 사용 예시
4. 마크다운 형식으로 작성

한국어로 작성해주세요.
"""
        return await self.chat(prompt)
    
    async def suggest_improvements(self, description: str, current_data: Optional[str] = None) -> str:
        """개선사항 제안"""
        prompt = f"""
상황: {description}

{f'현재 데이터: {current_data}' if current_data else ''}

다음에 대한 개선사항을 제안해주세요:
1. 구체적인 개선 방안
2. 우선순위
3. 구현 난이도
4. 예상 효과

한국어로 답변해주세요.
"""
        return await self.chat(prompt)
    
    async def translate_message(self, message: str, target_lang: str = "ko") -> str:
        """메시지 번역"""
        prompt = f"다음 텍스트를 {target_lang}로 번역해주세요:\n\n{message}"
        return await self.chat(prompt)
    
    async def analyze_with_file(self, file_path: str, question: str) -> str:
        """파일과 함께 분석 (Gemini CLI는 현재 작업 디렉토리의 파일 접근 가능)"""
        if not os.path.exists(file_path):
            return "❌ 파일을 찾을 수 없습니다."
        
        # 파일 내용을 읽어서 컨텍스트로 제공
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            prompt = f"""
파일: {file_path}
내용:
```
{file_content[:2000]}{'...' if len(file_content) > 2000 else ''}
```

질문: {question}

파일 내용을 바탕으로 답변해주세요. 한국어로 답변해주세요.
"""
            return await self.chat(prompt)
        except Exception as e:
            return f"❌ 파일 읽기 오류: {str(e)}"


# 전역 Gemini 서비스 인스턴스
gemini_service = GeminiService()