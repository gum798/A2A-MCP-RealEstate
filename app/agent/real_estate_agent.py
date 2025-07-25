"""
부동산 추천 Agent 시스템
투자가치 Agent와 삶의질가치 Agent를 통합한 추천 시스템
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..utils.logger import logger
from ..utils.config import settings

@dataclass
class PropertyInfo:
    """부동산 정보 데이터 클래스"""
    address: str
    lat: float
    lon: float
    price: int  # 만원 단위
    area: float  # 전용면적 (㎡)
    floor: int
    total_floor: int
    building_year: int
    property_type: str  # 아파트, 오피스텔, 연립다세대
    deal_type: str  # 매매, 전세, 월세

@dataclass
class LocationAnalysis:
    """위치 분석 결과"""
    subway_distance: float
    nearest_stations: List[Dict[str, Any]]
    facilities_count: int
    park_distance: Optional[float]
    location_score: float
    location_grade: str

@dataclass
class InvestmentScore:
    """투자가치 점수"""
    total_score: float
    grade: str
    price_score: float
    area_score: float
    floor_score: float
    transport_score: float
    future_potential_score: float

@dataclass
class LifeQualityScore:
    """삶의질 점수"""
    total_score: float
    grade: str
    environment_score: float
    convenience_score: float
    safety_score: float
    education_score: float
    culture_score: float

class RealEstateAgent(ABC):
    """부동산 Agent 기본 클래스"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logger.bind(agent=agent_name)
    
    @abstractmethod
    async def evaluate_property(self, property_info: PropertyInfo, location_analysis: LocationAnalysis) -> Dict[str, Any]:
        """부동산 평가 (추상 메서드)"""
        pass
    
    async def get_location_analysis(self, address: str, lat: float = None, lon: float = None) -> LocationAnalysis:
        """위치 분석 수행"""
        try:
            # Location Service MCP 서버 호출 (실제로는 FastMCP 클라이언트 사용)
            # 여기서는 간단한 예시로 구현
            
            # 가장 가까운 지하철역 검색
            subway_distance = 0.8  # 예시 값
            nearest_stations = [
                {"station_name": "강남역", "distance_km": 0.8, "lines": ["2호선", "신분당선"]}
            ]
            
            # 편의시설 개수
            facilities_count = 25  # 예시 값
            
            # 공원 거리
            park_distance = 0.5  # 예시 값
            
            # 위치 점수 계산
            location_score = self._calculate_location_score(subway_distance, facilities_count, park_distance)
            location_grade = self._score_to_grade(location_score)
            
            return LocationAnalysis(
                subway_distance=subway_distance,
                nearest_stations=nearest_stations,
                facilities_count=facilities_count,
                park_distance=park_distance,
                location_score=location_score,
                location_grade=location_grade
            )
            
        except Exception as e:
            self.logger.error(f"위치 분석 중 오류: {e}")
            raise
    
    def _calculate_location_score(self, subway_distance: float, facilities_count: int, park_distance: float) -> float:
        """위치 점수 계산"""
        # 교통 점수
        if subway_distance <= 0.5:
            transport_score = 100
        elif subway_distance <= 1.0:
            transport_score = 80
        elif subway_distance <= 1.5:
            transport_score = 60
        else:
            transport_score = 40
        
        # 편의성 점수
        if facilities_count >= 30:
            convenience_score = 100
        elif facilities_count >= 20:
            convenience_score = 80
        elif facilities_count >= 10:
            convenience_score = 60
        else:
            convenience_score = 40
        
        # 환경 점수
        if park_distance <= 0.3:
            environment_score = 100
        elif park_distance <= 0.5:
            environment_score = 80
        elif park_distance <= 1.0:
            environment_score = 60
        else:
            environment_score = 40
        
        return (transport_score * 0.4 + convenience_score * 0.35 + environment_score * 0.25)
    
    def _score_to_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        else:
            return "C"

