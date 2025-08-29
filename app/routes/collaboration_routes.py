"""
Agent Collaboration Routes
에이전트 간 협업을 위한 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agent.collaboration import (
    CollaborativeAgent, TaskRequest, TaskResponse, 
    CollaborationWorkflow, COLLABORATION_MESSAGE_TYPES
)
from app.agent.a2a_agent import A2AAgent
from app.utils.config import settings
from app.utils.logger import logger

router = APIRouter()

# 글로벌 협업 에이전트
base_agent = A2AAgent(settings.agent_id, settings.agent_name)
collaborative_agent = CollaborativeAgent(base_agent)


class CapabilityRegistration(BaseModel):
    capability: str
    skill_level: int


class CollaborationRequest(BaseModel):
    task_type: str
    description: str
    requirements: Dict[str, Any]
    target_agents: Optional[List[str]] = None
    priority: int = 1
    deadline: Optional[datetime] = None


class WorkflowRequest(BaseModel):
    name: str
    description: str
    agents: List[str]
    steps: List[Dict[str, Any]]
    collaboration_type: str = "sequential"


@router.post("/capabilities/register")
async def register_capability(capability_data: CapabilityRegistration):
    """에이전트 기능 등록"""
    try:
        await collaborative_agent.register_capability(
            capability_data.capability,
            capability_data.skill_level
        )
        
        return {
            "status": "registered",
            "capability": capability_data.capability,
            "skill_level": capability_data.skill_level,
            "agent_id": collaborative_agent.agent.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to register capability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities():
    """등록된 기능 목록 조회"""
    return {
        "agent_id": collaborative_agent.agent.agent_id,
        "capabilities": collaborative_agent.capabilities,
        "total_capabilities": len(collaborative_agent.capabilities),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/request")
async def request_collaboration(request_data: CollaborationRequest):
    """다른 에이전트에게 협업 요청"""
    try:
        task = TaskRequest(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{collaborative_agent.agent.agent_id[-4:]}",
            requester_id=collaborative_agent.agent.agent_id,
            task_type=request_data.task_type,
            description=request_data.description,
            requirements=request_data.requirements,
            priority=request_data.priority,
            deadline=request_data.deadline
        )
        
        responses = await collaborative_agent.request_collaboration(
            task, request_data.target_agents
        )
        
        return {
            "task_id": task.task_id,
            "status": "sent",
            "responses": [response.model_dump() for response in responses],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Collaboration request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond/{task_id}")
async def respond_to_collaboration(task_id: str, response_data: Dict[str, Any]):
    """협업 요청에 응답"""
    try:
        if task_id not in collaborative_agent.active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = collaborative_agent.active_tasks[task_id]
        
        # 작업 실행 (실제 구현에서는 더 복잡한 로직 필요)
        result = await _execute_task(task, response_data)
        
        response = TaskResponse(
            task_id=task_id,
            agent_id=collaborative_agent.agent.agent_id,
            status="completed",
            result=result,
            completion_time=datetime.now()
        )
        
        # 완료된 작업을 기록
        collaborative_agent.completed_tasks[task_id] = response
        del collaborative_agent.active_tasks[task_id]
        
        return response.model_dump()
        
    except Exception as e:
        logger.error(f"Failed to respond to collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow/create")
async def create_workflow(workflow_request: WorkflowRequest):
    """협업 워크플로우 생성"""
    try:
        workflow = CollaborationWorkflow(
            workflow_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=workflow_request.name,
            description=workflow_request.description,
            agents=workflow_request.agents,
            steps=workflow_request.steps
        )
        
        success = await collaborative_agent.create_workflow(workflow)
        
        if success:
            return {
                "workflow_id": workflow.workflow_id,
                "status": "created",
                "participants": len(workflow.agents),
                "steps": len(workflow.steps),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create workflow")
            
    except Exception as e:
        logger.error(f"Workflow creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    """워크플로우 실행"""
    try:
        results = await collaborative_agent.execute_workflow(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": "executed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """워크플로우 상태 조회"""
    try:
        if workflow_id not in collaborative_agent.workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = collaborative_agent.workflows[workflow_id]
        return workflow.model_dump()
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows():
    """모든 워크플로우 목록 조회"""
    return {
        "agent_id": collaborative_agent.agent.agent_id,
        "workflows": [workflow.model_dump() for workflow in collaborative_agent.workflows.values()],
        "total_workflows": len(collaborative_agent.workflows),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/tasks/active")
async def get_active_tasks():
    """진행 중인 작업 목록"""
    return {
        "agent_id": collaborative_agent.agent.agent_id,
        "active_tasks": [task.model_dump() for task in collaborative_agent.active_tasks.values()],
        "count": len(collaborative_agent.active_tasks),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/tasks/completed")
async def get_completed_tasks():
    """완료된 작업 목록"""
    return {
        "agent_id": collaborative_agent.agent.agent_id,
        "completed_tasks": [task.model_dump() for task in collaborative_agent.completed_tasks.values()],
        "count": len(collaborative_agent.completed_tasks),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status")
async def get_collaboration_status():
    """전체 협업 상태 조회"""
    try:
        status = await collaborative_agent.get_collaboration_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get collaboration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/message-types")
async def get_message_types():
    """지원하는 협업 메시지 유형 목록"""
    return {
        "message_types": COLLABORATION_MESSAGE_TYPES,
        "count": len(COLLABORATION_MESSAGE_TYPES),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/partners/add")
async def add_collaboration_partner(partner_data: Dict[str, Any]):
    """협업 파트너 추가"""
    try:
        agent_id = partner_data.get("agent_id")
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
        
        collaborative_agent.collaboration_partners[agent_id] = {
            **partner_data,
            "added_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        return {
            "status": "added",
            "partner_id": agent_id,
            "total_partners": len(collaborative_agent.collaboration_partners),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to add collaboration partner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners")
async def list_collaboration_partners():
    """협업 파트너 목록"""
    return {
        "agent_id": collaborative_agent.agent.agent_id,
        "partners": collaborative_agent.collaboration_partners,
        "count": len(collaborative_agent.collaboration_partners),
        "timestamp": datetime.now().isoformat()
    }


async def _execute_task(task: TaskRequest, execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """작업 실행 (예제 구현)"""
    # 실제 구현에서는 task_type에 따라 다른 로직 실행
    task_type = task.task_type
    
    if task_type == "data_analysis":
        return {"analysis_result": "Data analyzed successfully", "data": execution_data.get("data", {})}
    elif task_type == "data_processing":
        return {"processed_data": execution_data.get("input_data", {}), "processing_time": "0.5s"}
    elif task_type == "recommendation":
        return {"recommendations": ["option1", "option2", "option3"], "confidence": 0.85}
    else:
        return {"message": f"Task {task_type} executed", "input": execution_data}