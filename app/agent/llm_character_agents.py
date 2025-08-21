"""
LLM-Powered Character Agents - 투심이와 삼돌이
Google Gemini를 사용한 동적 응답 시스템
"""

import google.generativeai as genai
import os
from typing import Dict, Any, List
import json
import random
from loguru import logger

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class LLMInvestmentAgent:
    """투심이 - LLM 기반 투자가치 평가 에이전트"""
    
    def __init__(self):
        self.name = "투심이"
        self.personality = "투자 중심적, 현실적, 수익성 추구"
        self.model = genai.GenerativeModel('gemini-2.5-flash') if GEMINI_API_KEY else None
        
    def _get_character_prompt(self) -> str:
        """투심이의 캐릭터 프롬프트"""
        return """
당신은 '투심이'라는 부동산 투자 전문가 캐릭터입니다.

## 캐릭터 설정:
- 이름: 투심이 
- 성격: 투자 중심적, 현실적, 수익성을 최우선으로 생각
- 말투: 친근하지만 비즈니스 마인드가 강함, 가끔 삼돌이를 살짝 견제함
- 전문분야: 부동산 투자가치 평가 (가격, 면적, 층수, 교통, 미래가치)

## 응답 스타일:
- 투자 관점에서 냉정하게 분석
- 수익성과 시세를 중요하게 생각
- 삼돌이의 '삶의질' 중심 의견에 대해 "그것도 중요하지만 투자는..." 식으로 살짝 견제
- 구체적인 숫자와 근거를 제시하는 것을 좋아함
- 이모지 사용: 💰💸📈📊🏢

## 응답 형식:
반드시 JSON 형태로 응답하세요:
{
    "comment": "투심이의 주요 의견 (친근한 말투로)",
    "questions": ["사용자에게 할 질문 1", "사용자에게 할 질문 2"],
    "score": 점수 (1-100),
    "key_factors": ["중요 요소 1", "중요 요소 2", "중요 요소 3"]
}
"""

    async def analyze_property_llm(self, property_data: Dict[str, Any], user_message: str = "") -> Dict[str, Any]:
        """LLM을 사용한 부동산 투자가치 분석"""
        
        if not self.model:
            # Fallback to static response
            return self._fallback_response(property_data)
        
        try:
            prompt = f"""
{self._get_character_prompt()}

## 분석할 부동산 정보:
{json.dumps(property_data, ensure_ascii=False, indent=2)}

## 사용자 메시지:
{user_message if user_message else "부동산 투자 관점에서 분석해주세요"}

투심이의 캐릭터로 위 부동산을 투자 관점에서 분석하고, 위 JSON 형식으로 응답해주세요.
특히 가격 대비 수익성, 향후 가치 상승 가능성, 임대 수익 등을 고려해주세요.
"""
            
            response = self.model.generate_content(prompt)
            
            # JSON 응답 파싱 시도
            try:
                # 응답에서 JSON 부분 추출
                response_text = response.text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    # JSON 마커가 없으면 전체 텍스트에서 JSON 찾기
                    json_text = response_text.strip()
                
                result = json.loads(json_text)
                
                # 필수 필드 확인 및 보완
                if "comment" not in result:
                    result["comment"] = response_text
                if "questions" not in result:
                    result["questions"] = ["투자 예산은 어느 정도 생각하고 있어?", "언제쯤 매도할 계획이야?"]
                if "score" not in result:
                    result["score"] = random.randint(70, 95)
                if "key_factors" not in result:
                    result["key_factors"] = ["교통", "가격", "미래가치"]
                
                return {
                    "agent": self.name,
                    "total_score": result.get("score", 85),
                    "comment": result.get("comment", ""),
                    "questions": result.get("questions", []),
                    "key_factors": result.get("key_factors", [])
                }
                
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답 사용
                return {
                    "agent": self.name,
                    "total_score": random.randint(70, 95),
                    "comment": response.text,
                    "questions": ["투자 목적이 뭐야?", "예산은 어느 정도야?"],
                    "key_factors": ["교통", "가격", "미래가치"]
                }
                
        except Exception as e:
            logger.error(f"Gemini API error for 투심이: {e}")
            return self._fallback_response(property_data)
    
    def _fallback_response(self, property_data: Dict) -> Dict[str, Any]:
        """LLM 실패 시 fallback 응답"""
        comments = [
            "음... 투자 관점에서 보면 나쁘지 않은 것 같은데? 💰",
            "이 정도면 투자용으로 고려해볼 만하지 않을까? 📈",
            "가격 대비 수익성을 따져봐야겠어. 구체적인 정보가 더 필요해! 💸"
        ]
        
        return {
            "agent": self.name,
            "total_score": random.randint(70, 95),
            "comment": random.choice(comments),
            "questions": ["투자 목적이야, 거주 목적이야?", "예산은 어느 정도 생각하고 있어?"],
            "key_factors": ["교통", "가격", "미래가치"]
        }


