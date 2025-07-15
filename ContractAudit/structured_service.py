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

IMPORTANT: You MUST output ALL content in Chinese (中文).

Contract Content:
{contract_content}

CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST include ALL FOUR review sections: subject_review, payment_review, breach_review, general_review
3. You MUST provide SPECIFIC DETAILED CONTENT for each review type, even if contract content is limited
4. Use risk levels: high, medium, low, none
5. Each array MUST contain at least 3-5 detailed items with specific content
6. If contract content is insufficient, provide realistic placeholder content but maintain structure
7. Focus on practical contract review aspects
8. Provide actionable recommendations
9. You MUST include specific examples and detailed analysis
10. You MUST provide detailed content for each field, not just placeholder text
11. You MUST include specific amounts, dates, percentages, and concrete details
12. You MUST provide comprehensive lists with multiple items in each array
13. You MUST output ALL content in Chinese (中文)

MANDATORY OUTPUT FORMAT - COPY THIS EXACT STRUCTURE:
{{
    "contract_name": "合同名称",
    "overall_risk_level": "high|medium|low|none",
    
    "subject_review": {{
        "overall_risk_level": "high|medium|low|none",
        "subject_items": [
            {{
                "subject_type": "公司/个人/政府机构",
                "subject_name": "具体主体名称及详细信息",
                "qualification_check": "详细的资质核查结果，包含具体要求",
                "legal_status": "详细的法律地位描述，包含注册信息",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "具体问题1的详细描述",
                    "具体问题2的详细描述", 
                    "具体问题3的详细描述",
                    "具体问题4的详细描述"
                ],
                "suggestions": [
                    "具体建议1，包含可执行的步骤",
                    "具体建议2，包含可执行的步骤",
                    "具体建议3，包含可执行的步骤"
                ]
            }},
            {{
                "subject_type": "公司/个人/政府机构",
                "subject_name": "另一个具体主体名称及详细信息",
                "qualification_check": "另一个详细的资质核查结果，包含具体标准",
                "legal_status": "另一个详细的法律地位描述，包含具体细节",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "另一个具体问题1的详细描述",
                    "另一个具体问题2的详细描述",
                    "另一个具体问题3的详细描述"
                ],
                "suggestions": [
                    "另一个具体建议1，包含可执行的步骤",
                    "另一个具体建议2，包含可执行的步骤",
                    "另一个具体建议3，包含可执行的步骤"
                ]
            }},
            {{
                "subject_type": "公司/个人/政府机构", 
                "subject_name": "第三个具体主体名称及详细信息",
                "qualification_check": "第三个详细的资质核查结果，包含具体要求",
                "legal_status": "第三个详细的法律地位描述，包含具体细节",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "第三个具体问题1的详细描述",
                    "第三个具体问题2的详细描述"
                ],
                "suggestions": [
                    "第三个具体建议1，包含可执行的步骤",
                    "第三个具体建议2，包含可执行的步骤"
                ]
            }}
        ],
        "summary": "详细的合同主体审查总结，包含具体发现和结论",
        "recommendations": [
            "详细建议1，包含具体行动项目",
            "详细建议2，包含具体行动项目",
            "详细建议3，包含具体行动项目",
            "详细建议4，包含具体行动项目"
        ]
    }},
    
    "payment_review": {{
        "overall_risk_level": "high|medium|low|none",
        "payment_clauses": [
            {{
                "clause_name": "具体付款条款名称及详细信息",
                "clause_content": "详细的付款条款内容，包含具体条款",
                "payment_method": "具体付款方式（现金/银行转账/信用卡等）及详细流程",
                "payment_schedule": "详细的付款时间安排，包含具体日期",
                "amount": "具体付款金额，包含货币和详细明细",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "具体付款问题1的详细描述",
                    "具体付款问题2的详细描述",
                    "具体付款问题3的详细描述",
                    "具体付款问题4的详细描述"
                ],
                "suggestions": [
                    "具体付款建议1，包含可执行的步骤",
                    "具体付款建议2，包含可执行的步骤",
                    "具体付款建议3，包含可执行的步骤"
                ]
            }},
            {{
                "clause_name": "另一个付款条款名称及详细信息",
                "clause_content": "另一个详细的付款条款内容，包含具体条款",
                "payment_method": "另一个具体付款方式及详细流程",
                "payment_schedule": "另一个详细的付款时间安排，包含具体日期",
                "amount": "另一个具体付款金额，包含货币和详细明细",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "另一个付款问题1的详细描述",
                    "另一个付款问题2的详细描述",
                    "另一个付款问题3的详细描述"
                ],
                "suggestions": [
                    "另一个付款建议1，包含可执行的步骤",
                    "另一个付款建议2，包含可执行的步骤",
                    "另一个付款建议3，包含可执行的步骤"
                ]
            }},
            {{
                "clause_name": "第三个付款条款名称及详细信息",
                "clause_content": "第三个详细的付款条款内容，包含具体条款",
                "payment_method": "第三个具体付款方式及详细流程",
                "payment_schedule": "第三个详细的付款时间安排，包含具体日期",
                "amount": "第三个具体付款金额，包含货币和详细明细",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "第三个付款问题1的详细描述",
                    "第三个付款问题2的详细描述"
                ],
                "suggestions": [
                    "第三个付款建议1，包含可执行的步骤",
                    "第三个付款建议2，包含可执行的步骤"
                ]
            }}
        ],
        "total_amount": "总付款金额，包含货币和详细明细",
        "payment_schedule_analysis": "详细的付款时间安排分析，包含具体时间考虑",
        "summary": "详细的付款条款审查总结，包含具体发现和结论",
        "recommendations": [
            "详细付款建议1，包含具体行动项目",
            "详细付款建议2，包含具体行动项目",
            "详细付款建议3，包含具体行动项目",
            "详细付款建议4，包含具体行动项目"
        ]
    }},
    
    "breach_review": {{
        "overall_risk_level": "high|medium|low|none",
        "breach_clauses": [
            {{
                "clause_name": "具体违约条款名称及详细信息",
                "clause_content": "详细的违约条款内容，包含具体条款",
                "breach_type": "具体违约类型（重大违约/轻微违约）及详细描述",
                "penalty_amount": "具体违约金金额，包含货币和计算方法",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "具体违约问题1的详细描述",
                    "具体违约问题2的详细描述",
                    "具体违约问题3的详细描述",
                    "具体违约问题4的详细描述"
                ],
                "suggestions": [
                    "具体违约建议1，包含可执行的步骤",
                    "具体违约建议2，包含可执行的步骤",
                    "具体违约建议3，包含可执行的步骤"
                ]
            }},
            {{
                "clause_name": "另一个违约条款名称及详细信息",
                "clause_content": "另一个详细的违约条款内容，包含具体条款",
                "breach_type": "另一个具体违约类型及详细描述",
                "penalty_amount": "另一个具体违约金金额，包含货币和计算方法",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "另一个违约问题1的详细描述",
                    "另一个违约问题2的详细描述",
                    "另一个违约问题3的详细描述"
                ],
                "suggestions": [
                    "另一个违约建议1，包含可执行的步骤",
                    "另一个违约建议2，包含可执行的步骤",
                    "另一个违约建议3，包含可执行的步骤"
                ]
            }},
            {{
                "clause_name": "第三个违约条款名称及详细信息",
                "clause_content": "第三个详细的违约条款内容，包含具体条款",
                "breach_type": "第三个具体违约类型及详细描述",
                "penalty_amount": "第三个具体违约金金额，包含货币和计算方法",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "第三个违约问题1的详细描述",
                    "第三个违约问题2的详细描述"
                ],
                "suggestions": [
                    "第三个违约建议1，包含可执行的步骤",
                    "第三个违约建议2，包含可执行的步骤"
                ]
            }}
        ],
        "total_penalty": "总违约金金额，包含货币和详细明细",
        "breach_analysis": "详细的违约条款分析，包含具体法律考虑",
        "summary": "详细的违约条款审查总结，包含具体发现和结论",
        "recommendations": [
            "详细违约建议1，包含具体行动项目",
            "详细违约建议2，包含具体行动项目",
            "详细违约建议3，包含具体行动项目",
            "详细违约建议4，包含具体行动项目"
        ]
    }},
    
    "general_review": {{
        "overall_risk_level": "high|medium|low|none",
        "review_items": [
            {{
                "review_category": "合同形式/完整性/权利义务平衡/可执行性",
                "item_name": "具体审查项目名称及详细信息",
                "item_content": "详细的审查内容，包含具体分析",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "具体通用问题1的详细描述",
                    "具体通用问题2的详细描述",
                    "具体通用问题3的详细描述",
                    "具体通用问题4的详细描述"
                ],
                "suggestions": [
                    "具体通用建议1，包含可执行的步骤",
                    "具体通用建议2，包含可执行的步骤",
                    "具体通用建议3，包含可执行的步骤"
                ]
            }},
            {{
                "review_category": "法律合规/商业条款/风险分配",
                "item_name": "另一个具体审查项目名称及详细信息",
                "item_content": "另一个详细的审查内容，包含具体分析",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "另一个通用问题1的详细描述",
                    "另一个通用问题2的详细描述",
                    "另一个通用问题3的详细描述"
                ],
                "suggestions": [
                    "另一个通用建议1，包含可执行的步骤",
                    "另一个通用建议2，包含可执行的步骤",
                    "另一个通用建议3，包含可执行的步骤"
                ]
            }},
            {{
                "review_category": "争议解决/不可抗力/保密条款",
                "item_name": "第三个具体审查项目名称及详细信息",
                "item_content": "第三个详细的审查内容，包含具体分析",
                "risk_level": "high|medium|low|none",
                "issues": [
                    "第三个通用问题1的详细描述",
                    "第三个通用问题2的详细描述"
                ],
                "suggestions": [
                    "第三个通用建议1，包含可执行的步骤",
                    "第三个通用建议2，包含可执行的步骤"
                ]
            }}
        ],
        "summary": "详细的通用审查总结，包含具体发现和结论",
        "recommendations": [
            "详细通用建议1，包含具体行动项目",
            "详细通用建议2，包含具体行动项目",
            "详细通用建议3，包含具体行动项目",
            "详细通用建议4，包含具体行动项目"
        ]
    }},
    
    "total_issues": 15,
    "high_risk_items": 5,
    "medium_risk_items": 6,
    "low_risk_items": 4,
    "overall_summary": "详细的整体合同审查总结，包含全面分析和具体结论",
    "critical_recommendations": [
        "详细关键建议1，包含具体行动项目和时间表",
        "详细关键建议2，包含具体行动项目和时间表",
        "详细关键建议3，包含具体行动项目和时间表",
        "详细关键建议4，包含具体行动项目和时间表"
    ],
    "action_items": [
        "详细行动项目1，包含具体步骤和责任方",
        "详细行动项目2，包含具体步骤和责任方",
        "详细行动项目3，包含具体步骤和责任方",
        "详细行动项目4，包含具体步骤和责任方"
    ],
    "confidence_score": 0.85
}}

