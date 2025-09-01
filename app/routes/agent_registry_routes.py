"""
Agent Registry Routes
에이전트 레지스트리 관리 API 엔드포인트
"""

import asyncio
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.agent.agent_registry import agent_registry, RegistryAgent
from app.utils.logger import logger

router = APIRouter()


class AgentSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tag: Optional[str] = None
    limit: int = 10


class AgentRegistrationRequest(BaseModel):
    well_known_url: str
    agent_id: Optional[str] = None


class AgentUpdateRequest(BaseModel):
    agent_id: str
    aliases: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None
    trust_level: Optional[int] = None


@router.get("/agents")
async def list_all_agents(
    active_only: bool = Query(True, description="활성 에이전트만 조회"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    tag: Optional[str] = Query(None, description="태그 필터")
):
    """모든 에이전트 목록 조회"""
    try:
        if category:
            agents = agent_registry.get_agents_by_category(category)
        elif tag:
            agents = agent_registry.get_agents_by_tag(tag)
        else:
            agents = agent_registry.get_all_agents(active_only=active_only)
        
        return {
            "success": True,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "specialty": agent.specialty,
                    "capabilities": agent.capabilities,
                    "language": agent.language,
                    "status": agent.status,
                    "trust_level": agent.trust_level,
                    "popularity_score": agent.popularity_score,
                    "aliases": agent.aliases[:3],  # 처음 3개만
                    "keywords": agent.keywords[:5]  # 처음 5개만
                }
                for agent in agents
            ],
            "total": len(agents),
            "filters": {
                "active_only": active_only,
                "category": category,
                "tag": tag
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """특정 에이전트 상세 정보"""
    try:
        agent = agent_registry.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "agent": agent.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/search")
async def search_agents(request: AgentSearchRequest):
    """에이전트 검색"""
    try:
        # 키워드 검색
        keyword_results = agent_registry.search_agents_by_keyword(request.query)
        
        # 추천 에이전트
        recommended_results = agent_registry.get_recommended_agents(request.query, limit=request.limit)
        
        # 결과 병합 및 중복 제거
        all_results = []
        seen_ids = set()
        
        for agent in recommended_results + keyword_results:
            if agent.agent_id not in seen_ids:
                all_results.append(agent)
                seen_ids.add(agent.agent_id)
        
        # 카테고리/태그 필터 적용
        if request.category:
            category_agents = set(a.agent_id for a in agent_registry.get_agents_by_category(request.category))
            all_results = [a for a in all_results if a.agent_id in category_agents]
        
        if request.tag:
            tag_agents = set(a.agent_id for a in agent_registry.get_agents_by_tag(request.tag))
            all_results = [a for a in all_results if a.agent_id in tag_agents]
        
        # 결과 제한
        all_results = all_results[:request.limit]
        
        return {
            "success": True,
            "query": request.query,
            "results": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "specialty": agent.specialty,
                    "relevance_keywords": [kw for kw in agent.keywords if request.query.lower() in kw.lower()][:3],
                    "trust_level": agent.trust_level,
                    "popularity_score": agent.popularity_score,
                    "status": agent.status
                }
                for agent in all_results
            ],
            "total_results": len(all_results),
            "search_filters": {
                "category": request.category,
                "tag": request.tag,
                "limit": request.limit
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/discover")
async def discover_new_agent(request: AgentRegistrationRequest):
    """새 에이전트 발견 및 등록"""
    try:
        new_agent = await agent_registry.discover_and_register_agent(
            request.well_known_url,
            request.agent_id
        )
        
        if new_agent:
            return {
                "success": True,
                "message": f"New agent '{new_agent.name}' discovered and registered",
                "agent": {
                    "agent_id": new_agent.agent_id,
                    "name": new_agent.name,
                    "description": new_agent.description,
                    "specialty": new_agent.specialty,
                    "capabilities": new_agent.capabilities,
                    "status": new_agent.status
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to discover or register agent"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """카테고리 목록 조회"""
    try:
        categories = agent_registry.get_categories()
        
        category_stats = {}
        for category, agent_ids in categories.items():
            active_count = len([
                aid for aid in agent_ids 
                if agent_registry.get_agent_by_id(aid) and agent_registry.get_agent_by_id(aid).status == 'active'
            ])
            category_stats[category] = {
                "total_agents": len(agent_ids),
                "active_agents": active_count,
                "agent_ids": agent_ids
            }
        
        return {
            "success": True,
            "categories": category_stats,
            "total_categories": len(categories),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def list_tags():
    """태그 목록 조회"""
    try:
        tags = agent_registry.get_tags()
        
        tag_stats = {}
        for tag, agent_ids in tags.items():
            active_count = len([
                aid for aid in agent_ids 
                if agent_registry.get_agent_by_id(aid) and agent_registry.get_agent_by_id(aid).status == 'active'
            ])
            tag_stats[tag] = {
                "total_agents": len(agent_ids),
                "active_agents": active_count,
                "agent_ids": agent_ids
            }
        
        return {
            "success": True,
            "tags": tag_stats,
            "total_tags": len(tags),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_registry_stats():
    """레지스트리 통계 정보"""
    try:
        stats = agent_registry.get_registry_stats()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get registry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/update")
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """에이전트 정보 업데이트"""
    try:
        agent = agent_registry.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # 업데이트할 필드들
        updated = False
        if request.aliases is not None:
            agent.aliases = request.aliases
            updated = True
        
        if request.keywords is not None:
            agent.keywords = request.keywords
            updated = True
        
        if request.status is not None:
            agent.status = request.status
            updated = True
        
        if request.trust_level is not None:
            if 1 <= request.trust_level <= 10:
                agent.trust_level = request.trust_level
                updated = True
            else:
                raise HTTPException(status_code=400, detail="Trust level must be between 1 and 10")
        
        if updated:
            # 레지스트리에 다시 저장
            agent_registry.add_agent(agent)
            
            return {
                "success": True,
                "message": f"Agent {agent_id} updated successfully",
                "updated_agent": agent.model_dump(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "No fields to update",
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}")
async def remove_agent(agent_id: str):
    """에이전트 제거"""
    try:
        success = agent_registry.remove_agent(agent_id)
        
        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} removed successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-check")
async def health_check_all_agents():
    """모든 에이전트 상태 확인"""
    try:
        logger.info("Starting health check for all agents...")
        health_results = await agent_registry.health_check_all_agents()
        
        # 결과 요약
        healthy = len([r for r in health_results.values() if r == "healthy"])
        unhealthy = len([r for r in health_results.values() if r == "unhealthy"])
        unreachable = len([r for r in health_results.values() if r == "unreachable"])
        
        return {
            "success": True,
            "message": "Health check completed for all agents",
            "summary": {
                "total_agents": len(health_results),
                "healthy": healthy,
                "unhealthy": unhealthy,
                "unreachable": unreachable
            },
            "detailed_results": health_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{message}")
async def get_agent_recommendations(message: str, limit: int = Query(3, description="추천 에이전트 수")):
    """메시지 기반 에이전트 추천"""
    try:
        recommended_agents = agent_registry.get_recommended_agents(message, limit=limit)
        
        return {
            "success": True,
            "message": message,
            "recommendations": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "specialty": agent.specialty,
                    "trust_level": agent.trust_level,
                    "popularity_score": agent.popularity_score,
                    "matching_keywords": [kw for kw in agent.keywords if any(word.lower() in kw.lower() for word in message.lower().split())],
                    "matching_aliases": [alias for alias in agent.aliases if any(word.lower() in alias.lower() for word in message.lower().split())]
                }
                for agent in recommended_agents
            ],
            "total_recommendations": len(recommended_agents),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))