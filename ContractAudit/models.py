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

# 新增：Confirm接口审查结果相关表

class ConfirmReviewSession(Base):
    """Confirm接口审查会话表"""
    __tablename__ = 'confirm_review_session'
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_created_at', 'created_at'),
        {'comment': 'Confirm接口审查会话表'}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(255), nullable=False, comment='会话ID')
    user_id = Column(String(255), nullable=True, comment='用户ID')
    project_name = Column(String(500), nullable=True, comment='项目名称')
    review_stage = Column(String(100), nullable=True, comment='审查阶段')
    review_rules_count = Column(Integer, nullable=False, default=0, comment='审查规则数量')
    
    # 综合统计信息
    total_issues = Column(Integer, nullable=False, default=0, comment='总问题数')
    high_risk_items = Column(Integer, nullable=False, default=0, comment='高风险项数')
    medium_risk_items = Column(Integer, nullable=False, default=0, comment='中风险项数')
    low_risk_items = Column(Integer, nullable=False, default=0, comment='低风险项数')
    overall_risk_level = Column(String(50), nullable=False, default='medium', comment='整体风险等级')
    overall_summary = Column(Text, nullable=True, comment='整体总结')
    confidence_score = Column(Integer, nullable=False, default=80, comment='置信度分数(0-100)')
    
    # 建议和行动项
    critical_recommendations = Column(JSON, nullable=True, comment='关键建议列表')
    action_items = Column(JSON, nullable=True, comment='行动项列表')
    
    # 处理信息
    processing_time = Column(Integer, nullable=False, default=0, comment='处理时间(秒)')
    model_used = Column(String(100), nullable=False, default='rule_based_review', comment='使用的模型')
    
    # 状态信息
    status = Column(String(50), nullable=False, default='completed', comment='处理状态')
    error_message = Column(Text, nullable=True, comment='错误信息')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __repr__(self):
        return f"<ConfirmReviewSession(id={self.id}, session_id={self.session_id}, project_name={self.project_name})>"

class ConfirmReviewRuleResult(Base):
    """Confirm接口单个规则审查结果表"""
    __tablename__ = 'confirm_review_rule_result'
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_rule_id', 'rule_id'),
        Index('idx_review_result', 'review_result'),
        Index('idx_risk_level', 'risk_level'),
        {'comment': 'Confirm接口单个规则审查结果表'}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(255), nullable=False, comment='会话ID')
    rule_id = Column(Integer, nullable=False, comment='规则ID')
    rule_name = Column(String(500), nullable=False, comment='规则名称')
    rule_index = Column(Integer, nullable=False, comment='规则索引')
    
    # 审查结果
    review_result = Column(String(50), nullable=False, comment='审查结果(通过/不通过)')
    risk_level = Column(String(50), nullable=False, comment='风险等级(high/medium/low/none)')
    matched_content = Column(Text, nullable=True, comment='匹配到的合同内容片段')
    analysis = Column(Text, nullable=True, comment='详细的分析说明')
    
    # 问题和建议
    issues = Column(JSON, nullable=True, comment='具体问题列表')
    suggestions = Column(JSON, nullable=True, comment='具体建议列表')
    
    # 置信度
    confidence_score = Column(Integer, nullable=False, default=50, comment='置信度分数(0-100)')
    
    # 用户反馈 (0=点踩, 1=点赞, null=无反馈)
    user_feedback = Column(Integer, nullable=True, comment='用户反馈(0=点踩, 1=点赞, null=无反馈)')
    
    # 新增字段：反馈建议和审核状态
    feedback_suggestion = Column(Text, nullable=True, comment='反馈建议内容')
    is_approved = Column(Boolean, nullable=True, comment='审核是否通过标志')
    contract_id = Column(String(255), nullable=True, comment='合同ID')
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')

    def __repr__(self):
        return f"<ConfirmReviewRuleResult(id={self.id}, session_id={self.session_id}, rule_name={self.rule_name})>"

# Confirm接口相关的CRUD函数

