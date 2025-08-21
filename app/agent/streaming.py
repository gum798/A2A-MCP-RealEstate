"""
Server-Sent Events (SSE) Streaming
에이전트 간 실시간 스트리밍 통신 구현
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime
import uuid
from loguru import logger
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class StreamMessage(BaseModel):
    """스트림 메시지 모델"""
    id: str
    event: str
    data: Dict[str, Any]
    timestamp: str
    
class StreamManager:
    """스트림 관리자"""
    
    def __init__(self):
        self.active_streams: Dict[str, asyncio.Queue] = {}
        self.stream_metadata: Dict[str, Dict] = {}
        
    async def create_stream(self, stream_id: Optional[str] = None) -> str:
        """새 스트림 생성"""
        if stream_id is None:
            stream_id = str(uuid.uuid4())
            
        self.active_streams[stream_id] = asyncio.Queue()
        self.stream_metadata[stream_id] = {
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "status": "active"
        }
        
        logger.info(f"Created stream: {stream_id}")
        return stream_id
    
    async def close_stream(self, stream_id: str):
        """스트림 종료"""
        if stream_id in self.active_streams:
            # 종료 메시지 전송
            await self.send_message(stream_id, "stream_close", {"reason": "closed"})
            
            # 스트림 정리
            del self.active_streams[stream_id]
            if stream_id in self.stream_metadata:
                self.stream_metadata[stream_id]["status"] = "closed"
                
            logger.info(f"Closed stream: {stream_id}")
    
    async def send_message(self, stream_id: str, event: str, data: Dict[str, Any]) -> bool:
        """스트림에 메시지 전송"""
        if stream_id not in self.active_streams:
            logger.warning(f"Stream not found: {stream_id}")
            return False
            
        message = StreamMessage(
            id=str(uuid.uuid4()),
            event=event,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            await self.active_streams[stream_id].put(message)
            self.stream_metadata[stream_id]["message_count"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send message to stream {stream_id}: {e}")
            return False
    
    async def get_stream_generator(self, stream_id: str) -> AsyncGenerator[str, None]:
        """스트림 데이터 제너레이터"""
        if stream_id not in self.active_streams:
            yield self._format_sse_message("error", {"message": "Stream not found"})
            return
            
        queue = self.active_streams[stream_id]
        
        # 초기 연결 메시지
        yield self._format_sse_message("connected", {
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            while stream_id in self.active_streams:
                try:
                    # 타임아웃으로 주기적으로 heartbeat 전송
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    if message.event == "stream_close":
                        yield self._format_sse_message("close", message.data)
                        break
                        
                    yield self._format_sse_message(message.event, message.data, message.id)
                    
                except asyncio.TimeoutError:
                    # Heartbeat 메시지
                    yield self._format_sse_message("heartbeat", {
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Stream generator error for {stream_id}: {e}")
            yield self._format_sse_message("error", {"message": str(e)})
        finally:
            # 스트림 정리
            if stream_id in self.active_streams:
                await self.close_stream(stream_id)
    
    def _format_sse_message(self, event: str, data: Dict[str, Any], 
                          message_id: Optional[str] = None) -> str:
        """SSE 메시지 포맷팅"""
        lines = []
        
        if message_id:
            lines.append(f"id: {message_id}")
        
        lines.append(f"event: {event}")
        lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        lines.append("")  # 빈 줄로 메시지 구분
        
        return "\n".join(lines) + "\n"
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict]:
        """스트림 정보 조회"""
        if stream_id in self.stream_metadata:
            return {
                **self.stream_metadata[stream_id],
                "is_active": stream_id in self.active_streams
            }
        return None
    
    def get_all_streams_info(self) -> Dict[str, Any]:
        """모든 스트림 정보 조회"""
        return {
            "total_streams": len(self.stream_metadata),
            "active_streams": len(self.active_streams),
            "streams": {
                stream_id: self.get_stream_info(stream_id)
                for stream_id in self.stream_metadata
            }
        }

# 글로벌 스트림 매니저
stream_manager = StreamManager()

# 스트림 응답 생성 헬퍼 함수
async def create_stream_response(stream_id: str, request: Request) -> StreamingResponse:
    """스트림 응답 생성"""
    
    async def event_generator():
        """이벤트 제너레이터"""
        try:
            async for data in stream_manager.get_stream_generator(stream_id):
                # 클라이언트 연결 상태 확인
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from stream {stream_id}")
                    break
                yield data
        except Exception as e:
            logger.error(f"Stream response error: {e}")
        finally:
            await stream_manager.close_stream(stream_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# 부동산 분석 스트리밍 함수들
async def stream_real_estate_analysis(stream_id: str, property_data: Dict[str, Any]):
    """부동산 분석 스트리밍"""
    
    # 분석 시작 알림
    await stream_manager.send_message(stream_id, "analysis_start", {
        "message": "부동산 분석을 시작합니다.",
        "property": property_data.get("address", "unknown")
    })
    
    # 단계별 분석 진행
    analysis_steps = [
        ("price_analysis", "가격 분석 중...", {"progress": 20}),
        ("location_analysis", "위치 분석 중...", {"progress": 40}),
        ("transport_analysis", "교통 분석 중...", {"progress": 60}),
        ("facility_analysis", "편의시설 분석 중...", {"progress": 80}),
        ("final_analysis", "종합 분석 완료", {"progress": 100})
    ]
    
    for step, message, data in analysis_steps:
        await asyncio.sleep(1)  # 실제 분석 시뮬레이션
        await stream_manager.send_message(stream_id, step, {
            "message": message,
            **data
        })
    
    # 최종 결과 전송
    final_result = {
        "investment_score": 85.0,
        "life_quality_score": 72.0,
        "recommendation": "추천",
        "analysis_complete": True
    }
    
    await stream_manager.send_message(stream_id, "analysis_complete", final_result)

async def stream_market_data(stream_id: str, location: str):
    """시장 데이터 스트리밍"""
    
    # 실시간 시장 데이터 시뮬레이션
    for i in range(10):
        market_data = {
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "avg_price": 50000 + (i * 100),
            "transaction_count": 15 + i,
            "price_trend": "상승" if i % 2 == 0 else "보합"
        }
        
        await stream_manager.send_message(stream_id, "market_update", market_data)
        await asyncio.sleep(2)  # 2초 간격으로 업데이트