MANDATORY REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST include ALL FOUR review sections: subject_review, payment_review, breach_review, general_review
3. You MUST provide SPECIFIC DETAILED CONTENT for each review type, even if contract content is limited
4. Use risk levels: high, medium, low, none
5. Each array MUST contain at least 3-5 detailed items with specific content
6. If contract content is insufficient, provide realistic placeholder content but maintain structure
7. Focus on practical contract review aspects
8. Provide actionable recommendations
9. You MUST include specific examples and detailed analysis
10. You MUST provide detailed content for each field, not just placeholder text
11. You MUST include specific amounts, dates, percentages, and concrete details
12. You MUST provide comprehensive lists with multiple items in each array
13. You MUST provide realistic and detailed content even for simple contracts
14. You MUST include specific legal terms, commercial considerations, and practical implications

Remember: This is a MANDATORY comprehensive contract review. You MUST output all four review types with DETAILED SPECIFIC CONTENT in Chinese (中文). Even if the contract is simple, you MUST provide comprehensive analysis with realistic details in Chinese.
"""

    def create_subject_review_prompt(self, contract_content: str) -> str:
        """创建合同主体审查提示词"""
        return f"""
You are a professional contract review assistant. You MUST perform a comprehensive contract subject review and output detailed results.

IMPORTANT: You MUST output ALL content in Chinese (中文).