class LLMLifeQualityAgent:
    """삼돌이 - LLM 기반 삶의질가치 평가 에이전트"""
    
    def __init__(self):
        self.name = "삼돌이"
        self.personality = "생활 중심적, 감성적, 편안함 추구"
        self.model = genai.GenerativeModel('gemini-2.5-flash') if GEMINI_API_KEY else None
    
    def _get_character_prompt(self) -> str:
        """삼돌이의 캐릭터 프롬프트"""
        return """
당신은 '삼돌이'라는 부동산 생활환경 전문가 캐릭터입니다.

## 캐릭터 설정:
- 이름: 삼돌이
- 성격: 생활 중심적, 감성적, 실제 거주자 입장에서 생각
- 말투: 따뜻하고 친근함, 투심이의 투자 중심 의견에 "돈도 중요하지만 살기 좋은 게..." 식으로 대응
- 전문분야: 삶의질가치 평가 (환경, 편의성, 안전, 교육, 문화)

## 응답 스타일:
- 실제 거주자 관점에서 따뜻하게 분석
- 생활 편의성과 환경을 중요하게 생각
- 투심이의 투자 중심 의견에 대해 "그것도 맞지만 실제로 살 때는..." 식으로 살짝 견제
- 감성적이고 구체적인 생활 상황을 언급
- 이모지 사용: 🌱🏡🌳☀️🚶‍♀️👨‍👩‍👧‍👦

## 응답 형식:
반드시 JSON 형태로 응답하세요:
{
    "comment": "삼돌이의 주요 의견 (따뜻한 말투로)",
    "questions": ["사용자에게 할 질문 1", "사용자에게 할 질문 2"],
    "score": 점수 (1-100),
    "key_factors": ["중요 요소 1", "중요 요소 2", "중요 요소 3"]
}
"""

    async def analyze_property_llm(self, property_data: Dict[str, Any], user_message: str = "") -> Dict[str, Any]:
        """LLM을 사용한 부동산 삶의질 분석"""
        
        if not self.model:
            return self._fallback_response(property_data)
        
        try:
            prompt = f"""
{self._get_character_prompt()}

## 분석할 부동산 정보:
{json.dumps(property_data, ensure_ascii=False, indent=2)}

## 사용자 메시지:
{user_message if user_message else "생활환경 관점에서 분석해주세요"}

삼돌이의 캐릭터로 위 부동산을 생활환경 관점에서 분석하고, 위 JSON 형식으로 응답해주세요.
특히 환경, 편의시설, 안전성, 교육환경, 문화시설 등 실제 거주 시의 편의성을 고려해주세요.
"""
            
            response = self.model.generate_content(prompt)
            
            try:
                response_text = response.text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text.strip()
                
                result = json.loads(json_text)
                
                if "comment" not in result:
                    result["comment"] = response_text
                if "questions" not in result:
                    result["questions"] = ["가족 구성은 어떻게 돼?", "주로 어떤 편의시설을 이용해?"]
                if "score" not in result:
                    result["score"] = random.randint(65, 85)
                if "key_factors" not in result:
                    result["key_factors"] = ["환경", "편의성", "안전"]
                
                return {
                    "agent": self.name,
                    "total_score": result.get("score", 75),
                    "comment": result.get("comment", ""),
                    "questions": result.get("questions", []),
                    "key_factors": result.get("key_factors", [])
                }
                
            except json.JSONDecodeError:
                return {
                    "agent": self.name,
                    "total_score": random.randint(65, 85),
                    "comment": response.text,
                    "questions": ["가족 구성은 어떻게 돼?", "출퇴근은 어디로 해야 해?"],
                    "key_factors": ["환경", "편의성", "안전"]
                }
                
        except Exception as e:
            logger.error(f"Gemini API error for 삼돌이: {e}")
            return self._fallback_response(property_data)
    
    def _fallback_response(self, property_data: Dict) -> Dict[str, Any]:
        """LLM 실패 시 fallback 응답"""
        comments = [
            "살기 좋은 환경이 제일 중요하지~ 🌱",
            "투심이 말도 맞지만, 실제로 생활할 때를 생각해봐야 해! 🏡",
            "편의시설이나 주변 환경이 어떤지 궁금하네~ 🌳"
        ]
        
        return {
            "agent": self.name,
            "total_score": random.randint(65, 85),
            "comment": random.choice(comments),
            "questions": ["가족 구성은 어떻게 돼?", "조용한 곳을 선호해?"],
            "key_factors": ["환경", "편의성", "안전"]
        }


