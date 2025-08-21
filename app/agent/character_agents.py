"""
Character Agents - 투심이와 삼돌이
부동산 분석을 위한 캐릭터형 에이전트 구현
"""

from typing import Dict, Any, List
import random
from loguru import logger

class InvestmentAgent:
    """투심이 - 투자가치 평가 에이전트"""
    
    def __init__(self):
        self.name = "투심이"
        self.personality = "투자 중심적, 현실적, 수익성 추구"
        self.weights = {
            "가격": 0.25,
            "면적": 0.20,
            "층수": 0.15,
            "교통": 0.25,
            "미래가치": 0.15
        }
        
    def analyze_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """부동산 투자가치 분석"""
        
        # 기본 점수 계산 (실제 구현 시 더 정교한 로직 필요)
        scores = {
            "가격": self._analyze_price(property_data),
            "면적": self._analyze_area(property_data),
            "층수": self._analyze_floor(property_data),
            "교통": self._analyze_transport(property_data),
            "미래가치": self._analyze_future_value(property_data)
        }
        
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        return {
            "agent": self.name,
            "total_score": round(total_score, 1),
            "detailed_scores": scores,
            "comment": self._generate_comment(total_score, scores),
            "questions": self._generate_questions(property_data)
        }
    
    def _analyze_price(self, data: Dict) -> float:
        # 가격 분석 로직 (예시)
        return random.uniform(70, 95)
    
    def _analyze_area(self, data: Dict) -> float:
        # 면적 분석 로직 (예시)
        return random.uniform(75, 90)
    
    def _analyze_floor(self, data: Dict) -> float:
        # 층수 분석 로직 (예시)
        return random.uniform(80, 95)
    
    def _analyze_transport(self, data: Dict) -> float:
        # 교통 분석 로직 (예시)
        return random.uniform(85, 100)
    
    def _analyze_future_value(self, data: Dict) -> float:
        # 미래가치 분석 로직 (예시)
        return random.uniform(70, 85)
    
    def _generate_comment(self, total_score: float, scores: Dict) -> str:
        """투심이의 개성있는 코멘트 생성"""
        
        comments = []
        
        if total_score >= 90:
            comments.append("와 이거 진짜 괜찮은데? 투자 관점에서 보면 거의 완벽하지 않아?")
        elif total_score >= 80:
            comments.append("음... 나쁘지 않네. 투자용으로는 충분히 고려해볼 만해.")
        elif total_score >= 70:
            comments.append("흠.. 투자로는 좀 애매한 것 같은데? 가격이 더 떨어지면 모르겠지만...")
        else:
            comments.append("이건 좀... 투자 관점에서는 별로인 것 같아. 다른 곳 알아보는 게 어때?")
        
        # 세부 항목별 코멘트 추가
        if scores["교통"] >= 90:
            comments.append("특히 교통은 정말 좋네! 지하철역 가깝다는 건 투자에서 엄청 중요해.")
        
        if scores["미래가치"] >= 85:
            comments.append("미래 발전 가능성도 높아 보이고... 몇 년 후 가격 상승 기대해볼 만하지 않을까?")
        
        return " ".join(comments)
    
    def _generate_questions(self, data: Dict) -> List[str]:
        """사용자에게 물어볼 질문들"""
        questions = [
            "혹시 투자 목적이야, 거주 목적이야?",
            "예산은 어느 정도 생각하고 있어?",
            "언제쯤 매도할 계획이야?",
            "주변에 개발 계획이나 재건축 얘기 들어본 적 있어?"
        ]
        return random.sample(questions, 2)