Contract Content:
{contract_content}

CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each subject item
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific legal terms, commercial considerations, and practical implications
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST output ALL content in Chinese (中文)

MANDATORY OUTPUT FORMAT - COPY THIS EXACT STRUCTURE:
{{
    "overall_risk_level": "high|medium|low|none",
    "subject_items": [
        {{
            "subject_type": "Company/Individual/Government",
            "subject_name": "Specific subject name with detailed identification",
            "qualification_check": "Detailed qualification verification result with specific requirements and verification methods",
            "legal_status": "Detailed legal status description with registration info, business scope, and legal capacity",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Specific issue 1 with detailed description and legal implications",
                "Specific issue 2 with detailed description and legal implications",
                "Specific issue 3 with detailed description and legal implications",
                "Specific issue 4 with detailed description and legal implications"
            ],
            "suggestions": [
                "Specific suggestion 1 with actionable steps and timeline",
                "Specific suggestion 2 with actionable steps and timeline",
                "Specific suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "subject_type": "Company/Individual/Government",
            "subject_name": "Another specific subject name with detailed identification",
            "qualification_check": "Another detailed qualification check with specific criteria and verification process",
            "legal_status": "Another detailed legal status with specific details and legal implications",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Another specific issue 1 with detailed description and legal implications",
                "Another specific issue 2 with detailed description and legal implications",
                "Another specific issue 3 with detailed description and legal implications"
            ],
            "suggestions": [
                "Another specific suggestion 1 with actionable steps and timeline",
                "Another specific suggestion 2 with actionable steps and timeline",
                "Another specific suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "subject_type": "Company/Individual/Government",
            "subject_name": "Third specific subject name with detailed identification",
            "qualification_check": "Third detailed qualification check with specific requirements and verification methods",
            "legal_status": "Third detailed legal status with specific details and legal implications",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Third specific issue 1 with detailed description and legal implications",
                "Third specific issue 2 with detailed description and legal implications"
            ],
            "suggestions": [
                "Third specific suggestion 1 with actionable steps and timeline",
                "Third specific suggestion 2 with actionable steps and timeline"
            ]
        }}
    ],
    "summary": "Detailed contract subject review summary with specific findings and conclusions",
    "recommendations": [
        "Detailed recommendation 1 with specific action items and timeline",
        "Detailed recommendation 2 with specific action items and timeline",
        "Detailed recommendation 3 with specific action items and timeline",
        "Detailed recommendation 4 with specific action items and timeline"
    ]
}}