class LLMCharacterAgentManager:
    """LLM 기반 캐릭터 에이전트 관리자"""
    
    def __init__(self):
        self.investment_agent = LLMInvestmentAgent()
        self.life_quality_agent = LLMLifeQualityAgent()
        self.conversation_history = []
    
    async def analyze_property_with_llm(self, property_data: Dict[str, Any], 
                                      user_message: str = "") -> Dict[str, Any]:
        """LLM 기반 캐릭터들이 함께 부동산을 분석"""
        
        # 투심이가 먼저 분석 (LLM)
        investment_analysis = await self.investment_agent.analyze_property_llm(property_data, user_message)
        
        # 삼돌이가 이어서 분석 (LLM, 투심이 의견 참고)
        enhanced_message = f"{user_message}\n\n투심이 의견: {investment_analysis.get('comment', '')}"
        life_quality_analysis = await self.life_quality_agent.analyze_property_llm(property_data, enhanced_message)
        
        # 대화 기록 저장
        self.conversation_history.append({
            "user_message": user_message,
            "investment_response": investment_analysis,
            "life_quality_response": life_quality_analysis
        })
        
        return {
            "투심이_분석": investment_analysis,
            "삼돌이_분석": life_quality_analysis,
            "종합_의견": self._generate_combined_opinion_llm(investment_analysis, life_quality_analysis),
            "추가_질문": investment_analysis.get("questions", []) + life_quality_analysis.get("questions", [])
        }
    
    def _generate_combined_opinion_llm(self, inv_analysis: Dict, life_analysis: Dict) -> str:
        """두 캐릭터의 종합 의견 (LLM 기반)"""
        
        inv_score = inv_analysis.get("total_score", 80)
        life_score = life_analysis.get("total_score", 75)
        avg_score = (inv_score + life_score) / 2
        
        if avg_score >= 85:
            return "투심이와 삼돌이 모두 이 매물을 추천하네요! 투자와 생활 두 마리 토끼를 다 잡을 수 있을 것 같아요. 🎯"
        elif avg_score >= 75:
            return "의견이 조금 엇갈리긴 하지만, 전반적으로 괜찮은 매물인 것 같아요. 각자의 우선순위에 따라 결정하시면 될 것 같네요! 😊"
        else:
            return "음... 두 친구 모두 좀 아쉬워하는 것 같네요. 다른 옵션도 알아보시거나, 더 구체적인 조건을 알려주시면 도움이 될 것 같아요! 🤔"

# 글로벌 LLM 캐릭터 에이전트 매니저
llm_character_manager = LLMCharacterAgentManager()