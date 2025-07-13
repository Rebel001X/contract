"""
合同审查结构化数据模型
支持四种审查类型：合同主体审查、付款条款审查、违约条款审查、通用审查
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class ReviewStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEED_REVIEW = "need_review"

# 合同主体审查模型
class SubjectReviewItem(BaseModel):
    """合同主体审查项目"""
    subject_type: str = Field(..., description="主体类型（如：公司、个人、政府机构等）")
    subject_name: str = Field(..., description="主体名称")
    qualification_check: str = Field(..., description="资质检查结果")
    legal_status: str = Field(..., description="法律地位")
    risk_level: RiskLevel = Field(..., description="风险等级")
    issues: List[str] = Field(..., description="发现的问题")
    suggestions: List[str] = Field(..., description="改进建议")

class ContractSubjectReview(BaseModel):
    """合同主体审查结果"""
    overall_risk_level: RiskLevel = Field(..., description="整体风险等级")
    subject_items: List[SubjectReviewItem] = Field(..., description="主体审查项目")
    summary: str = Field(..., description="主体审查总结")
    recommendations: List[str] = Field(..., description="主体相关建议")

# 付款条款审查模型
class PaymentClauseItem(BaseModel):
    """付款条款审查项目"""
    clause_name: str = Field(..., description="条款名称")
    clause_content: str = Field(..., description="条款内容")
    payment_method: str = Field(..., description="付款方式")
    payment_schedule: str = Field(..., description="付款时间安排")
    amount: str = Field(..., description="付款金额")
    risk_level: RiskLevel = Field(..., description="风险等级")
    issues: List[str] = Field(..., description="发现的问题")
    suggestions: List[str] = Field(..., description="改进建议")

class PaymentClauseReview(BaseModel):
    """付款条款审查结果"""
    overall_risk_level: RiskLevel = Field(..., description="整体风险等级")
    payment_clauses: List[PaymentClauseItem] = Field(..., description="付款条款审查项目")
    total_amount: str = Field(..., description="总付款金额")
    payment_schedule_analysis: str = Field(..., description="付款时间安排分析")
    summary: str = Field(..., description="付款条款审查总结")
    recommendations: List[str] = Field(..., description="付款相关建议")

# 违约条款审查模型
class BreachClauseItem(BaseModel):
    """违约条款审查项目"""
    clause_name: str = Field(..., description="条款名称")
    clause_content: str = Field(..., description="条款内容")
    breach_type: str = Field(..., description="违约类型")
    penalty_amount: str = Field(..., description="违约金金额")
    risk_level: RiskLevel = Field(..., description="风险等级")
    issues: List[str] = Field(..., description="发现的问题")
    suggestions: List[str] = Field(..., description="改进建议")

class BreachClauseReview(BaseModel):
    """违约条款审查结果"""
    overall_risk_level: RiskLevel = Field(..., description="整体风险等级")
    breach_clauses: List[BreachClauseItem] = Field(..., description="违约条款审查项目")
    total_penalty: str = Field(..., description="总违约金")
    breach_analysis: str = Field(..., description="违约条款分析")
    summary: str = Field(..., description="违约条款审查总结")
    recommendations: List[str] = Field(..., description="违约相关建议")

# 通用审查模型
class GeneralReviewItem(BaseModel):
    """通用审查项目"""
    review_category: str = Field(..., description="审查类别")
    item_name: str = Field(..., description="审查项目名称")
    item_content: str = Field(..., description="审查项目内容")
    risk_level: RiskLevel = Field(..., description="风险等级")
    issues: List[str] = Field(..., description="发现的问题")
    suggestions: List[str] = Field(..., description="改进建议")

class GeneralReview(BaseModel):
    """通用审查结果"""
    overall_risk_level: RiskLevel = Field(..., description="整体风险等级")
    review_items: List[GeneralReviewItem] = Field(..., description="通用审查项目")
    summary: str = Field(..., description="通用审查总结")
    recommendations: List[str] = Field(..., description="通用建议")

# 综合审查结果模型
class ComprehensiveContractReview(BaseModel):
    """综合合同审查结果"""
    contract_name: str = Field(..., description="合同名称")
    review_timestamp: datetime = Field(default_factory=datetime.now, description="审查时间")
    overall_risk_level: RiskLevel = Field(..., description="整体风险等级")
    
    # 四种审查类型的结果
    subject_review: Optional[ContractSubjectReview] = Field(None, description="合同主体审查结果")
    payment_review: Optional[PaymentClauseReview] = Field(None, description="付款条款审查结果")
    breach_review: Optional[BreachClauseReview] = Field(None, description="违约条款审查结果")
    general_review: Optional[GeneralReview] = Field(None, description="通用审查结果")
    
    # 综合信息
    total_issues: int = Field(..., description="总问题数量")
    high_risk_items: int = Field(..., description="高风险项目数量")
    medium_risk_items: int = Field(..., description="中风险项目数量")
    low_risk_items: int = Field(..., description="低风险项目数量")
    
    # 总体建议
    overall_summary: str = Field(..., description="总体审查总结")
    critical_recommendations: List[str] = Field(..., description="关键建议")
    action_items: List[str] = Field(..., description="需要采取的行动")
    
    # 元数据
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="审查置信度")
    review_duration: float = Field(..., description="审查耗时（秒）")
    model_used: str = Field(..., description="使用的模型") 