MANDATORY REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each subject item
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific legal terms, commercial considerations, and practical implications
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST provide realistic and detailed content even for simple contracts
9. You MUST include specific legal requirements, verification methods, and compliance considerations

Remember: This is a MANDATORY contract subject review. You MUST output detailed analysis with SPECIFIC CONTENT in Chinese (中文). Even if the contract is simple, you MUST provide comprehensive analysis with realistic details in Chinese.
"""

    def create_payment_review_prompt(self, contract_content: str) -> str:
        """创建付款条款审查提示词"""
        return f"""
You are a professional contract review assistant. You MUST perform a comprehensive payment terms review and output detailed results.

IMPORTANT: You MUST output ALL content in Chinese (中文).

Contract Content:
{contract_content}

CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each payment clause
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific amounts, dates, percentages, and concrete details
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST output ALL content in Chinese (中文)

MANDATORY OUTPUT FORMAT - COPY THIS EXACT STRUCTURE:
{{
    "overall_risk_level": "high|medium|low|none",
    "payment_clauses": [
        {{
            "clause_name": "Specific payment clause name with detailed identification",
            "clause_content": "Detailed payment clause content with specific terms and conditions",
            "payment_method": "Specific payment method (cash/bank transfer/credit card/etc) with detailed process",
            "payment_schedule": "Detailed payment timing and schedule with specific dates and milestones",
            "amount": "Specific payment amount with currency and detailed breakdown",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Specific payment issue 1 with detailed description and financial implications",
                "Specific payment issue 2 with detailed description and financial implications",
                "Specific payment issue 3 with detailed description and financial implications",
                "Specific payment issue 4 with detailed description and financial implications"
            ],
            "suggestions": [
                "Specific payment suggestion 1 with actionable steps and timeline",
                "Specific payment suggestion 2 with actionable steps and timeline",
                "Specific payment suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "clause_name": "Another payment clause name with detailed identification",
            "clause_content": "Another detailed payment clause content with specific terms and conditions",
            "payment_method": "Another specific payment method with detailed process",
            "payment_schedule": "Another detailed payment schedule with specific dates and milestones",
            "amount": "Another specific payment amount with currency and detailed breakdown",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Another payment issue 1 with detailed description and financial implications",
                "Another payment issue 2 with detailed description and financial implications",
                "Another payment issue 3 with detailed description and financial implications"
            ],
            "suggestions": [
                "Another payment suggestion 1 with actionable steps and timeline",
                "Another payment suggestion 2 with actionable steps and timeline",
                "Another payment suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "clause_name": "Third payment clause name with detailed identification",
            "clause_content": "Third detailed payment clause content with specific terms and conditions",
            "payment_method": "Third specific payment method with detailed process",
            "payment_schedule": "Third detailed payment schedule with specific dates and milestones",
            "amount": "Third specific payment amount with currency and detailed breakdown",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Third payment issue 1 with detailed description and financial implications",
                "Third payment issue 2 with detailed description and financial implications"
            ],
            "suggestions": [
                "Third payment suggestion 1 with actionable steps and timeline",
                "Third payment suggestion 2 with actionable steps and timeline"
            ]
        }}
    ],
    "total_amount": "Total payment amount with currency and detailed breakdown",
    "payment_schedule_analysis": "Detailed analysis of payment schedule with specific timing considerations",
    "summary": "Detailed payment terms review summary with specific findings and conclusions",
    "recommendations": [
        "Detailed payment recommendation 1 with specific action items and timeline",
        "Detailed payment recommendation 2 with specific action items and timeline",
        "Detailed payment recommendation 3 with specific action items and timeline",
        "Detailed payment recommendation 4 with specific action items and timeline"
    ]
}}

