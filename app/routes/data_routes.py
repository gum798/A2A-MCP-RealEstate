"""
데이터 API 라우트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.data.sample_data import sample_data
from app.utils.logger import logger

router = APIRouter()


class GenerateDataRequest(BaseModel):
    count: Optional[int] = 5


@router.get("/")
async def data_info():
    """데이터 API 정보"""
    return {
        "message": "Sample data endpoints",
        "available_types": ["users", "orders", "products", "system", "metrics"],
        "endpoints": [
            "/api/data/users",
            "/api/data/orders", 
            "/api/data/products",
            "/api/data/system",
            "/api/data/metrics",
            "/api/data/type/{data_type}",
            "/api/data/generate/{data_type}"
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/users")
async def get_users():
    """사용자 데이터 조회"""
    return {
        "type": "user_data",
        "data": sample_data.get_users(),
        "count": len(sample_data.get_users()),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/orders")
async def get_orders():
    """주문 데이터 조회"""
    return {
        "type": "order_data",
        "data": sample_data.get_orders(),
        "count": len(sample_data.get_orders()),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/products")
async def get_products():
    """상품 데이터 조회"""
    return {
        "type": "product_data",
        "data": sample_data.get_products(),
        "count": len(sample_data.get_products()),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/system")
async def get_system_status():
    """시스템 상태 데이터 조회"""
    return {
        "type": "system_data",
        "data": sample_data.get_system_status(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/metrics")
async def get_metrics():
    """메트릭 데이터 조회"""
    return {
        "type": "metrics_data",
        "data": sample_data.get_metrics(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/type/{data_type}")
async def get_data_by_type(data_type: str):
    """특정 타입 데이터 조회"""
    data_methods = {
        "users": sample_data.get_users,
        "orders": sample_data.get_orders,
        "products": sample_data.get_products,
        "system": sample_data.get_system_status,
        "metrics": sample_data.get_metrics
    }
    
    if data_type not in data_methods:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Data type not found",
                "available_types": list(data_methods.keys())
            }
        )
    
    data = data_methods[data_type]()
    return {
        "type": data_type,
        "data": data,
        "count": len(data) if isinstance(data, list) else 1,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/generate/{data_type}")
async def generate_sample_data(data_type: str, request: GenerateDataRequest):
    """샘플 데이터 생성"""
    try:
        generated_data = sample_data.generate_dynamic_data(data_type, request.count)
        
        if not generated_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid data type for generation",
                    "supported_types": ["users", "orders", "products"]
                }
            )
        
        return {
            "type": data_type,
            "count": len(generated_data),
            "data": generated_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Data generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data generation failed: {str(e)}"
        )


@router.get("/random/{data_type}")
async def get_random_data(data_type: str, count: Optional[int] = 3):
    """랜덤 데이터 조회"""
    import random
    
    data_methods = {
        "users": sample_data.get_users,
        "orders": sample_data.get_orders,
        "products": sample_data.get_products
    }
    
    if data_type not in data_methods:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Data type not found",
                "available_types": list(data_methods.keys())
            }
        )
    
    all_data = data_methods[data_type]()
    random_data = random.sample(all_data, min(count, len(all_data)))
    
    return {
        "type": f"random_{data_type}",
        "requested_count": count,
        "actual_count": len(random_data),
        "data": random_data,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_data_stats():
    """데이터 통계"""
    return {
        "statistics": {
            "users": len(sample_data.get_users()),
            "orders": len(sample_data.get_orders()),
            "products": len(sample_data.get_products()),
            "system_services": len(sample_data.get_system_status()["services"]),
            "total_data_points": (
                len(sample_data.get_users()) + 
                len(sample_data.get_orders()) + 
                len(sample_data.get_products())
            )
        },
        "timestamp": datetime.now().isoformat()
    }