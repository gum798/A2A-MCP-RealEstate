"""
샘플 데이터 모듈
"""
from datetime import datetime
from typing import Dict, List, Any
import random


class SampleDataGenerator:
    """샘플 데이터 생성기"""
    
    @staticmethod
    def get_users() -> List[Dict]:
        """사용자 데이터"""
        return [
            {
                "id": 1,
                "name": "김철수",
                "email": "kim.chulsoo@example.com",
                "role": "admin",
                "department": "IT",
                "created_at": "2024-01-15T09:00:00Z",
                "is_active": True
            },
            {
                "id": 2,
                "name": "이영희",
                "email": "lee.younghee@example.com",
                "role": "user",
                "department": "Sales",
                "created_at": "2024-02-10T14:30:00Z",
                "is_active": True
            },
            {
                "id": 3,
                "name": "박민수",
                "email": "park.minsoo@example.com",
                "role": "manager",
                "department": "Marketing",
                "created_at": "2024-01-20T11:15:00Z",
                "is_active": False
            },
            {
                "id": 4,
                "name": "정수연",
                "email": "jung.suyeon@example.com",
                "role": "user",
                "department": "HR",
                "created_at": "2024-03-05T16:45:00Z",
                "is_active": True
            }
        ]
    
    @staticmethod
    def get_orders() -> List[Dict]:
        """주문 데이터"""
        return [
            {
                "order_id": "ORD-2024-001",
                "customer_id": 1,
                "customer_name": "김철수",
                "items": [
                    {"product_id": 101, "product_name": "노트북", "quantity": 1, "price": 1500000},
                    {"product_id": 102, "product_name": "마우스", "quantity": 2, "price": 25000}
                ],
                "total_amount": 1550000,
                "status": "completed",
                "order_date": "2024-06-01T10:30:00Z",
                "delivery_date": "2024-06-03T14:00:00Z"
            },
            {
                "order_id": "ORD-2024-002",
                "customer_id": 2,
                "customer_name": "이영희",
                "items": [
                    {"product_id": 103, "product_name": "키보드", "quantity": 1, "price": 150000},
                    {"product_id": 104, "product_name": "모니터", "quantity": 1, "price": 300000}
                ],
                "total_amount": 450000,
                "status": "pending",
                "order_date": "2024-06-15T15:20:00Z",
                "delivery_date": None
            },
            {
                "order_id": "ORD-2024-003",
                "customer_id": 4,
                "customer_name": "정수연",
                "items": [
                    {"product_id": 105, "product_name": "태블릿", "quantity": 1, "price": 800000}
                ],
                "total_amount": 800000,
                "status": "shipped",
                "order_date": "2024-06-20T09:15:00Z",
                "delivery_date": "2024-06-22T16:30:00Z"
            }
        ]
    
    @staticmethod
    def get_products() -> List[Dict]:
        """상품 데이터"""
        return [
            {
                "id": 101,
                "name": "울트라북 Pro",
                "category": "전자제품",
                "price": 1500000,
                "stock": 15,
                "description": "고성능 울트라북",
                "specifications": {
                    "cpu": "Intel i7",
                    "memory": "16GB",
                    "storage": "512GB SSD",
                    "display": "14인치 FHD"
                },
                "created_at": "2024-01-10T08:00:00Z"
            },
            {
                "id": 102,
                "name": "무선 마우스",
                "category": "액세서리",
                "price": 25000,
                "stock": 50,
                "description": "인체공학적 무선 마우스",
                "specifications": {
                    "connectivity": "Bluetooth 5.0",
                    "battery": "충전식",
                    "sensor": "광학식"
                },
                "created_at": "2024-01-12T10:30:00Z"
            },
            {
                "id": 103,
                "name": "기계식 키보드",
                "category": "액세서리",
                "price": 150000,
                "stock": 25,
                "description": "RGB 백라이트 기계식 키보드",
                "specifications": {
                    "switch": "체리 MX 브라운",
                    "layout": "한영 104키",
                    "backlight": "RGB"
                },
                "created_at": "2024-01-15T14:20:00Z"
            },
            {
                "id": 104,
                "name": "4K 모니터",
                "category": "전자제품",
                "price": 300000,
                "stock": 8,
                "description": "27인치 4K UHD 모니터",
                "specifications": {
                    "size": "27인치",
                    "resolution": "3840x2160",
                    "refresh_rate": "60Hz",
                    "panel": "IPS"
                },
                "created_at": "2024-02-01T11:45:00Z"
            },
            {
                "id": 105,
                "name": "프리미엄 태블릿",
                "category": "전자제품",
                "price": 800000,
                "stock": 12,
                "description": "10인치 프리미엄 태블릿",
                "specifications": {
                    "display": "10.5인치 OLED",
                    "storage": "256GB",
                    "memory": "8GB",
                    "os": "Android 14"
                },
                "created_at": "2024-02-15T09:30:00Z"
            }
        ]
    
    @staticmethod
    def get_system_status() -> Dict:
        """시스템 상태 데이터"""
        return {
            "server": {
                "name": "A2A_Python_Agent_Server",
                "status": "running",
                "uptime": "3 days, 8 hours",
                "cpu": {
                    "usage": "35%",
                    "cores": 8,
                    "load": [0.8, 1.2, 1.5]
                },
                "memory": {
                    "total": "16GB",
                    "used": "8GB",
                    "free": "8GB",
                    "usage": "50%"
                },
                "disk": {
                    "total": "500GB",
                    "used": "120GB",
                    "free": "380GB",
                    "usage": "24%"
                }
            },
            "database": {
                "status": "connected",
                "type": "PostgreSQL",
                "version": "15.4",
                "connections": {
                    "active": 8,
                    "idle": 12,
                    "max": 100
                },
                "performance": {
                    "queries_per_second": 95,
                    "avg_response_time": "8ms"
                }
            },
            "network": {
                "status": "connected",
                "latency": "5ms",
                "bandwidth": {
                    "download": "1Gbps",
                    "upload": "1Gbps"
                },
                "packets": {
                    "sent": 987654,
                    "received": 976543,
                    "lost": 0.05
                }
            },
            "services": [
                {"name": "FastAPI", "status": "running", "port": 8000},
                {"name": "Database", "status": "running", "port": 5432},
                {"name": "Redis", "status": "running", "port": 6379},
                {"name": "Message_Queue", "status": "running", "port": 5672}
            ],
            "last_update": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_metrics() -> Dict:
        """메트릭 데이터"""
        return {
            "requests": {
                "total": 8945,
                "success": 8756,
                "failed": 189,
                "rate": "85 req/min"
            },
            "response_times": {
                "avg": "28ms",
                "p50": "22ms",
                "p95": "65ms",
                "p99": "95ms"
            },
            "errors": [
                {"type": "timeout", "count": 23, "last_occurrence": "2024-07-02T17:30:00Z"},
                {"type": "connection_refused", "count": 8, "last_occurrence": "2024-07-02T16:45:00Z"},
                {"type": "invalid_request", "count": 5, "last_occurrence": "2024-07-02T17:20:00Z"}
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_dynamic_data(data_type: str, count: int = 5) -> List[Dict]:
        """동적 데이터 생성"""
        if data_type == "users":
            return [
                {
                    "id": i + 100,
                    "name": f"생성된 사용자 {i + 1}",
                    "email": f"user{i + 1}@generated.com",
                    "created_at": datetime.now().isoformat()
                }
                for i in range(count)
            ]
        elif data_type == "orders":
            return [
                {
                    "order_id": f"GEN{str(i + 1).zfill(3)}",
                    "amount": round(random.uniform(10, 1000) * 100) / 100,
                    "status": random.choice(["pending", "completed", "cancelled"]),
                    "created_at": datetime.now().isoformat()
                }
                for i in range(count)
            ]
        elif data_type == "products":
            categories = ["전자제품", "의류", "도서", "생활용품"]
            return [
                {
                    "id": i + 1000,
                    "name": f"생성된 상품 {i + 1}",
                    "price": round(random.uniform(10, 500) * 100) / 100,
                    "category": random.choice(categories),
                    "stock": random.randint(0, 100)
                }
                for i in range(count)
            ]
        else:
            return []


# 샘플 데이터 인스턴스
sample_data = SampleDataGenerator()