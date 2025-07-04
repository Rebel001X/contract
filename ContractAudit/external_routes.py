from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .models import (
    ContractAuditReview,
    create_contract_audit_review,
    get_contract_audit_review,
    list_contract_audit_reviews,
    update_contract_audit_review,
    delete_contract_audit_review
)
from .config import get_session
import requests
import os

router = APIRouter()

# Pydantic Schemas
class ContractAuditReviewBase(BaseModel):
    project_name: str
    risk_level: str = Field(default="无")
    review_status: str = Field(default="待审查")
    reviewer: Optional[str] = None
    review_comment: Optional[str] = None
    ext_json: Optional[dict] = None

class ContractAuditReviewCreate(ContractAuditReviewBase):
    pass

class ContractAuditReviewUpdate(BaseModel):
    project_name: Optional[str] = None
    risk_level: Optional[str] = None
    review_status: Optional[str] = None
    reviewer: Optional[str] = None
    review_comment: Optional[str] = None
    ext_json: Optional[dict] = None

class ContractAuditReviewOut(ContractAuditReviewBase):
    id: int
    is_deleted: bool
    updated_at: str
    created_at: str

    class Config:
        orm_mode = True

class PaginatedContractAuditReview(BaseModel):
    total: int
    items: List[ContractAuditReviewOut]

# CRUD 路由
@router.post("/contract-audit-reviews", response_model=ContractAuditReviewOut)
def create_review(review: ContractAuditReviewCreate, db: Session = Depends(get_session)):
    obj = create_contract_audit_review(db, review.dict())
    return obj



@router.get("/contract-audit-reviews/{review_id}", response_model=ContractAuditReviewOut)
def get_review(review_id: int, db: Session = Depends(get_session)):
    obj = get_contract_audit_review(db, review_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Review not found")
    return obj

@router.get("/contract-audit-reviews", response_model=List[ContractAuditReviewOut])
def list_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    return list_contract_audit_reviews(db, skip=skip, limit=limit)

@router.put("/contract-audit-reviews/{review_id}", response_model=ContractAuditReviewOut)
def update_review(review_id: int, review: ContractAuditReviewUpdate, db: Session = Depends(get_session)):
    obj = update_contract_audit_review(db, review_id, review.dict(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Review not found")
    return obj

@router.delete("/contract-audit-reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_session)):
    success = delete_contract_audit_review(db, review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted"}

@router.post("/external/upload")
async def upload_local_docx():
    """
    直接读取 D:\abc.docx 文件并转发到外部服务 http://localhost:9621/documents/upload
    """
    file_path = r"D:\abc.docx"
    try:
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        files = {
            "file": (filename, file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }
        resp = requests.post("http://localhost:9621/documents/upload", files=files)
        resp.raise_for_status()
        print("外部服务返回:", resp.text)  # 打印返回内容到终端
        return resp.json()
    except Exception as e:
        print("外部服务调用异常:", e)
        raise HTTPException(status_code=500, detail=f"外部服务调用失败: {str(e)}")

@router.get("/contract-audit-reviews/page", response_model=PaginatedContractAuditReview)
def paginated_reviews(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_session)
):
    skip = (page - 1) * page_size
    total = db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False).count()
    items = db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False).order_by(ContractAuditReview.updated_at.desc()).offset(skip).limit(page_size).all()
    return PaginatedContractAuditReview(total=total, items=items)

if __name__ == "__main__":
    # 直接运行时，同步调用 upload_local_docx 并输出结果
    import asyncio
    try:
        result = asyncio.run(upload_local_docx())
        print("最终返回:", result)
    except Exception as e:
        print("主程序异常:", e) 