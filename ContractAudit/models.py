from sqlalchemy import (
    Column, BigInteger, Text, Enum, Boolean, JSON, DateTime, Index, Integer, String
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

class ReviewRule(Base):
    __tablename__ = 'review_rule'
    __table_args__ = (
        Index('idx_rule_name', 'rule_name'),
        Index('idx_risk_level', 'risk_level'),
        Index('idx_rule_group_id', 'rule_group_id'),
        {'comment': '审查规则表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='id')
    rule_name = Column(String(255), nullable=False, comment='规则名称')
    type = Column(Integer, nullable=False, comment='规则类型，0-预设，1-自定义')
    risk_level = Column(Integer, nullable=False, comment='风险等级，0-低风险，1-中风险，2-高风险')
    risk_attribution_id = Column(Integer, nullable=True, comment='风险归属id')
    risk_attribution_name = Column(String(255), nullable=True, comment='风险归属名')
    censored_search_engine = Column(Integer, nullable=False, comment='审查引擎，0-大模型 1-规则推理')
    rule_group_id = Column(Integer, nullable=True, comment='规则分组id')
    rule_group_name = Column(String(255), nullable=True, comment='规则分组名')
    include_rule = Column(Text, nullable=True, comment='包含规则')
    logic_rule_list = Column(JSON, nullable=True, comment='逻辑规则列表')
    example_list = Column(JSON, nullable=True, comment='例子列表')
    conditional_identifier = Column(String(255), nullable=True, comment='条件判断符')
    condition_list = Column(JSON, nullable=True, comment='条件列表')
    revise_opinion = Column(Text, nullable=True, comment='修改意见')
    creator_id = Column(Integer, nullable=True, comment='创建者id')
    creator_name = Column(String(255), nullable=True, comment='创建者姓名')
    version = Column(Integer, nullable=False, default=1, comment='版本号')
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __repr__(self):
        return f"<ReviewRule(id={self.id}, rule_name={self.rule_name}, risk_level={self.risk_level})>"

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

# ReviewRule CRUD functions
def create_review_rule(db: Session, rule_data: dict) -> ReviewRule:
    rule = ReviewRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

def get_review_rule(db: Session, rule_id: int) -> ReviewRule:
    return db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()

def list_review_rules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ReviewRule).offset(skip).limit(limit).all()

def update_review_rule(db: Session, rule_id: int, update_data: dict) -> ReviewRule:
    rule = db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()
    if not rule:
        return None
    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule

def delete_review_rule(db: Session, rule_id: int) -> bool:
    rule = db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()
    if not rule:
        return False
    db.delete(rule)
    db.commit()
    return True

def bulk_create_review_rules(db: Session, rules_data: list) -> list:
    """批量创建审查规则"""
    rules = []
    for rule_data in rules_data:
        rule = ReviewRule(**rule_data)
        rules.append(rule)
    
    db.add_all(rules)
    db.commit()
    
    # 刷新所有对象以获取ID
    for rule in rules:
        db.refresh(rule)
    
    return rules

def get_review_rule_by_external_id(db: Session, external_id: int) -> ReviewRule:
    """根据外部ID获取审查规则（用于避免重复插入）"""
    return db.query(ReviewRule).filter(ReviewRule.id == external_id).first() 