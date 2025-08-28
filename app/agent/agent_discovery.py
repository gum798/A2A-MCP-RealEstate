"""
Agent Discovery System
에이전트 카드 기반 디스커버리 시스템 구현
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import httpx
import dns.resolver
from loguru import logger

from ..utils.config import get_settings

settings = get_settings()

class AgentDiscovery:
    def __init__(self):
        self.discovered_agents: Dict[str, Dict] = {}
        self.agent_card_path = Path(__file__).parent.parent.parent / "agent.json"
        
    async def load_agent_card(self) -> Dict:
        """로컬 에이전트 카드 로드"""
        try:
            with open(self.agent_card_path, 'r', encoding='utf-8') as f:
                agent_card = json.load(f)
            logger.info("Agent card loaded successfully")
            return agent_card
        except Exception as e:
            logger.error(f"Failed to load agent card: {e}")
            return {}
    
    async def discover_agent_by_dns(self, domain: str) -> Optional[Dict]:
        """DNS TXT 레코드를 통한 에이전트 디스커버리"""
        try:
            txt_query = f"_agent.{domain}"
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(txt_query, 'TXT')
            
            for rdata in answers:
                txt_data = str(rdata).strip('"')
                if txt_data.startswith('agent-card='):
                    card_url = txt_data.split('=', 1)[1]
                    return await self.fetch_agent_card(card_url)
                    
        except Exception as e:
            logger.warning(f"DNS discovery failed for {domain}: {e}")
        return None
    
    async def discover_agent_by_well_known(self, base_url: str) -> Optional[Dict]:
        """Well-known 엔드포인트를 통한 에이전트 디스커버리"""
        try:
            well_known_url = f"{base_url.rstrip('/')}/.well-known/agent-card"
            return await self.fetch_agent_card(well_known_url)
        except Exception as e:
            logger.warning(f"Well-known discovery failed for {base_url}: {e}")
        return None
    
    async def fetch_agent_card(self, url: str) -> Optional[Dict]:
        """URL에서 에이전트 카드 가져오기"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                agent_card = response.json()
                
                # 기본 검증
                required_fields = ['name', 'description', 'url', 'capabilities']
                if all(field in agent_card for field in required_fields):
                    return agent_card
                else:
                    logger.warning(f"Invalid agent card structure from {url}")
                    
        except Exception as e:
            logger.error(f"Failed to fetch agent card from {url}: {e}")
        return None
    
    async def register_agent(self, agent_id: str, agent_card: Dict):
        """에이전트 등록"""
        self.discovered_agents[agent_id] = {
            **agent_card,
            'discovered_at': asyncio.get_event_loop().time(),
            'status': 'active'
        }
        logger.info(f"Agent registered: {agent_id}")
    
    async def discover_agents_from_registry(self, registry_url: str) -> List[Dict]:
        """레지스트리에서 에이전트 목록 조회"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{registry_url}/agents")
                response.raise_for_status()
                agents = response.json()
                
                discovered = []
                for agent_info in agents:
                    if 'agent_card_url' in agent_info:
                        card = await self.fetch_agent_card(agent_info['agent_card_url'])
                        if card:
                            discovered.append(card)
                
                return discovered
                
        except Exception as e:
            logger.error(f"Registry discovery failed for {registry_url}: {e}")
        return []
    
    async def health_check_agent(self, agent_url: str) -> bool:
        """에이전트 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{agent_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_agent_capabilities(self, agent_id: str) -> Optional[Dict]:
        """에이전트 기능 조회"""
        if agent_id in self.discovered_agents:
            return self.discovered_agents[agent_id].get('capabilities')
        return None
    
    async def find_agents_by_capability(self, capability: str) -> List[str]:
        """특정 기능을 가진 에이전트 검색"""
        matching_agents = []
        for agent_id, agent_info in self.discovered_agents.items():
            capabilities = agent_info.get('capabilities', {})
            primary_functions = capabilities.get('primary_functions', [])
            
            if capability in primary_functions:
                matching_agents.append(agent_id)
        
        return matching_agents
    
    async def get_discovery_info(self) -> Dict[str, Any]:
        """디스커버리 시스템 정보 반환"""
        return {
            'total_agents': len(self.discovered_agents),
            'agents': {
                agent_id: {
                    'name': info.get('name'),
                    'description': info.get('description'),
                    'url': info.get('url'),
                    'status': info.get('status'),
                    'capabilities': info.get('capabilities', {}).get('primary_functions', [])
                }
                for agent_id, info in self.discovered_agents.items()
            },
            'discovery_methods': [
                'dns_txt_record',
                'well_known_endpoint', 
                'manual_configuration',
                'registry_based'
            ]
        }

# 글로벌 디스커버리 인스턴스
agent_discovery = AgentDiscovery()