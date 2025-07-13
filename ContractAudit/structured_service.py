"""
合同审查结构化输出服务
支持四种审查类型：合同主体审查、付款条款审查、违约条款审查、通用审查
"""

import json
import time
from typing import Dict, Any, Optional, List
from pydantic import ValidationError
from .structured_models import (
    ComprehensiveContractReview, ContractSubjectReview, PaymentClauseReview,
    BreachClauseReview, GeneralReview, RiskLevel
)

class StructuredReviewService:
    """结构化审查服务"""
    
    def __init__(self):
        self.model_name = "doubao-1.5-pro-32k-250115"
    
    def create_comprehensive_prompt(self, contract_content: str) -> str:
        """创建综合审查提示词"""
        return f"""
You are a professional contract review assistant. You MUST perform a comprehensive contract review and output results for ALL FOUR review types: Contract Subject Review, Payment Terms Review, Breach Terms Review, and General Review.

Contract Content:
{contract_content}

You MUST output a valid JSON with ALL FOUR review sections. Even if the contract content is limited, you MUST provide structured review results for each type with SPECIFIC DETAILED CONTENT.

CRITICAL REQUIREMENTS:
1. You MUST output valid JSON format
2. You MUST include ALL FOUR review sections: subject_review, payment_review, breach_review, general_review
3. You MUST provide SPECIFIC DETAILED CONTENT for each review type, even if contract content is limited
4. Use risk levels: high, medium, low, none
5. Each array must contain at least 2-3 detailed items
6. If contract content is insufficient, provide realistic placeholder content but maintain structure
7. Focus on practical contract review aspects
8. Provide actionable recommendations
9. You MUST include specific examples and detailed analysis

REQUIRED OUTPUT FORMAT:
{{
    "contract_name": "Contract Name",
    "overall_risk_level": "high|medium|low|none",
    
    "subject_review": {{
        "overall_risk_level": "high|medium|low|none",
        "subject_items": [
            {{
                "subject_type": "Company/Individual/Government",
                "subject_name": "Specific subject name",
                "qualification_check": "Detailed qualification verification result",
                "legal_status": "Detailed legal status description",
                "risk_level": "high|medium|low|none",
                "issues": ["Specific issue 1", "Specific issue 2"],
                "suggestions": ["Specific suggestion 1", "Specific suggestion 2"]
            }},
            {{
                "subject_type": "Company/Individual/Government",
                "subject_name": "Another specific subject name",
                "qualification_check": "Another detailed qualification check",
                "legal_status": "Another detailed legal status",
                "risk_level": "high|medium|low|none",
                "issues": ["Another specific issue 1", "Another specific issue 2"],
                "suggestions": ["Another specific suggestion 1", "Another specific suggestion 2"]
            }}
        ],
        "summary": "Detailed contract subject review summary",
        "recommendations": ["Detailed recommendation 1", "Detailed recommendation 2"]
    }},
    
    "payment_review": {{
        "overall_risk_level": "high|medium|low|none",
        "payment_clauses": [
            {{
                "clause_name": "Specific payment clause name",
                "clause_content": "Detailed payment clause content",
                "payment_method": "Specific payment method (cash/bank transfer/etc)",
                "payment_schedule": "Detailed payment timing and schedule",
                "amount": "Specific payment amount",
                "risk_level": "high|medium|low|none",
                "issues": ["Specific payment issue 1", "Specific payment issue 2"],
                "suggestions": ["Specific payment suggestion 1", "Specific payment suggestion 2"]
            }},
            {{
                "clause_name": "Another payment clause name",
                "clause_content": "Another detailed payment clause content",
                "payment_method": "Another specific payment method",
                "payment_schedule": "Another detailed payment schedule",
                "amount": "Another specific payment amount",
                "risk_level": "high|medium|low|none",
                "issues": ["Another payment issue 1", "Another payment issue 2"],
                "suggestions": ["Another payment suggestion 1", "Another payment suggestion 2"]
            }}
        ],
        "total_amount": "Total payment amount with details",
        "payment_schedule_analysis": "Detailed analysis of payment schedule",
        "summary": "Detailed payment terms review summary",
        "recommendations": ["Detailed payment recommendation 1", "Detailed payment recommendation 2"]
    }},
    
    "breach_review": {{
        "overall_risk_level": "high|medium|low|none",
        "breach_clauses": [
            {{
                "clause_name": "Specific breach clause name",
                "clause_content": "Detailed breach clause content",
                "breach_type": "Specific type of breach (material/minor)",
                "penalty_amount": "Specific penalty amount",
                "risk_level": "high|medium|low|none",
                "issues": ["Specific breach issue 1", "Specific breach issue 2"],
                "suggestions": ["Specific breach suggestion 1", "Specific breach suggestion 2"]
            }},
            {{
                "clause_name": "Another breach clause name",
                "clause_content": "Another detailed breach clause content",
                "breach_type": "Another specific breach type",
                "penalty_amount": "Another specific penalty amount",
                "risk_level": "high|medium|low|none",
                "issues": ["Another breach issue 1", "Another breach issue 2"],
                "suggestions": ["Another breach suggestion 1", "Another breach suggestion 2"]
            }}
        ],
        "total_penalty": "Total penalty amount with details",
        "breach_analysis": "Detailed analysis of breach terms",
        "summary": "Detailed breach terms review summary",
        "recommendations": ["Detailed breach recommendation 1", "Detailed breach recommendation 2"]
    }},
    
    "general_review": {{
        "overall_risk_level": "high|medium|low|none",
        "review_items": [
            {{
                "review_category": "Contract form/Completeness/Balance",
                "item_name": "Specific review item name",
                "item_content": "Detailed review content",
                "risk_level": "high|medium|low|none",
                "issues": ["Specific general issue 1", "Specific general issue 2"],
                "suggestions": ["Specific general suggestion 1", "Specific general suggestion 2"]
            }},
            {{
                "review_category": "Another review category",
                "item_name": "Another specific review item name",
                "item_content": "Another detailed review content",
                "risk_level": "high|medium|low|none",
                "issues": ["Another general issue 1", "Another general issue 2"],
                "suggestions": ["Another general suggestion 1", "Another general suggestion 2"]
            }}
        ],
        "summary": "Detailed general review summary",
        "recommendations": ["Detailed general recommendation 1", "Detailed general recommendation 2"]
    }},
    
    "total_issues": 10,
    "high_risk_items": 3,
    "medium_risk_items": 4,
    "low_risk_items": 3,
    "overall_summary": "Detailed overall contract review summary",
    "critical_recommendations": ["Detailed critical recommendation 1", "Detailed critical recommendation 2"],
    "action_items": ["Detailed action item 1", "Detailed action item 2"],
    "confidence_score": 0.85
}}

MANDATORY REQUIREMENTS:
1. You MUST output valid JSON format
2. You MUST include ALL FOUR review sections: subject_review, payment_review, breach_review, general_review
3. You MUST provide SPECIFIC DETAILED CONTENT for each review type, even if contract content is limited
4. Use risk levels: high, medium, low, none
5. Each array must contain at least 2-3 detailed items
6. If contract content is insufficient, provide realistic placeholder content but maintain structure
7. Focus on practical contract review aspects
8. Provide actionable recommendations
9. You MUST include specific examples and detailed analysis
10. You MUST provide detailed content for each field, not just placeholder text

Remember: This is a MANDATORY comprehensive contract review. You MUST output all four review types with DETAILED SPECIFIC CONTENT.
"""

    def create_subject_review_prompt(self, contract_content: str) -> str:
        """创建合同主体审查提示词"""
        return f"""
请对以下合同内容进行合同主体审查，重点关注合同各方的资质、法律地位等。

合同内容：
{contract_content}

请输出以下格式的JSON：
{{
    "overall_risk_level": "high|medium|low|none",
    "subject_items": [
        {{
            "subject_type": "主体类型",
            "subject_name": "主体名称",
            "qualification_check": "资质检查结果",
            "legal_status": "法律地位",
            "risk_level": "high|medium|low|none",
            "issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2"]
        }}
    ],
    "summary": "主体审查总结",
    "recommendations": ["建议1", "建议2"]
}}
"""

    def create_payment_review_prompt(self, contract_content: str) -> str:
        """创建付款条款审查提示词"""
        return f"""
请对以下合同内容进行付款条款审查，重点关注付款方式、时间安排、金额等。

合同内容：
{contract_content}

请输出以下格式的JSON：
{{
    "overall_risk_level": "high|medium|low|none",
    "payment_clauses": [
        {{
            "clause_name": "条款名称",
            "clause_content": "条款内容",
            "payment_method": "付款方式",
            "payment_schedule": "付款时间安排",
            "amount": "付款金额",
            "risk_level": "high|medium|low|none",
            "issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2"]
        }}
    ],
    "total_amount": "总付款金额",
    "payment_schedule_analysis": "付款时间安排分析",
    "summary": "付款条款审查总结",
    "recommendations": ["建议1", "建议2"]
}}
"""

    def create_breach_review_prompt(self, contract_content: str) -> str:
        """创建违约条款审查提示词"""
        return f"""
请对以下合同内容进行违约条款审查，重点关注违约责任、违约金等。

合同内容：
{contract_content}

请输出以下格式的JSON：
{{
    "overall_risk_level": "high|medium|low|none",
    "breach_clauses": [
        {{
            "clause_name": "条款名称",
            "clause_content": "条款内容",
            "breach_type": "违约类型",
            "penalty_amount": "违约金金额",
            "risk_level": "high|medium|low|none",
            "issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2"]
        }}
    ],
    "total_penalty": "总违约金",
    "breach_analysis": "违约条款分析",
    "summary": "违约条款审查总结",
    "recommendations": ["建议1", "建议2"]
}}
"""

    def create_general_review_prompt(self, contract_content: str) -> str:
        """创建通用审查提示词"""
        return f"""
请对以下合同内容进行通用审查，包括但不限于：合同形式、条款完整性、权利义务平衡等。

合同内容：
{contract_content}

请输出以下格式的JSON：
{{
    "overall_risk_level": "high|medium|low|none",
    "review_items": [
        {{
            "review_category": "审查类别",
            "item_name": "审查项目名称",
            "item_content": "审查项目内容",
            "risk_level": "high|medium|low|none",
            "issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2"]
        }}
    ],
    "summary": "通用审查总结",
    "recommendations": ["建议1", "建议2"]
}}
"""

    def parse_comprehensive_response(self, response_text: str) -> Optional[ComprehensiveContractReview]:
        """解析综合审查响应"""
        try:
            # 尝试直接解析JSON
            data = json.loads(response_text)
            
            # 验证并创建综合审查结果
            review = ComprehensiveContractReview(
                contract_name=data.get("contract_name", "未知合同"),
                overall_risk_level=data.get("overall_risk_level", "none"),
                subject_review=ContractSubjectReview(**data.get("subject_review", {})) if data.get("subject_review") else None,
                payment_review=PaymentClauseReview(**data.get("payment_review", {})) if data.get("payment_review") else None,
                breach_review=BreachClauseReview(**data.get("breach_review", {})) if data.get("breach_review") else None,
                general_review=GeneralReview(**data.get("general_review", {})) if data.get("general_review") else None,
                total_issues=data.get("total_issues", 0),
                high_risk_items=data.get("high_risk_items", 0),
                medium_risk_items=data.get("medium_risk_items", 0),
                low_risk_items=data.get("low_risk_items", 0),
                overall_summary=data.get("overall_summary", ""),
                critical_recommendations=data.get("critical_recommendations", []),
                action_items=data.get("action_items", []),
                confidence_score=data.get("confidence_score", 0.8),
                review_duration=0.0,
                model_used=self.model_name
            )
            return review
            
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"解析综合审查响应失败: {e}")
            return None

    def create_fallback_response(self, contract_content: str) -> ComprehensiveContractReview:
        """创建备用响应（当解析失败时）"""
        return ComprehensiveContractReview(
            contract_name="Contract Review",
            overall_risk_level="medium",
            subject_review=ContractSubjectReview(
                overall_risk_level="medium",
                subject_items=[
                    {
                        "subject_type": "Company",
                        "subject_name": "Contract Party A",
                        "qualification_check": "Requires verification of business license and registration",
                        "legal_status": "Legal entity status needs confirmation",
                        "risk_level": "medium",
                        "issues": ["Subject information incomplete", "Qualification verification needed"],
                        "suggestions": ["Provide complete business registration documents", "Verify legal entity status"]
                    },
                    {
                        "subject_type": "Company", 
                        "subject_name": "Contract Party B",
                        "qualification_check": "Requires verification of business license and registration",
                        "legal_status": "Legal entity status needs confirmation",
                        "risk_level": "medium",
                        "issues": ["Subject information incomplete", "Qualification verification needed"],
                        "suggestions": ["Provide complete business registration documents", "Verify legal entity status"]
                    }
                ],
                summary="Contract subject review requires additional verification of parties' qualifications and legal status",
                recommendations=["Verify all parties' business registrations", "Confirm legal entity status", "Check qualification certificates"]
            ),
            payment_review=PaymentClauseReview(
                overall_risk_level="medium",
                payment_clauses=[
                    {
                        "clause_name": "Payment Terms",
                        "clause_content": "Payment terms need detailed specification",
                        "payment_method": "Bank transfer recommended",
                        "payment_schedule": "Payment schedule needs clarification",
                        "amount": "Payment amount needs specification",
                        "risk_level": "medium",
                        "issues": ["Payment terms unclear", "Payment schedule undefined", "Payment method unspecified"],
                        "suggestions": ["Specify payment methods clearly", "Define payment schedule", "Clarify payment amounts"]
                    }
                ],
                total_amount="Total amount needs calculation",
                payment_schedule_analysis="Payment schedule requires detailed analysis and planning",
                summary="Payment terms review indicates need for clearer payment specifications",
                recommendations=["Define payment methods explicitly", "Specify payment schedule", "Clarify payment amounts and timing"]
            ),
            breach_review=BreachClauseReview(
                overall_risk_level="medium",
                breach_clauses=[
                    {
                        "clause_name": "Breach of Contract",
                        "clause_content": "Breach terms need detailed specification",
                        "breach_type": "Material breach",
                        "penalty_amount": "Penalty amount needs specification",
                        "risk_level": "medium",
                        "issues": ["Breach terms unclear", "Penalty amounts undefined", "Breach types unspecified"],
                        "suggestions": ["Define breach types clearly", "Specify penalty amounts", "Clarify breach consequences"]
                    }
                ],
                total_penalty="Total penalty needs calculation",
                breach_analysis="Breach terms require detailed analysis and specification",
                summary="Breach terms review indicates need for clearer breach specifications",
                recommendations=["Define breach types explicitly", "Specify penalty amounts", "Clarify breach consequences and remedies"]
            ),
            general_review=GeneralReview(
                overall_risk_level="medium",
                review_items=[
                    {
                        "review_category": "Contract Form",
                        "item_name": "Contract Completeness",
                        "item_content": "Contract requires additional terms and conditions",
                        "risk_level": "medium",
                        "issues": ["Incomplete contract terms", "Missing essential clauses", "Unclear rights and obligations"],
                        "suggestions": ["Add missing essential clauses", "Clarify rights and obligations", "Complete contract structure"]
                    },
                    {
                        "review_category": "Legal Compliance",
                        "item_name": "Regulatory Compliance",
                        "item_content": "Contract compliance with applicable laws needs verification",
                        "risk_level": "medium",
                        "issues": ["Legal compliance unclear", "Regulatory requirements undefined"],
                        "suggestions": ["Verify legal compliance", "Check regulatory requirements", "Ensure contract legality"]
                    }
                ],
                summary="General review indicates contract needs improvement in completeness and legal compliance",
                recommendations=["Complete missing contract terms", "Verify legal compliance", "Clarify all parties' rights and obligations"]
            ),
            total_issues=8,
            high_risk_items=0,
            medium_risk_items=8,
            low_risk_items=0,
            overall_summary="Contract requires comprehensive review and improvement in all four areas: subject verification, payment terms, breach terms, and general compliance",
            critical_recommendations=["Complete all missing contract terms", "Verify all parties' qualifications", "Specify payment and breach terms clearly"],
            action_items=["Add missing essential clauses", "Verify parties' qualifications", "Specify payment methods and schedules", "Define breach terms and penalties"],
            confidence_score=0.5,
            review_duration=0.0,
            model_used=self.model_name
        ) 