class InvestmentAgent(RealEstateAgent):
    """투자가치 평가 Agent"""
    
    def __init__(self):
        super().__init__("투자가치 평가 Agent")
    
    async def evaluate_property(self, property_info: PropertyInfo, location_analysis: LocationAnalysis) -> InvestmentScore:
        """투자가치 관점에서 부동산 평가"""
        try:
            self.logger.info(f"투자가치 평가 시작: {property_info.address}")
            
            # 1. 가격 점수 (시세 대비 합리성)
            price_score = self._evaluate_price(property_info)
            
            # 2. 면적 점수 (넓이의 효율성)
            area_score = self._evaluate_area(property_info)
            
            # 3. 층수 점수 (투자 관점에서의 층수 선호도)
            floor_score = self._evaluate_floor(property_info)
            
            # 4. 교통 점수 (지하철 접근성)
            transport_score = self._evaluate_transport(location_analysis)
            
            # 5. 미래 발전 가능성 점수
            future_potential_score = self._evaluate_future_potential(property_info, location_analysis)
            
            # 종합 점수 계산 (가중평균)
            total_score = (
                price_score * 0.25 +
                area_score * 0.20 +
                floor_score * 0.15 +
                transport_score * 0.25 +
                future_potential_score * 0.15
            )
            
            grade = self._score_to_grade(total_score)
            
            self.logger.info(f"투자가치 평가 완료: {total_score:.1f}점 ({grade})")
            
            return InvestmentScore(
                total_score=round(total_score, 1),
                grade=grade,
                price_score=price_score,
                area_score=area_score,
                floor_score=floor_score,
                transport_score=transport_score,
                future_potential_score=future_potential_score
            )
            
        except Exception as e:
            self.logger.error(f"투자가치 평가 중 오류: {e}")
            raise
    
    def _evaluate_price(self, property_info: PropertyInfo) -> float:
        """가격 평가"""
        # 평당 가격 계산 (3.3㎡ = 1평)
        price_per_pyeong = property_info.price / (property_info.area / 3.3)
        
        # 지역별 평균 시세와 비교 (예시)
        if property_info.address.startswith("서울"):
            if price_per_pyeong <= 8000:  # 8천만원/평 이하
                return 100
            elif price_per_pyeong <= 12000:
                return 80
            elif price_per_pyeong <= 16000:
                return 60
            else:
                return 40
        else:
            if price_per_pyeong <= 3000:
                return 100
            elif price_per_pyeong <= 5000:
                return 80
            elif price_per_pyeong <= 7000:
                return 60
            else:
                return 40
    
    def _evaluate_area(self, property_info: PropertyInfo) -> float:
        """면적 평가"""
        # 투자 관점에서 선호하는 면적대
        area_pyeong = property_info.area / 3.3
        
        if 20 <= area_pyeong <= 35:  # 20-35평 (가장 선호)
            return 100
        elif 15 <= area_pyeong < 20 or 35 < area_pyeong <= 45:
            return 80
        elif 10 <= area_pyeong < 15 or 45 < area_pyeong <= 60:
            return 60
        else:
            return 40
    
    def _evaluate_floor(self, property_info: PropertyInfo) -> float:
        """층수 평가"""
        floor_rate = property_info.floor / property_info.total_floor
        
        # 중간층~중상층 선호 (투자 관점)
        if 0.3 <= floor_rate <= 0.8:
            return 100
        elif 0.2 <= floor_rate < 0.3 or 0.8 < floor_rate <= 0.9:
            return 80
        else:
            return 60
    
    def _evaluate_transport(self, location_analysis: LocationAnalysis) -> float:
        """교통 평가"""
        # 지하철 거리 기반
        if location_analysis.subway_distance <= 0.5:
            return 100
        elif location_analysis.subway_distance <= 1.0:
            return 80
        elif location_analysis.subway_distance <= 1.5:
            return 60
        else:
            return 40
    
    def _evaluate_future_potential(self, property_info: PropertyInfo, location_analysis: LocationAnalysis) -> float:
        """미래 발전 가능성 평가"""
        score = 50  # 기본 점수
        
        # 재건축 연한 (30년 이상 시 가점)
        current_year = datetime.now().year
        building_age = current_year - property_info.building_year
        if building_age >= 30:
            score += 20
        elif building_age >= 20:
            score += 10
        
        # 역세권 (지하철 500m 이내 시 가점)
        if location_analysis.subway_distance <= 0.5:
            score += 20
        elif location_analysis.subway_distance <= 1.0:
            score += 10
        
        # 복합역 (환승역 시 가점)
        for station in location_analysis.nearest_stations:
            if len(station.get("lines", [])) >= 2:
                score += 10
                break
        
        return min(score, 100)

