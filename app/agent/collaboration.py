"""
Agent Collaboration Framework
에이전트 간 협업을 위한 고급 기능
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from .a2a_agent import A2AAgent
from .agent_discovery import agent_discovery


class TaskRequest(BaseModel):
    """협업 작업 요청"""
    task_id: str
    requester_id: str
    task_type: str
    description: str
    requirements: Dict[str, Any]
    priority: int = 1  # 1-5 (5가 가장 높음)
    deadline: Optional[datetime] = None
    collaboration_type: str = "sequential"  # sequential, parallel, pipeline


class TaskResponse(BaseModel):
    """작업 응답"""
    task_id: str
    agent_id: str
    status: str  # accepted, rejected, completed, failed
    result: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None
    completion_time: Optional[datetime] = None


class CollaborationWorkflow(BaseModel):
    """협업 워크플로우"""
    workflow_id: str
    name: str
    description: str
    agents: List[str]
    steps: List[Dict[str, Any]]
    status: str = "pending"
    created_at: datetime = datetime.now()


class CollaborativeAgent:
    """협업 기능이 강화된 A2A 에이전트"""
    
    def __init__(self, base_agent: A2AAgent):
        self.agent = base_agent
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.completed_tasks: Dict[str, TaskResponse] = {}
        self.workflows: Dict[str, CollaborationWorkflow] = {}
        self.capabilities: Dict[str, int] = {}  # capability -> skill_level (1-10)
        self.collaboration_partners: Dict[str, Dict] = {}
        
    async def register_capability(self, capability: str, skill_level: int):
        """기능 등록"""
        self.capabilities[capability] = skill_level
        logger.info(f"Agent {self.agent.agent_id} registered capability: {capability} (level {skill_level})")
    
    async def request_collaboration(self, task: TaskRequest, target_agents: List[str] = None) -> List[TaskResponse]:
        """협업 요청"""
        if not target_agents:
            # 자동으로 적합한 에이전트 찾기
            target_agents = await self._find_suitable_agents(task)
        
        responses = []
        for agent_id in target_agents:
            try:
                response = await self.agent.send_message(
                    agent_id,
                    "collaboration_request",
                    {
                        "task": task.model_dump(),
                        "requester_capabilities": self.capabilities
                    }
                )
                if response:
                    responses.append(TaskResponse(**response))
            except Exception as e:
                logger.error(f"Failed to request collaboration from {agent_id}: {e}")
        
        return responses
    
    async def handle_collaboration_request(self, request_data: Dict) -> TaskResponse:
        """협업 요청 처리"""
        task = TaskRequest(**request_data["task"])
        
        # 작업 수용 가능성 평가
        can_handle = await self._evaluate_task_capability(task)
        
        if can_handle:
            self.active_tasks[task.task_id] = task
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent.agent_id,
                status="accepted"
            )
        else:
            # 다른 적합한 에이전트 추천
            suggested_agents = await self._find_suitable_agents(task)
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent.agent_id,
                status="rejected",
                result={"suggested_agents": suggested_agents}
            )
    
    async def create_workflow(self, workflow: CollaborationWorkflow) -> bool:
        """협업 워크플로우 생성"""
        try:
            self.workflows[workflow.workflow_id] = workflow
            
            # 참여 에이전트들에게 워크플로우 정보 전송
            for agent_id in workflow.agents:
                await self.agent.send_message(
                    agent_id,
                    "workflow_invitation",
                    {
                        "workflow": workflow.model_dump(),
                        "coordinator": self.agent.agent_id
                    }
                )
            
            logger.info(f"Workflow created: {workflow.name} ({workflow.workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 실행"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.status = "running"
        
        results = {}
        try:
            if workflow.name == "sequential":
                results = await self._execute_sequential_workflow(workflow)
            elif workflow.name == "parallel":
                results = await self._execute_parallel_workflow(workflow)
            elif workflow.name == "pipeline":
                results = await self._execute_pipeline_workflow(workflow)
            
            workflow.status = "completed"
            
        except Exception as e:
            workflow.status = "failed"
            logger.error(f"Workflow execution failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _execute_sequential_workflow(self, workflow: CollaborationWorkflow) -> Dict:
        """순차 실행 워크플로우"""
        results = {}
        current_data = {}
        
        for i, step in enumerate(workflow.steps):
            agent_id = workflow.agents[i % len(workflow.agents)]
            
            task_request = TaskRequest(
                task_id=f"{workflow.workflow_id}_step_{i}",
                requester_id=self.agent.agent_id,
                task_type=step["type"],
                description=step["description"],
                requirements={**step.get("requirements", {}), **current_data}
            )
            
            response = await self.request_collaboration(task_request, [agent_id])
            if response and response[0].status == "completed":
                current_data = response[0].result or {}
                results[f"step_{i}"] = current_data
            else:
                raise Exception(f"Step {i} failed")
        
        return results
    
    async def _execute_parallel_workflow(self, workflow: CollaborationWorkflow) -> Dict:
        """병렬 실행 워크플로우"""
        tasks = []
        
        for i, step in enumerate(workflow.steps):
            agent_id = workflow.agents[i % len(workflow.agents)]
            
            task_request = TaskRequest(
                task_id=f"{workflow.workflow_id}_parallel_{i}",
                requester_id=self.agent.agent_id,
                task_type=step["type"],
                description=step["description"],
                requirements=step.get("requirements", {})
            )
            
            tasks.append(self.request_collaboration(task_request, [agent_id]))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {f"task_{i}": result for i, result in enumerate(results)}
    
    async def _execute_pipeline_workflow(self, workflow: CollaborationWorkflow) -> Dict:
        """파이프라인 워크플로우 (각 단계의 출력이 다음 단계의 입력)"""
        results = {}
        pipeline_data = {}
        
        for i, step in enumerate(workflow.steps):
            agent_id = workflow.agents[i % len(workflow.agents)]
            
            # 이전 단계의 출력을 입력으로 사용
            step_requirements = {**step.get("requirements", {})}
            if i > 0:
                step_requirements["input_data"] = pipeline_data
            
            task_request = TaskRequest(
                task_id=f"{workflow.workflow_id}_pipeline_{i}",
                requester_id=self.agent.agent_id,
                task_type=step["type"],
                description=step["description"],
                requirements=step_requirements
            )
            
            response = await self.request_collaboration(task_request, [agent_id])
            if response and response[0].status == "completed":
                pipeline_data = response[0].result or {}
                results[f"pipeline_step_{i}"] = pipeline_data
            else:
                raise Exception(f"Pipeline step {i} failed")
        
        return results
    
    async def _find_suitable_agents(self, task: TaskRequest) -> List[str]:
        """작업에 적합한 에이전트 찾기"""
        suitable_agents = []
        
        # 등록된 에이전트들 중에서 검색
        all_agents = await agent_discovery.get_discovery_info()
        
        for agent_id, agent_info in all_agents.get("agents", {}).items():
            if agent_id == self.agent.agent_id:
                continue
                
            capabilities = agent_info.get("capabilities", [])
            
            # 작업 유형과 에이전트 기능 매칭
            if any(cap in task.requirements.get("required_capabilities", []) 
                   for cap in capabilities):
                suitable_agents.append(agent_id)
        
        return suitable_agents
    
    async def _evaluate_task_capability(self, task: TaskRequest) -> bool:
        """작업 수행 능력 평가"""
        required_caps = task.requirements.get("required_capabilities", [])
        
        for cap in required_caps:
            if cap not in self.capabilities:
                return False
            
            min_level = task.requirements.get(f"{cap}_min_level", 1)
            if self.capabilities[cap] < min_level:
                return False
        
        return True
    
    async def get_collaboration_status(self) -> Dict[str, Any]:
        """협업 상태 조회"""
        return {
            "agent_id": self.agent.agent_id,
            "capabilities": self.capabilities,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "active_workflows": len([w for w in self.workflows.values() if w.status == "running"]),
            "collaboration_partners": len(self.collaboration_partners),
            "status": self.agent.status
        }


# 협업 메시지 타입들
COLLABORATION_MESSAGE_TYPES = {
    "collaboration_request": "협업 요청",
    "collaboration_response": "협업 응답", 
    "workflow_invitation": "워크플로우 초대",
    "workflow_status": "워크플로우 상태",
    "task_update": "작업 업데이트",
    "capability_query": "기능 조회",
    "agent_recommendation": "에이전트 추천"
}