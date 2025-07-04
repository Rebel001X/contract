"""
合同审计提示模板
基于LangChain的提示词模板集合
"""

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from typing import Dict, Any

class ContractAuditPrompts:
    """合同审计提示模板集合"""
    
    @staticmethod
    def get_basic_chat_template() -> ChatPromptTemplate:
        """基础对话模板"""
        template = """你是一个专业的合同审计助手，具有丰富的法律知识和合同分析经验。

你的职责：
1. 分析合同条款的合法性和合理性
2. 识别潜在的法律风险和问题
3. 提供专业的法律建议和解释
4. 回答用户关于合同的各类问题

合同内容：
{context}

聊天历史：
{chat_history}

用户问题：{question}

请基于合同内容和聊天历史，为用户提供准确、专业的回答。回答要：
- 简洁明了，重点突出
- 基于合同具体条款
- 指出潜在风险（如有）
- 提供实用建议（如适用）

如果问题超出合同范围，请明确说明。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "{question}")
        ])
    
    @staticmethod
    def get_risk_analysis_template() -> ChatPromptTemplate:
        """风险分析模板"""
        template = """你是一个专业的合同风险分析师。请对以下合同进行全面的风险分析。

合同内容：
{contract_content}

请从以下维度分析风险：
1. 法律合规风险
2. 商业风险
3. 财务风险
4. 操作风险
5. 声誉风险

对每个风险点，请说明：
- 风险描述
- 风险等级（高/中/低）
- 可能的影响
- 建议的应对措施

请以结构化的方式输出分析结果。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "请分析这份合同的风险")
        ])
    
    @staticmethod
    def get_clause_analysis_template() -> ChatPromptTemplate:
        """条款分析模板"""
        template = """你是一个专业的合同条款分析师。请对用户指定的合同条款进行详细分析。1. 条款含义和目的
2. 权利义务分配
3. 潜在的法律问题
4. 与其他条款的关系
5. 建议的修改意见（如适用）

请提供详细、专业的分析。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "请分析这个条款：{target_clause}")
        ])
    
    @staticmethod
    def get_comparison_template() -> ChatPromptTemplate:
        """合同对比模板"""
        template = """你是一个专业的合同对比分析师。请对比分析两份合同的关键差异。

合同A内容：
{contract_a}

合同B内容：
{contract_b}

请从以下维度进行对比：
1. 主要条款差异
2. 权利义务差异
3. 风险分配差异
4. 商业条款差异
5. 法律保护程度差异

请以表格或列表形式清晰展示对比结果。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "请对比这两份合同")
        ])
    
    @staticmethod
    def get_summary_template() -> ChatPromptTemplate:
        """合同摘要模板"""
        template = """你是一个专业的合同摘要专家。请为以下合同生成结构化的摘要。

合同内容：
{contract_content}

请生成包含以下内容的摘要：
1. 合同基本信息（类型、主体、标的等）
2. 主要条款概述
3. 关键权利义务
4. 重要时间节点
5. 风险提示要点
6. 建议关注事项

请以清晰的结构化格式输出。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "请为这份合同生成摘要")
        ])
    
    @staticmethod
    def get_legal_advice_template() -> ChatPromptTemplate:
        """法律建议模板"""
        template = """你是一个专业的法律顾问，专门提供合同相关的法律建议。

合同内容：
{contract_content}

用户问题：{question}

请提供专业的法律建议，包括：
1. 法律依据
2. 风险分析
3. 建议措施
4. 注意事项

请注意：
- 提供准确的法律信息
- 指出潜在的法律风险
- 建议在必要时咨询专业律师
- 避免提供具体的法律意见（除非明确要求）

请以专业、谨慎的态度提供建议。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "{question}")
        ])
    
    @staticmethod
    def get_negotiation_template() -> ChatPromptTemplate:
        """谈判建议模板"""
        template = """你是一个专业的合同谈判顾问。请为用户提供合同谈判的建议。

合同内容：
{contract_content}

用户立场：{user_position}

请提供谈判建议，包括：
1. 关键谈判点识别
2. 谈判策略建议
3. 底线设定建议
4. 让步空间分析
5. 风险控制建议

请基于合同内容和用户立场提供实用建议。"""
        
        return ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "请为我的谈判提供建议，我的立场是：{user_position}")
        ])

# 提示模板工厂
class PromptFactory:
    """提示模板工厂类"""
    
    @staticmethod
    def get_template(template_type: str) -> ChatPromptTemplate:
        """根据类型获取提示模板"""
        templates = {
            "basic": ContractAuditPrompts.get_basic_chat_template,
            "risk_analysis": ContractAuditPrompts.get_risk_analysis_template,
            "clause_analysis": ContractAuditPrompts.get_clause_analysis_template,
            "comparison": ContractAuditPrompts.get_comparison_template,
            "summary": ContractAuditPrompts.get_summary_template,
            "legal_advice": ContractAuditPrompts.get_legal_advice_template,
            "negotiation": ContractAuditPrompts.get_negotiation_template,
        }
        
        if template_type not in templates:
            raise ValueError(f"Unknown template type: {template_type}")
        
        return templates[template_type]()
    
    @staticmethod
    def get_all_templates() -> Dict[str, ChatPromptTemplate]:
        """获取所有提示模板"""
        return {
            "basic": ContractAuditPrompts.get_basic_chat_template(),
            "risk_analysis": ContractAuditPrompts.get_risk_analysis_template(),
            "clause_analysis": ContractAuditPrompts.get_clause_analysis_template(),
            "comparison": ContractAuditPrompts.get_comparison_template(),
            "summary": ContractAuditPrompts.get_summary_template(),
            "legal_advice": ContractAuditPrompts.get_legal_advice_template(),
            "negotiation": ContractAuditPrompts.get_negotiation_template(),
        } 