class LifeQualityAgent(RealEstateAgent):
    """삶의질가치 평가 Agent"""
    
    def __init__(self):
        super().__init__("삶의질가치 평가 Agent")
    
    async def evaluate_property(self, property_info: PropertyInfo, location_analysis: LocationAnalysis) -> LifeQualityScore:
        """삶의질 관점에서 부동산 평가"""
        try:
            self.logger.info(f"삶의질가치 평가 시작: {property_info.address}")
            
            # 1. 환경 점수 (공원, 녹지, 공기질 등)
            environment_score = self._evaluate_environment(location_analysis)
            
            # 2. 편의성 점수 (마트, 병원, 편의점 등)
            convenience_score = self._evaluate_convenience(location_analysis)
            
            # 3. 안전 점수 (치안, 교통사고 등)
            safety_score = self._evaluate_safety(property_info, location_analysis)
            
            # 4. 교육 점수 (학교, 학원가 등)
            education_score = self._evaluate_education(location_analysis)
            
            # 5. 문화 점수 (문화시설, 여가시설 등)
            culture_score = self._evaluate_culture(location_analysis)
            
            # 종합 점수 계산 (가중평균)
            total_score = (
                environment_score * 0.25 +
                convenience_score * 0.25 +
                safety_score * 0.20 +
                education_score * 0.15 +
                culture_score * 0.15
            )
            
            grade = self._score_to_grade(total_score)
            
            self.logger.info(f"삶의질가치 평가 완료: {total_score:.1f}점 ({grade})")
            
            return LifeQualityScore(
                total_score=round(total_score, 1),
                grade=grade,
                environment_score=environment_score,
                convenience_score=convenience_score,
                safety_score=safety_score,
                education_score=education_score,
                culture_score=culture_score
            )
            
        except Exception as e:
            self.logger.error(f"삶의질가치 평가 중 오류: {e}")
            raise
    
    def _evaluate_environment(self, location_analysis: LocationAnalysis) -> float:
        """환경 평가"""
        score = 50  # 기본 점수
        
        # 공원 거리
        if location_analysis.park_distance:
            if location_analysis.park_distance <= 0.3:
                score += 30
            elif location_analysis.park_distance <= 0.5:
                score += 20
            elif location_analysis.park_distance <= 1.0:
                score += 10
        
        # 한강 접근성 (예시로 강남, 여의도 등 한강 근처 지역 가점)
        # 실제로는 더 정교한 로직 필요
        
        return min(score, 100)
    
    def _evaluate_convenience(self, location_analysis: LocationAnalysis) -> float:
        """편의성 평가"""
        # 편의시설 개수 기반
        if location_analysis.facilities_count >= 40:
            return 100
        elif location_analysis.facilities_count >= 30:
            return 85
        elif location_analysis.facilities_count >= 20:
            return 70
        elif location_analysis.facilities_count >= 10:
            return 55
        else:
            return 40
    
    def _evaluate_safety(self, property_info: PropertyInfo, location_analysis: LocationAnalysis) -> float:
        """안전 평가"""
        score = 70  # 기본 점수
        
        # 대로변 여부 (소음, 사고 위험)
        # 실제로는 도로 정보가 필요하지만 예시로 구현
        
        # 층수 (1층은 보안 우려로 감점)
        if property_info.floor == 1:
            score -= 10
        elif property_info.floor >= 15:
            score -= 5  # 화재 시 피난 우려
        
        return max(score, 30)
    
    def _evaluate_education(self, location_analysis: LocationAnalysis) -> float:
        """교육 평가"""
        # 학교, 학원가 접근성
        # 실제로는 교육시설 데이터가 필요하지만 예시로 구현
        return 70  # 기본 점수
    
    def _evaluate_culture(self, location_analysis: LocationAnalysis) -> float:
        """문화 평가"""
        # 문화시설, 여가시설 접근성
        # 실제로는 문화시설 데이터가 필요하지만 예시로 구현
        return 65  # 기본 점수

