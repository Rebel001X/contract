from sqlalchemy import (
    Column, BigInteger, Text, Enum, Boolean, JSON, DateTime, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime

Base = declarative_base()

class ContractAuditReview(Base):
    __tablename__ = 'contract_audit_review'
    __table_args__ = (
        Index('idx_risk_level', 'risk_level'),
        Index('idx_review_status', 'review_status'),
        {'comment': '合同审计-审查记录表'}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    project_name = Column(Text, nullable=False, comment='审查项目（长文本）')
    risk_level = Column(Enum('高', '中', '低', '无'), nullable=False, default='无', comment='风险等级')
    review_status = Column(Enum('通过', '不通过', '待审查'), nullable=False, default='待审查', comment='审查状态')
    reviewer = Column(Text, nullable=True, comment='审查人（长文本）')
    review_comment = Column(Text, nullable=True, comment='审查备注/说明（长文本）')
    is_deleted = Column(Boolean, nullable=False, default=False, comment='是否删除 0-正常 1-已删除')
    ext_json = Column(JSON, nullable=True, comment='扩展字段（可存储额外信息）')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='修改时间')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')

    def __repr__(self):
        return f"<ContractAuditReview(id={self.id}, project_name={self.project_name}, risk_level={self.risk_level})>"

# CRUD functions

def create_contract_audit_review(db: Session, review_data: dict) -> ContractAuditReview:
    review = ContractAuditReview(**review_data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

def get_contract_audit_review(db: Session, review_id: int) -> ContractAuditReview:
    return db.query(ContractAuditReview).filter(ContractAuditReview.id == review_id, ContractAuditReview.is_deleted == False).first()

def list_contract_audit_reviews(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False).offset(skip).limit(limit).all()

def update_contract_audit_review(db: Session, review_id: int, update_data: dict) -> ContractAuditReview:
    review = db.query(ContractAuditReview).filter(ContractAuditReview.id == review_id, ContractAuditReview.is_deleted == False).first()
    if not review:
        return None
    for key, value in update_data.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review

def delete_contract_audit_review(db: Session, review_id: int) -> bool:
    review = db.query(ContractAuditReview).filter(ContractAuditReview.id == review_id, ContractAuditReview.is_deleted == False).first()
    if not review:
        return False
    review.is_deleted = True
    db.commit()
    return True 