class LifeQualityAgent:
    """삼돌이 - 삶의질가치 평가 에이전트"""
    
    def __init__(self):
        self.name = "삼돌이"
        self.personality = "생활 중심적, 감성적, 편안함 추구"
        self.weights = {
            "환경": 0.25,
            "편의성": 0.25,
            "안전": 0.20,
            "교육": 0.15,
            "문화": 0.15
        }
    
    def analyze_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """부동산 삶의질 분석"""
        
        scores = {
            "환경": self._analyze_environment(property_data),
            "편의성": self._analyze_convenience(property_data),
            "안전": self._analyze_safety(property_data),
            "교육": self._analyze_education(property_data),
            "문화": self._analyze_culture(property_data)
        }
        
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        return {
            "agent": self.name,
            "total_score": round(total_score, 1),
            "detailed_scores": scores,
            "comment": self._generate_comment(total_score, scores),
            "questions": self._generate_questions(property_data)
        }
    
    def _analyze_environment(self, data: Dict) -> float:
        return random.uniform(65, 85)
    
    def _analyze_convenience(self, data: Dict) -> float:
        return random.uniform(70, 90)
    
    def _analyze_safety(self, data: Dict) -> float:
        return random.uniform(75, 95)
    
    def _analyze_education(self, data: Dict) -> float:
        return random.uniform(70, 85)
    
    def _analyze_culture(self, data: Dict) -> float:
        return random.uniform(60, 80)
    
    def _generate_comment(self, total_score: float, scores: Dict) -> str:
        """삼돌이의 개성있는 코멘트 생성"""
        
        comments = []
        
        # 투심이를 살짝 견제하면서 시작
        opening_comments = [
            "투심이가 뭐라고 하든, 살기 좋은 게 제일 중요하지~",
            "아 투심이는 또 투자 얘기만 하네 ㅋㅋ 실제로 살 사람 입장도 좀 생각해봐!",
            "투자도 중요하지만, 매일매일 살아가는 곳인데 환경이 더 중요하지 않을까?"
        ]
        comments.append(random.choice(opening_comments))
        
        if total_score >= 85:
            comments.append("진짜 살기 좋을 것 같은데? 여기서 생활하면 매일이 즐거울 것 같아!")
        elif total_score >= 75:
            comments.append("생활하기에는 나쁘지 않네~ 특히 편의시설이 괜찮아 보여.")
        elif total_score >= 65:
            comments.append("음... 살기에는 평범한 것 같은데? 뭔가 아쉬운 부분이 있어.")
        else:
            comments.append("이건 좀... 생활하기에는 불편할 것 같아. 다른 곳도 알아보는 게 어때?")
        
        # 세부 항목별 코멘트
        if scores["환경"] >= 80:
            comments.append("공원이나 녹지가 가까워서 산책하기 좋을 것 같고!")
        
        if scores["편의성"] >= 85:
            comments.append("마트나 병원도 가깝고... 이런 게 진짜 중요한 거야.")
        
        return " ".join(comments)
    
    def _generate_questions(self, data: Dict) -> List[str]:
        """사용자에게 물어볼 질문들"""
        questions = [
            "가족 구성원은 어떻게 돼? 아이들이 있어?",
            "주로 어떤 편의시설을 자주 이용해?",
            "조용한 곳을 선호해, 아니면 좀 번화한 곳이 좋아?",
            "운동이나 취미생활은 주로 뭘 해?",
            "출퇴근은 어디로 해야 해?"
        ]
        return random.sample(questions, 2)


class CharacterAgentManager:
    """캐릭터 에이전트 관리자"""
    
    def __init__(self):
        self.investment_agent = InvestmentAgent()
        self.life_quality_agent = LifeQualityAgent()
        self.conversation_history = []
    
    def analyze_property_with_characters(self, property_data: Dict[str, Any], 
                                       user_message: str = "") -> Dict[str, Any]:
        """캐릭터들이 함께 부동산을 분석"""
        
        # 투심이가 먼저 분석
        investment_analysis = self.investment_agent.analyze_property(property_data)
        
        # 삼돌이가 이어서 분석
        life_quality_analysis = self.life_quality_agent.analyze_property(property_data)
        
        # 대화 기록 저장
        self.conversation_history.append({
            "user_message": user_message,
            "investment_response": investment_analysis,
            "life_quality_response": life_quality_analysis
        })
        
        return {
            "투심이_분석": investment_analysis,
            "삼돌이_분석": life_quality_analysis,
            "종합_의견": self._generate_combined_opinion(investment_analysis, life_quality_analysis),
            "추가_질문": self._generate_combined_questions(investment_analysis, life_quality_analysis)
        }
    
    def _generate_combined_opinion(self, inv_analysis: Dict, life_analysis: Dict) -> str:
        """두 캐릭터의 종합 의견"""
        
        avg_score = (inv_analysis["total_score"] + life_analysis["total_score"]) / 2
        
        if avg_score >= 85:
            return "투심이와 삼돌이 모두 이 매물을 추천하네요! 투자와 생활 두 마리 토끼를 다 잡을 수 있을 것 같아요."
        elif avg_score >= 75:
            return "의견이 조금 엇갈리긴 하지만, 전반적으로 괜찮은 매물인 것 같아요."
        else:
            return "음... 두 친구 모두 좀 아쉬워하는 것 같네요. 다른 옵션도 알아보시는 게 어떨까요?"
    
    def _generate_combined_questions(self, inv_analysis: Dict, life_analysis: Dict) -> List[str]:
        """두 캐릭터의 질문 통합"""
        all_questions = inv_analysis["questions"] + life_analysis["questions"]
        return list(set(all_questions))  # 중복 제거

# 글로벌 캐릭터 에이전트 매니저
character_manager = CharacterAgentManager()