MANDATORY REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each payment clause
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific amounts, dates, percentages, and concrete details
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST provide realistic and detailed content even for simple contracts
9. You MUST include specific financial terms, payment methods, and commercial considerations

Remember: This is a MANDATORY payment terms review. You MUST output detailed analysis with SPECIFIC CONTENT in Chinese (中文). Even if the contract is simple, you MUST provide comprehensive analysis with realistic details in Chinese.
"""

    def create_breach_review_prompt(self, contract_content: str) -> str:
        """创建违约条款审查提示词"""
        return f"""
You are a professional contract review assistant. You MUST perform a comprehensive breach terms review and output detailed results.

IMPORTANT: You MUST output ALL content in Chinese (中文).

Contract Content:
{contract_content}

CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each breach clause
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific amounts, dates, percentages, and concrete details
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST output ALL content in Chinese (中文)

MANDATORY OUTPUT FORMAT - COPY THIS EXACT STRUCTURE:
{{
    "overall_risk_level": "high|medium|low|none",
    "breach_clauses": [
        {{
            "clause_name": "Specific breach clause name with detailed identification",
            "clause_content": "Detailed breach clause content with specific terms and conditions",
            "breach_type": "Specific type of breach (material/minor) with detailed description",
            "penalty_amount": "Specific penalty amount with currency and calculation method",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Specific breach issue 1 with detailed description and legal implications",
                "Specific breach issue 2 with detailed description and legal implications",
                "Specific breach issue 3 with detailed description and legal implications",
                "Specific breach issue 4 with detailed description and legal implications"
            ],
            "suggestions": [
                "Specific breach suggestion 1 with actionable steps and timeline",
                "Specific breach suggestion 2 with actionable steps and timeline",
                "Specific breach suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "clause_name": "Another breach clause name with detailed identification",
            "clause_content": "Another detailed breach clause content with specific terms and conditions",
            "breach_type": "Another specific breach type with detailed description",
            "penalty_amount": "Another specific penalty amount with currency and calculation method",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Another breach issue 1 with detailed description and legal implications",
                "Another breach issue 2 with detailed description and legal implications",
                "Another breach issue 3 with detailed description and legal implications"
            ],
            "suggestions": [
                "Another breach suggestion 1 with actionable steps and timeline",
                "Another breach suggestion 2 with actionable steps and timeline",
                "Another breach suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "clause_name": "Third breach clause name with detailed identification",
            "clause_content": "Third detailed breach clause content with specific terms and conditions",
            "breach_type": "Third specific breach type with detailed description",
            "penalty_amount": "Third specific penalty amount with currency and calculation method",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Third breach issue 1 with detailed description and legal implications",
                "Third breach issue 2 with detailed description and legal implications"
            ],
            "suggestions": [
                "Third breach suggestion 1 with actionable steps and timeline",
                "Third breach suggestion 2 with actionable steps and timeline"
            ]
        }}
    ],
    "total_penalty": "Total penalty amount with currency and detailed breakdown",
    "breach_analysis": "Detailed analysis of breach terms with specific legal considerations",
    "summary": "Detailed breach terms review summary with specific findings and conclusions",
    "recommendations": [
        "Detailed breach recommendation 1 with specific action items and timeline",
        "Detailed breach recommendation 2 with specific action items and timeline",
        "Detailed breach recommendation 3 with specific action items and timeline",
        "Detailed breach recommendation 4 with specific action items and timeline"
    ]
}}

