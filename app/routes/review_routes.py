"""
부동산 리뷰 및 댓글 시스템 라우트
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

# 간단한 메모리 기반 저장소 (실제로는 DB 사용)
reviews_db = []
comments_db = []

class ReviewCreate(BaseModel):
    property_address: str
    property_type: str
    rating: int  # 1-5점
    title: str
    content: str
    author_name: str
    pros: List[str] = []
    cons: List[str] = []
    living_period: Optional[str] = None  # "6개월", "1년" 등

class CommentCreate(BaseModel):
    review_id: str
    content: str
    author_name: str

class Review(ReviewCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    likes: int = 0
    comments_count: int = 0

class Comment(CommentCreate):
    id: str
    created_at: datetime
    likes: int = 0

@router.post("/", response_model=Review)
async def create_review(review: ReviewCreate):
    """리뷰 작성"""
    new_review = Review(
        **review.dict(),
        id=str(uuid.uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    reviews_db.append(new_review)
    return new_review

@router.get("/", response_model=List[Review])
async def get_reviews(
    property_address: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = 20
):
    """리뷰 목록 조회"""
    filtered_reviews = reviews_db
    
    if property_address:
        filtered_reviews = [r for r in filtered_reviews if property_address.lower() in r.property_address.lower()]
    
    if property_type:
        filtered_reviews = [r for r in filtered_reviews if r.property_type == property_type]
    
    return filtered_reviews[:limit]

@router.get("/{review_id}")
async def get_review(review_id: str):
    """특정 리뷰 상세 조회"""
    review = next((r for r in reviews_db if r.id == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    
    # 해당 리뷰의 댓글들도 함께 반환
    review_comments = [c for c in comments_db if c.review_id == review_id]
    
    return {
        "review": review,
        "comments": review_comments
    }

@router.post("/{review_id}/comments", response_model=Comment)
async def create_comment(review_id: str, comment: CommentCreate):
    """리뷰에 댓글 작성"""
    # 리뷰 존재 확인
    review = next((r for r in reviews_db if r.id == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    
    new_comment = Comment(
        **comment.dict(),
        id=str(uuid.uuid4()),
        created_at=datetime.now()
    )
    comments_db.append(new_comment)
    
    # 리뷰의 댓글 수 증가
    review.comments_count += 1
    
    return new_comment

@router.post("/{review_id}/like")
async def like_review(review_id: str):
    """리뷰 좋아요"""
    review = next((r for r in reviews_db if r.id == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    
    review.likes += 1
    return {"message": "좋아요가 추가되었습니다", "likes": review.likes}

@router.get("/stats/{property_address}")
async def get_review_stats(property_address: str):
    """특정 주소의 리뷰 통계"""
    property_reviews = [r for r in reviews_db if property_address.lower() in r.property_address.lower()]
    
    if not property_reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {}
        }
    
    total = len(property_reviews)
    avg_rating = sum(r.rating for r in property_reviews) / total
    
    rating_dist = {}
    for i in range(1, 6):
        rating_dist[f"{i}점"] = len([r for r in property_reviews if r.rating == i])
    
    return {
        "total_reviews": total,
        "average_rating": round(avg_rating, 1),
        "rating_distribution": rating_dist,
        "recent_reviews": property_reviews[:5]  # 최근 5개
    }