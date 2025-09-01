"""
Agent Registry Manager
A2A 에이전트 레지스트리 관리 시스템
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import httpx
from loguru import logger

from .agent_discovery import agent_discovery


class RegistryAgent(BaseModel):
    """레지스트리에 등록된 에이전트 정보"""
    agent_id: str
    name: str
    description: str
    well_known_url: str
    base_url: str
    aliases: List[str]
    keywords: List[str]
    capabilities: List[str]
    specialty: str
    language: List[str]
    personality_traits: List[str]
    status: str = "active"
    trust_level: int = 5  # 1-10
    popularity_score: int = 50  # 1-100


class AgentRegistry:
    """에이전트 레지스트리 관리자"""
    
    def __init__(self, registry_file: str = None):
        self.registry_file = registry_file or str(Path(__file__).parent.parent / "data" / "agent_registry.json")
        self.registry_data: Dict[str, Any] = {}
        self.agents: Dict[str, RegistryAgent] = {}
        self.categories: Dict[str, List[str]] = {}
        self.tags: Dict[str, List[str]] = {}
        
        # 레지스트리 로드
        self._load_registry()
    
    def _load_registry(self):
        """레지스트리 파일 로드"""
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                self.registry_data = json.load(f)
            
            # 에이전트 데이터 파싱
            for agent_data in self.registry_data.get("agents", []):
                agent = RegistryAgent(**agent_data)
                self.agents[agent.agent_id] = agent
            
            self.categories = self.registry_data.get("categories", {})
            self.tags = self.registry_data.get("tags", {})
            
            logger.info(f"Agent registry loaded: {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to load agent registry: {e}")
            self.registry_data = {"agents": [], "categories": {}, "tags": {}}
    
    def _save_registry(self):
        """레지스트리 파일 저장"""
        try:
            # 에이전트 데이터 업데이트
            self.registry_data["agents"] = [
                agent.model_dump() for agent in self.agents.values()
            ]
            self.registry_data["categories"] = self.categories
            self.registry_data["tags"] = self.tags
            self.registry_data["registry_info"]["last_updated"] = datetime.now().isoformat()
            self.registry_data["registry_info"]["total_agents"] = len(self.agents)
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Agent registry saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save agent registry: {e}")
    
    def get_agent_by_id(self, agent_id: str) -> Optional[RegistryAgent]:
        """에이전트 ID로 조회"""
        return self.agents.get(agent_id)
    
    def get_agent_by_alias(self, alias: str) -> Optional[RegistryAgent]:
        """별명으로 에이전트 조회"""
        alias_lower = alias.lower()
        for agent in self.agents.values():
            if alias_lower in [a.lower() for a in agent.aliases]:
                return agent
            if alias_lower in agent.name.lower():
                return agent
        return None
    
    def search_agents_by_keyword(self, keyword: str) -> List[RegistryAgent]:
        """키워드로 에이전트 검색"""
        keyword_lower = keyword.lower()
        matching_agents = []
        
        for agent in self.agents.values():
            # 키워드 매칭
            for kw in agent.keywords:
                if keyword_lower in kw.lower():
                    matching_agents.append(agent)
                    break
            else:
                # 이름, 설명, 전문분야에서도 검색
                if (keyword_lower in agent.name.lower() or 
                    keyword_lower in agent.description.lower() or
                    keyword_lower in agent.specialty.lower()):
                    matching_agents.append(agent)
        
        # 인기도 순으로 정렬
        matching_agents.sort(key=lambda x: x.popularity_score, reverse=True)
        return matching_agents
    
    def get_agents_by_category(self, category: str) -> List[RegistryAgent]:
        """카테고리별 에이전트 조회"""
        agent_ids = self.categories.get(category, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_agents_by_tag(self, tag: str) -> List[RegistryAgent]:
        """태그별 에이전트 조회"""
        agent_ids = self.tags.get(tag, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_recommended_agents(self, user_message: str, limit: int = 3) -> List[RegistryAgent]:
        """사용자 메시지 기반 에이전트 추천"""
        message_lower = user_message.lower()
        agent_scores = {}
        
        for agent_id, agent in self.agents.items():
            score = 0
            
            # 키워드 매칭 (가중치 3)
            for keyword in agent.keywords:
                if keyword.lower() in message_lower:
                    score += 3
            
            # 별명 매칭 (가중치 5)
            for alias in agent.aliases:
                if alias.lower() in message_lower:
                    score += 5
            
            # 이름 매칭 (가중치 4)
            if agent.name.lower() in message_lower:
                score += 4
            
            # 전문분야 매칭 (가중치 2)
            if agent.specialty.lower() in message_lower:
                score += 2
            
            # 신뢰도와 인기도 반영 (가중치 1)
            score += (agent.trust_level + agent.popularity_score // 20)
            
            if score > 0:
                agent_scores[agent_id] = score
        
        # 점수 순으로 정렬
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [self.agents[agent_id] for agent_id, _ in sorted_agents[:limit]]
    
    async def discover_and_register_agent(self, well_known_url: str, agent_id: str = None) -> Optional[RegistryAgent]:
        """새 에이전트 발견 및 등록"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(well_known_url)
                response.raise_for_status()
                agent_data = response.json()
            
            # 기본 에이전트 정보 추출
            if not agent_id:
                agent_id = agent_data.get('id') or f"agent-{hash(well_known_url) % 10000}"
            
            base_url = agent_data.get('url', well_known_url.replace('/.well-known/agent.json', ''))
            
            # 레지스트리 에이전트 생성
            new_agent = RegistryAgent(
                agent_id=agent_id,
                name=agent_data.get('name', 'Unknown Agent'),
                description=agent_data.get('description', ''),
                well_known_url=well_known_url,
                base_url=base_url,
                aliases=[agent_data.get('name', '').lower()],
                keywords=agent_data.get('capabilities', {}).get('skills', []),
                capabilities=list(agent_data.get('capabilities', {}).keys()),
                specialty=agent_data.get('description', '')[:50],
                language=['English'],  # 기본값
                personality_traits=[],
                status='active',
                trust_level=5,
                popularity_score=50
            )
            
            # 레지스트리에 추가
            self.agents[agent_id] = new_agent
            self._save_registry()
            
            logger.info(f"New agent registered: {new_agent.name} ({agent_id})")
            return new_agent
            
        except Exception as e:
            logger.error(f"Failed to discover and register agent: {e}")
            return None
    
    def add_agent(self, agent: RegistryAgent):
        """에이전트 수동 추가"""
        self.agents[agent.agent_id] = agent
        self._save_registry()
        logger.info(f"Agent added: {agent.name} ({agent.agent_id})")
    
    def remove_agent(self, agent_id: str) -> bool:
        """에이전트 제거"""
        if agent_id in self.agents:
            agent_name = self.agents[agent_id].name
            del self.agents[agent_id]
            
            # 카테고리와 태그에서도 제거
            for category_agents in self.categories.values():
                if agent_id in category_agents:
                    category_agents.remove(agent_id)
            
            for tag_agents in self.tags.values():
                if agent_id in tag_agents:
                    tag_agents.remove(agent_id)
            
            self._save_registry()
            logger.info(f"Agent removed: {agent_name} ({agent_id})")
            return True
        
        return False
    
    def update_agent_status(self, agent_id: str, status: str):
        """에이전트 상태 업데이트"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self._save_registry()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """레지스트리 통계 정보"""
        active_agents = [a for a in self.agents.values() if a.status == 'active']
        
        return {
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "categories": len(self.categories),
            "tags": len(self.tags),
            "avg_trust_level": sum(a.trust_level for a in active_agents) / len(active_agents) if active_agents else 0,
            "avg_popularity": sum(a.popularity_score for a in active_agents) / len(active_agents) if active_agents else 0,
            "languages": list(set(lang for agent in active_agents for lang in agent.language)),
            "specialties": list(set(agent.specialty for agent in active_agents))
        }
    
    def get_all_agents(self, active_only: bool = True) -> List[RegistryAgent]:
        """모든 에이전트 조회"""
        agents = list(self.agents.values())
        
        if active_only:
            agents = [a for a in agents if a.status == 'active']
        
        # 인기도 순으로 정렬
        agents.sort(key=lambda x: (x.trust_level, x.popularity_score), reverse=True)
        return agents
    
    def get_categories(self) -> Dict[str, List[str]]:
        """카테고리 목록"""
        return self.categories.copy()
    
    def get_tags(self) -> Dict[str, List[str]]:
        """태그 목록"""
        return self.tags.copy()
    
    async def health_check_all_agents(self) -> Dict[str, str]:
        """모든 에이전트 상태 확인"""
        results = {}
        
        async def check_agent(agent: RegistryAgent):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Try multiple health check endpoints in order
                    health_endpoints = [
                        f"{agent.base_url}/health",
                        agent.well_known_url,  # Try well-known endpoint
                        agent.base_url.rstrip('/'),  # Try base URL
                    ]
                    
                    for endpoint in health_endpoints:
                        try:
                            response = await client.get(endpoint)
                            if response.status_code == 200:
                                results[agent.agent_id] = "healthy"
                                self.update_agent_status(agent.agent_id, "active")
                                return
                        except Exception:
                            continue
                    
                    # If all endpoints fail
                    results[agent.agent_id] = "unhealthy"
                    self.update_agent_status(agent.agent_id, "inactive")
                    
            except Exception:
                results[agent.agent_id] = "unreachable"
                self.update_agent_status(agent.agent_id, "error")
        
        # 모든 에이전트 동시 확인
        tasks = [check_agent(agent) for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results


# 글로벌 레지스트리 인스턴스
agent_registry = AgentRegistry()