MANDATORY REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each breach clause
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific amounts, dates, percentages, and concrete details
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST provide realistic and detailed content even for simple contracts
9. You MUST include specific legal terms, breach types, and enforcement considerations

Remember: This is a MANDATORY breach terms review. You MUST output detailed analysis with SPECIFIC CONTENT in Chinese (中文). Even if the contract is simple, you MUST provide comprehensive analysis with realistic details in Chinese.
"""

    def create_general_review_prompt(self, contract_content: str) -> str:
        """创建通用审查提示词"""
        return f"""
You are a professional contract review assistant. You MUST perform a comprehensive general contract review and output detailed results.

IMPORTANT: You MUST output ALL content in Chinese (中文).

Contract Content:
{contract_content}

CRITICAL REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each review item
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific legal terms, commercial considerations, and practical implications
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST output ALL content in Chinese (中文)

MANDATORY OUTPUT FORMAT - COPY THIS EXACT STRUCTURE:
{{
    "overall_risk_level": "high|medium|low|none",
    "review_items": [
        {{
            "review_category": "Contract form/Completeness/Balance/Enforceability",
            "item_name": "Specific review item name with detailed identification",
            "item_content": "Detailed review content with specific analysis and legal considerations",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Specific general issue 1 with detailed description and legal implications",
                "Specific general issue 2 with detailed description and legal implications",
                "Specific general issue 3 with detailed description and legal implications",
                "Specific general issue 4 with detailed description and legal implications"
            ],
            "suggestions": [
                "Specific general suggestion 1 with actionable steps and timeline",
                "Specific general suggestion 2 with actionable steps and timeline",
                "Specific general suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "review_category": "Legal compliance/Commercial terms/Risk allocation",
            "item_name": "Another specific review item name with detailed identification",
            "item_content": "Another detailed review content with specific analysis and legal considerations",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Another general issue 1 with detailed description and legal implications",
                "Another general issue 2 with detailed description and legal implications",
                "Another general issue 3 with detailed description and legal implications"
            ],
            "suggestions": [
                "Another general suggestion 1 with actionable steps and timeline",
                "Another general suggestion 2 with actionable steps and timeline",
                "Another general suggestion 3 with actionable steps and timeline"
            ]
        }},
        {{
            "review_category": "Dispute resolution/Force majeure/Confidentiality",
            "item_name": "Third specific review item name with detailed identification",
            "item_content": "Third detailed review content with specific analysis and legal considerations",
            "risk_level": "high|medium|low|none",
            "issues": [
                "Third general issue 1 with detailed description and legal implications",
                "Third general issue 2 with detailed description and legal implications"
            ],
            "suggestions": [
                "Third general suggestion 1 with actionable steps and timeline",
                "Third general suggestion 2 with actionable steps and timeline"
            ]
        }}
    ],
    "summary": "Detailed general review summary with specific findings and conclusions",
    "recommendations": [
        "Detailed general recommendation 1 with specific action items and timeline",
        "Detailed general recommendation 2 with specific action items and timeline",
        "Detailed general recommendation 3 with specific action items and timeline",
        "Detailed general recommendation 4 with specific action items and timeline"
    ]
}}

MANDATORY REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
1. You MUST output valid JSON format ONLY
2. You MUST provide SPECIFIC DETAILED CONTENT for each review item
3. Use risk levels: high, medium, low, none
4. Each array MUST contain at least 3-5 detailed items with specific content
5. If contract content is insufficient, provide realistic placeholder content but maintain structure
6. You MUST include specific legal terms, commercial considerations, and practical implications
7. You MUST provide detailed content for each field, not just placeholder text
8. You MUST provide realistic and detailed content even for simple contracts
9. You MUST include specific legal requirements, commercial considerations, and practical implications

Remember: This is a MANDATORY general contract review. You MUST output detailed analysis with SPECIFIC CONTENT in Chinese (中文). Even if the contract is simple, you MUST provide comprehensive analysis with realistic details in Chinese.
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