def create_confirm_review_session(db: Session, session_data: dict) -> ConfirmReviewSession:
    """创建Confirm审查会话"""
    session = ConfirmReviewSession(**session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_confirm_review_session(db: Session, session_id: str) -> ConfirmReviewSession:
    """根据会话ID获取Confirm审查会话"""
    return db.query(ConfirmReviewSession).filter(ConfirmReviewSession.session_id == session_id).first()

def list_confirm_review_sessions(db: Session, user_id: str = None, skip: int = 0, limit: int = 100):
    """列出Confirm审查会话"""
    query = db.query(ConfirmReviewSession)
    if user_id:
        query = query.filter(ConfirmReviewSession.user_id == user_id)
    return query.order_by(ConfirmReviewSession.created_at.desc()).offset(skip).limit(limit).all()

def update_confirm_review_session(db: Session, session_id: str, update_data: dict) -> ConfirmReviewSession:
    """更新Confirm审查会话"""
    session = db.query(ConfirmReviewSession).filter(ConfirmReviewSession.session_id == session_id).first()
    if not session:
        return None
    for key, value in update_data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session

def create_confirm_review_rule_result(db: Session, result_data: dict) -> ConfirmReviewRuleResult:
    """创建单个规则审查结果"""
    result = ConfirmReviewRuleResult(**result_data)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def bulk_create_confirm_review_rule_results(db: Session, results_data: list) -> list:
    """批量创建规则审查结果"""
    print(f"[DEBUG] bulk_create_confirm_review_rule_results 开始，数据条数: {len(results_data)}")
    print(f"[DEBUG] 输入数据: {results_data}")
    
    try:
        results = []
        for i, result_data in enumerate(results_data):
            print(f"[DEBUG] 处理第 {i+1} 条数据: {result_data}")
            result = ConfirmReviewRuleResult(**result_data)
            results.append(result)
        
        print(f"[DEBUG] 准备添加到数据库，对象数量: {len(results)}")
        db.add_all(results)
        print(f"[DEBUG] 执行 commit...")
        db.commit()
        print(f"[DEBUG] commit 成功")
        
        # 刷新所有对象以获取ID
        created_ids = []
        for result in results:
            db.refresh(result)
            created_ids.append(result.id)
            print(f"[DEBUG] 刷新对象，ID: {result.id}, session_id: {result.session_id}, rule_name: {result.rule_name}")
        
        print(f"[DEBUG] bulk_create_confirm_review_rule_results 完成，创建的ID列表: {created_ids}")
        return results
        
    except Exception as e:
        print(f"[ERROR] bulk_create_confirm_review_rule_results 异常: {e}")
        import traceback
        print(f"[ERROR] 异常详情: {traceback.format_exc()}")
        db.rollback()
        raise

def get_confirm_review_rule_results(db: Session, session_id: str):
    """获取指定会话的所有规则审查结果"""
    return db.query(ConfirmReviewRuleResult).filter(
        ConfirmReviewRuleResult.session_id == session_id
    ).order_by(ConfirmReviewRuleResult.rule_index).all()

def get_confirm_review_statistics(db: Session, user_id: str = None):
    """获取Confirm审查统计信息"""
    query = db.query(ConfirmReviewSession)
    if user_id:
        query = query.filter(ConfirmReviewSession.user_id == user_id)
    
    total_sessions = query.count()
    total_issues = query.with_entities(db.func.sum(ConfirmReviewSession.total_issues)).scalar() or 0
    high_risk_sessions = query.filter(ConfirmReviewSession.overall_risk_level == 'high').count()
    medium_risk_sessions = query.filter(ConfirmReviewSession.overall_risk_level == 'medium').count()
    low_risk_sessions = query.filter(ConfirmReviewSession.overall_risk_level == 'low').count()
    
    return {
        'total_sessions': total_sessions,
        'total_issues': total_issues,
        'high_risk_sessions': high_risk_sessions,
        'medium_risk_sessions': medium_risk_sessions,
        'low_risk_sessions': low_risk_sessions
    } 