class RealEstateRecommendationSystem:
    """부동산 추천 시스템"""
    
    def __init__(self):
        self.investment_agent = InvestmentAgent()
        self.life_quality_agent = LifeQualityAgent()
        self.logger = logger.bind(system="부동산추천시스템")
    
    async def recommend_property(self, property_info: PropertyInfo, user_preference: str = "균형") -> Dict[str, Any]:
        """
        부동산 추천
        
        Args:
            property_info: 부동산 정보
            user_preference: 사용자 선호도 ("투자", "삶의질", "균형")
        
        Returns:
            종합 추천 결과
        """
        try:
            self.logger.info(f"부동산 추천 시작: {property_info.address}")
            
            # 위치 분석
            location_analysis = await self.investment_agent.get_location_analysis(
                property_info.address, property_info.lat, property_info.lon
            )
            
            # 투자가치 평가
            investment_score = await self.investment_agent.evaluate_property(
                property_info, location_analysis
            )
            
            # 삶의질가치 평가
            life_quality_score = await self.life_quality_agent.evaluate_property(
                property_info, location_analysis
            )
            
            # 사용자 선호도에 따른 가중치 조정
            if user_preference == "투자":
                final_score = investment_score.total_score * 0.8 + life_quality_score.total_score * 0.2
            elif user_preference == "삶의질":
                final_score = investment_score.total_score * 0.2 + life_quality_score.total_score * 0.8
            else:  # 균형
                final_score = investment_score.total_score * 0.5 + life_quality_score.total_score * 0.5
            
            final_grade = self.investment_agent._score_to_grade(final_score)
            
            # 추천 사유 생성
            recommendation_reason = self._generate_recommendation_reason(
                investment_score, life_quality_score, location_analysis, user_preference
            )
            
            result = {
                "property_info": {
                    "address": property_info.address,
                    "price": property_info.price,
                    "area": property_info.area,
                    "floor": f"{property_info.floor}/{property_info.total_floor}",
                    "building_year": property_info.building_year,
                    "property_type": property_info.property_type,
                    "deal_type": property_info.deal_type
                },
                "evaluation": {
                    "final_score": round(final_score, 1),
                    "final_grade": final_grade,
                    "user_preference": user_preference,
                    "investment_score": investment_score,
                    "life_quality_score": life_quality_score,
                    "location_analysis": location_analysis
                },
                "recommendation": {
                    "recommended": final_score >= 70,
                    "reason": recommendation_reason,
                    "pros": self._extract_pros(investment_score, life_quality_score, location_analysis),
                    "cons": self._extract_cons(investment_score, life_quality_score, location_analysis)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"부동산 추천 완료: {final_score:.1f}점 ({final_grade})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"부동산 추천 중 오류: {e}")
            raise
    
    def _generate_recommendation_reason(self, investment_score: InvestmentScore, 
                                      life_quality_score: LifeQualityScore,
                                      location_analysis: LocationAnalysis,
                                      user_preference: str) -> str:
        """추천 사유 생성"""
        reasons = []
        
        if user_preference == "투자":
            if investment_score.transport_score >= 80:
                reasons.append("교통접근성이 우수하여 투자가치가 높습니다")
            if investment_score.future_potential_score >= 80:
                reasons.append("향후 발전 가능성이 높아 투자 수익을 기대할 수 있습니다")
        elif user_preference == "삶의질":
            if life_quality_score.environment_score >= 80:
                reasons.append("주변 환경이 쾌적하여 거주 만족도가 높습니다")
            if life_quality_score.convenience_score >= 80:
                reasons.append("생활 편의시설이 풍부하여 편리한 생활이 가능합니다")
        else:
            if location_analysis.location_score >= 80:
                reasons.append("입지 조건이 우수하여 투자와 거주 모두에 적합합니다")
        
        return " | ".join(reasons) if reasons else "종합적으로 고려할 때 적정한 수준의 매물입니다"
    
    def _extract_pros(self, investment_score: InvestmentScore, 
                     life_quality_score: LifeQualityScore,
                     location_analysis: LocationAnalysis) -> List[str]:
        """장점 추출"""
        pros = []
        
        if investment_score.transport_score >= 80:
            pros.append(f"지하철 {location_analysis.subway_distance}km 역세권")
        if life_quality_score.convenience_score >= 80:
            pros.append(f"편의시설 {location_analysis.facilities_count}개 풍부")
        if life_quality_score.environment_score >= 80:
            pros.append("주변 환경 쾌적")
        if investment_score.future_potential_score >= 80:
            pros.append("미래 발전 가능성 높음")
        
        return pros
    
    def _extract_cons(self, investment_score: InvestmentScore,
                     life_quality_score: LifeQualityScore,
                     location_analysis: LocationAnalysis) -> List[str]:
        """단점 추출"""
        cons = []
        
        if investment_score.transport_score < 60:
            cons.append("교통접근성 다소 아쉬움")
        if life_quality_score.convenience_score < 60:
            cons.append("편의시설 부족")
        if investment_score.price_score < 60:
            cons.append("시세 대비 가격 높음")
        if life_quality_score.environment_score < 60:
            cons.append("주변 환경 개선 필요")
        
        return cons