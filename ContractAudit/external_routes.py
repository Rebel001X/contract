from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks, Body
from typing import List, Optional, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from .models import (
    ContractAuditReview,
    create_contract_audit_review,
    get_contract_audit_review,
    list_contract_audit_reviews,
    update_contract_audit_review,
    delete_contract_audit_review,
    ReviewRule,
    bulk_create_review_rules,
    get_review_rule_by_external_id,
    list_review_rules,
    ConfirmReviewRuleResult,
    create_confirm_review_rule_result,
    bulk_create_confirm_review_rule_results,
    get_confirm_review_rule_results
)
from .config import get_session
import requests
import os
from fastapi.responses import StreamingResponse
import asyncio
import threading
import sys
import os
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import or_
import pytz
from fastapi.responses import JSONResponse
import traceback
import json

# Robust import for unified_response
try:
    from .utils import unified_response
except ImportError:
    try:
        from ContractAudit.utils import unified_response
    except ImportError:
        # Fallback: add parent dir to sys.path and try again
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from utils import unified_response

router = APIRouter()

# 异步数据库写入函数
async def save_review_rules_to_db(rules_data: list):
    """
    异步将审查规则数据保存到数据库
    """
    try:
        from .config import get_session
        db = next(get_session())
        
        # 过滤和转换数据
        valid_rules = []
        for rule in rules_data:
            # 检查是否已存在（根据外部ID）
            existing_rule = get_review_rule_by_external_id(db, rule.get('id'))
            if existing_rule:
                print(f"规则已存在，跳过: {rule.get('rule_name')}")
                continue
                
            # 转换数据格式
            rule_data = {
                'id': rule.get('id'),  # 使用外部ID作为本地ID
                'rule_name': rule.get('ruleName', ''),
                'type': rule.get('type', 0),
                'risk_level': rule.get('riskLevel', 0),
                'risk_attribution_id': rule.get('riskAttributionId'),
                'risk_attribution_name': rule.get('riskAttributionName'),
                'censored_search_engine': rule.get('censoredSearchEngine', 0),
                'rule_group_id': rule.get('ruleGroupId'),
                'rule_group_name': rule.get('ruleGroupName'),
                'include_rule': rule.get('includeRule'),
                'logic_rule_list': rule.get('logicRuleList'),
                'example_list': rule.get('exampleList'),
                'conditional_identifier': rule.get('conditionalIdentifier'),
                'condition_list': rule.get('conditionList'),
                'revise_opinion': rule.get('reviseOpinion'),
                'creator_id': rule.get('creatorId'),
                'creator_name': rule.get('creatorName'),
                'version': rule.get('version', 1),
                'update_time': rule.get('updateTime')
            }
            valid_rules.append(rule_data)
        
        if valid_rules:
            # 批量插入数据
            created_rules = bulk_create_review_rules(db, valid_rules)
            print(f"成功保存 {len(created_rules)} 条审查规则到数据库")
        else:
            print("没有新的审查规则需要保存")
            
    except Exception as e:
        print(f"保存审查规则到数据库失败: {e}")
    finally:
        db.close()

def run_async_db_save(rules_data: list):
    """
    在新线程中运行异步数据库保存
    """
    def save_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(save_review_rules_to_db(rules_data))
        finally:
            loop.close()
    
    thread = threading.Thread(target=save_in_thread)
    thread.daemon = True
    thread.start()

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

# Review Rule Schemas
class QueryReviewRuleDto(BaseModel):
    ruleGroupId: Optional[int] = Field(None, description="规则分组id")
    riskLevel: Optional[int] = Field(None, description="风险等级，0-低风险，1-中风险，2-高风险")
    ruleName: Optional[str] = Field(None, description="规则名称")
    type: Optional[int] = Field(None, description="类型，0-预设，1-自定义")
    pageNum: Optional[int] = Field(1, description="页码")
    pageSize: Optional[int] = Field(10, description="每页数量")

class BasePageRequest(BaseModel):
    pageNum: Optional[int] = Field(1, description="页码")
    pageSize: Optional[int] = Field(10, description="每页数量")

class BaseResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None

# CRUD 路由
@unified_response
@router.post("/contract-audit-reviews")
def create_review(review: ContractAuditReviewCreate, db: Session = Depends(get_session)):
    obj = create_contract_audit_review(db, review.dict())
    return obj

@unified_response
@router.get("/contract-audit-reviews/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_session)):
    obj = get_contract_audit_review(db, review_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Review not found")
    return obj

@unified_response
@router.get("/contract-audit-reviews")
def list_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    data = list_contract_audit_reviews(db, skip=skip, limit=limit)
    return {"items": data}

@unified_response
@router.put("/contract-audit-reviews/{review_id}")
def update_review(review_id: int, review: ContractAuditReviewUpdate, db: Session = Depends(get_session)):
    obj = update_contract_audit_review(db, review_id, review.dict(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Review not found")
    return obj

@unified_response
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

# @unified_response
# @router.get("/contract-audit-reviews/page")
# def paginated_reviews(
#     page: int = Query(1, ge=1, description="页码，从1开始"),
#     page_size: int = Query(10, ge=1, le=100, description="每页数量"),
#     session_id: Optional[str] = Query(None, description="会话ID过滤"),
#     risk_level: Optional[str] = Query(None, description="风险等级过滤"),
#     review_status: Optional[str] = Query(None, description="审查状态过滤"),
#     db: Session = Depends(get_session)
# ):
#     skip = (page - 1) * page_size
#     query = db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False)
#     
#     # 添加过滤条件
#     if session_id:
#         query = query.filter(ContractAuditReview.ext_json.contains({"session_id": session_id}))
#     if risk_level:
#         query = query.filter(ContractAuditReview.risk_level == risk_level)
#     if review_status:
#         query = query.filter(ContractAuditReview.review_status == review_status)
#     
#     total = query.count()
#     items = query.order_by(ContractAuditReview.updated_at.desc()).offset(skip).limit(page_size).all()
#     max_page = (total + page_size - 1) // page_size if page_size else 1
#     return {"total": total, "items": items, "maxPage": max_page}

@unified_response
@router.get("/contract-audit-reviews/by-session/{session_id}")
def get_reviews_by_session(session_id: str, db: Session = Depends(get_session)):
    """
    根据会话ID获取审查记录
    """
    reviews = db.query(ContractAuditReview).filter(
        ContractAuditReview.ext_json.contains({"session_id": session_id}),
        ContractAuditReview.is_deleted == False
    ).order_by(ContractAuditReview.created_at.desc()).all()
    
    return {"items": reviews}

@unified_response
@router.get("/contract-audit-reviews/stats")
def get_review_stats(
    session_id: Optional[str] = Query(None, description="会话ID"),
    db: Session = Depends(get_session)
):
    """
    获取审查记录统计信息
    """
    query = db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False)
    
    if session_id:
        query = query.filter(ContractAuditReview.ext_json.contains({"session_id": session_id}))
    
    # 统计各风险等级数量
    risk_stats = db.query(
        ContractAuditReview.risk_level,
        db.func.count(ContractAuditReview.id).label('count')
    ).filter(ContractAuditReview.is_deleted == False).group_by(ContractAuditReview.risk_level).all()
    
    # 统计各审查状态数量
    status_stats = db.query(
        ContractAuditReview.review_status,
        db.func.count(ContractAuditReview.id).label('count')
    ).filter(ContractAuditReview.is_deleted == False).group_by(ContractAuditReview.review_status).all()
    
    # 总体统计
    total_count = query.count()
    high_risk_count = query.filter(ContractAuditReview.risk_level == "高").count()
    medium_risk_count = query.filter(ContractAuditReview.risk_level == "中").count()
    low_risk_count = query.filter(ContractAuditReview.risk_level == "低").count()
    passed_count = query.filter(ContractAuditReview.review_status == "通过").count()
    failed_count = query.filter(ContractAuditReview.review_status == "不通过").count()
    
    return {"code": 0, "data": {
        "total_count": total_count,
        "risk_level_stats": {item.risk_level: item.count for item in risk_stats},
        "review_status_stats": {item.review_status: item.count for item in status_stats},
        "summary": {
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "passed_count": passed_count,
            "failed_count": failed_count
        }
    }, "maxPage": 1, "message": ""}

@router.get("/hetong-docx")
async def get_hetong_docx():
    """
    获取D盘的hetong.docx文件并解析为文本内容
    """
    file_path = r"D:\abc4.docx"
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # 尝试解析docx文件内容
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            # docx文件是zip格式，包含word/document.xml
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 读取文档内容
                xml_content = zip_file.read('word/document.xml')
                
                # 解析XML
                root = ET.fromstring(xml_content)
                
                # 提取所有文本内容
                text_content = []
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        text_content.append(elem.text.strip())
                
                full_text = "\n".join(text_content)
                
                return {
                    "filename": file_name,
                    "size": file_size,
                    "path": file_path,
                    "text_content": full_text,
                    "message": "文件解析成功"
                }
                
        except Exception as parse_error:
            # 如果解析失败，返回原始二进制内容
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            return {
                "filename": file_name,
                "size": file_size,
                "path": file_path,
                "content": file_content.hex(),
                "parse_error": str(parse_error),
                "message": "文件获取成功（解析失败，返回原始内容）"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

@router.post("/external/rag-stream")
async def external_rag_stream(request: Request):
    """
    代理调用外部Docker服务的RAG流式接口，自动拼接prompt模板
    """
    try:
        # 获取请求数据
        data = await request.json()
        contract_content = data.get("contract_content")
        if not contract_content:
            raise HTTPException(status_code=400, detail="contract_content参数必填")

        # Prompt模板
        prompt_template = (
            "你是一名专业的合同审查助手。请根据以下审查规则，对给定合同内容进行风险分级，并输出每一类对应的项目。分级标准如下：\n"
            "- 高风险项目\n"
            "- 中风险项目\n"
            "- 低风险项目\n"
            "- 通过项目\n\n"
            "请严格按照如下格式输出：\n\n"
            "高风险项目：\n- 项目1：简要说明\n- 项目2：简要说明\n\n"
            "中风险项目：\n- 项目1：简要说明\n\n"
            "低风险项目：\n- 项目1：简要说明\n\n"
            "通过项目：\n- 项目1：简要说明\n\n"
            "请直接输出分级结果，无需解释分析过程。\n\n"
            "合同内容如下：\n{contract_content}"
        )
        final_prompt = prompt_template.format(contract_content=contract_content)

        # 调用外部服务
        external_url = "http://localhost:9621/query/stream"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "query": final_prompt,
            "stream": True
        }
        response = requests.post(
            external_url,
            headers=headers,
            json=payload,
            stream=True
        )
        if response.status_code == 200:
            def event_stream():
                for line in response.iter_lines():
                    if line:
                        yield line + b'\n'
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"外部服务调用失败: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理调用失败: {str(e)}")

@unified_response
@router.post("/external/review-rules", response_model=BaseResponse)
async def get_review_rule_list(query_dto: QueryReviewRuleDto, background_tasks: BackgroundTasks):
    """
    获取审查规则列表，代理调用外部API，并异步保存到数据库
    外部API地址: http://172.20.14.29:8080/contract/ReviewRuleController/getReviewRuleListUsingPOST
    """
    try:
        # 构建请求参数
        payload = query_dto.dict(exclude_none=True)
        
        # 调用外部API
        external_url = "http://172.20.14.29:8080/review/rule/get/list/1.0"
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            external_url,
            headers=headers,
            json=payload,
            timeout=30  # 设置30秒超时
        )
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            print(f"外部API调用成功: {result}")  # 打印返回内容到终端
            
            # 异步保存数据到数据库
            if result.get('code') == 200 and result.get('data'):
                rules_data = result.get('data', {}).get('list', [])
                if rules_data:
                    # 使用后台任务异步保存到数据库
                    background_tasks.add_task(run_async_db_save, rules_data)
                    print(f"已启动后台任务保存 {len(rules_data)} 条审查规则到数据库")
                else:
                    print("没有审查规则数据需要保存")
            
            return result
        else:
            print(f"外部API调用失败: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"外部API调用失败: {response.text}"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="外部API调用超时")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="无法连接到外部API服务")
    except Exception as e:
        print(f"获取审查规则列表异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取审查规则列表失败: {str(e)}")

@unified_response
@router.post("/external/review-rules/sync", response_model=BaseResponse)
async def sync_review_rules_to_db(background_tasks: BackgroundTasks):
    """
    手动同步审查规则到数据库
    """
    try:
        # 调用外部API获取所有规则
        external_url = "http://172.20.14.29:8080/review/rule/get/list/1.0"
        headers = {
            "Content-Type": "application/json"
        }
        
        # 获取所有规则（不分页）
        payload = {
            "pageNum": 1,
            "pageSize": 1000  # 获取大量数据
        }
        
        response = requests.post(
            external_url,
            headers=headers,
            json=payload,
            timeout=60  # 设置60秒超时
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200 and result.get('data'):
                rules_data = result.get('data', {}).get('list', [])
                if rules_data:
                    # 使用后台任务异步保存到数据库
                    background_tasks.add_task(run_async_db_save, rules_data)
                    return {
                        "code": 200,
                        "message": f"已启动后台任务同步 {len(rules_data)} 条审查规则到数据库",
                        "data": {"total_rules": len(rules_data)}
                    }
                else:
                    return {
                        "code": 200,
                        "message": "没有审查规则数据需要同步",
                        "data": {"total_rules": 0}
                    }
            else:
                raise HTTPException(status_code=400, detail="外部API返回数据格式错误")
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"外部API调用失败: {response.text}"
            )
            
    except Exception as e:
        print(f"同步审查规则异常: {e}")
        raise HTTPException(status_code=500, detail=f"同步审查规则失败: {str(e)}")

@unified_response
@router.get("/review-rules")
def get_saved_review_rules(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_session)
):
    """
    获取已保存到数据库的审查规则列表
    """
    try:
        rules = list_review_rules(db, skip=skip, limit=limit)
        return {"items": [
            {
                "id": rule.id,
                "rule_name": rule.rule_name,
                "type": rule.type,
                "risk_level": rule.risk_level,
                "risk_attribution_id": rule.risk_attribution_id,
                "risk_attribution_name": rule.risk_attribution_name,
                "censored_search_engine": rule.censored_search_engine,
                "rule_group_id": rule.rule_group_id,
                "rule_group_name": rule.rule_group_name,
                "include_rule": rule.include_rule,
                "logic_rule_list": rule.logic_rule_list,
                "example_list": rule.example_list,
                "conditional_identifier": rule.conditional_identifier,
                "condition_list": rule.condition_list,
                "revise_opinion": rule.revise_opinion,
                "creator_id": rule.creator_id,
                "creator_name": rule.creator_name,
                "version": rule.version,
                "update_time": rule.update_time.isoformat() if rule.update_time else None
            }
            for rule in rules
        ]}
    except Exception as e:
        print(f"获取保存的审查规则异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取审查规则失败: {str(e)}")

@unified_response
@router.get("/review-rules/count")
def get_review_rules_count(db: Session = Depends(get_session)):
    """
    获取数据库中审查规则的总数
    """
    try:
        count = db.query(ReviewRule).count()
        return {
            "code": 200,
            "message": "获取成功",
            "data": {"total_count": count}
        }
    except Exception as e:
        print(f"获取审查规则数量异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取审查规则数量失败: {str(e)}")

# 新增：用户勾选审查规则的数据模型
class SelectedReviewRuleDto(BaseModel):
    rule_id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    type: int = Field(..., description="规则类型，0-预设，1-自定义")
    risk_level: int = Field(..., description="风险等级，0-低风险，1-中风险，2-高风险")
    risk_attribution_id: Optional[int] = Field(None, description="风险归属id")
    risk_attribution_name: Optional[str] = Field(None, description="风险归属名")
    censored_search_engine: int = Field(..., description="审查引擎，0-大模型 1-规则推理")
    rule_group_id: Optional[int] = Field(None, description="规则分组id")
    rule_group_name: Optional[str] = Field(None, description="规则分组名")
    include_rule: Optional[str] = Field(None, description="包含规则")
    logic_rule_list: Optional[list] = Field(None, description="逻辑规则列表")
    example_list: Optional[list] = Field(None, description="例子列表")
    conditional_identifier: Optional[str] = Field(None, description="条件判断符")
    condition_list: Optional[list] = Field(None, description="条件列表")
    revise_opinion: Optional[str] = Field(None, description="修改意见")
    creator_id: Optional[int] = Field(None, description="创建者id")
    creator_name: Optional[str] = Field(None, description="创建者姓名")
    version: int = Field(default=1, description="版本号")
    update_time: Optional[str] = Field(None, description="更新时间")

class SaveSelectedRulesRequest(BaseModel):
    selected_rules: List[SelectedReviewRuleDto] = Field(..., description="勾选的审查规则列表")
    user_id: Optional[str] = Field(None, description="用户ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="描述信息")

class SaveSelectedRulesResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None

@unified_response
@router.post("/review-rules/save-selected", response_model=SaveSelectedRulesResponse)
async def save_selected_review_rules(
    request: SaveSelectedRulesRequest, 
    background_tasks: BackgroundTasks
):
    """
    保存用户勾选的审查规则到数据库
    """
    try:
        # 转换数据格式
        rules_data = []
        for rule in request.selected_rules:
            rule_data = {
                'id': rule.rule_id,  # 使用外部ID作为本地ID
                'rule_name': rule.rule_name,
                'type': rule.type,
                'risk_level': rule.risk_level,
                'risk_attribution_id': rule.risk_attribution_id,
                'risk_attribution_name': rule.risk_attribution_name,
                'censored_search_engine': rule.censored_search_engine,
                'rule_group_id': rule.rule_group_id,
                'rule_group_name': rule.rule_group_name,
                'include_rule': rule.include_rule,
                'logic_rule_list': rule.logic_rule_list,
                'example_list': rule.example_list,
                'conditional_identifier': rule.conditional_identifier,
                'condition_list': rule.condition_list,
                'revise_opinion': rule.revise_opinion,
                'creator_id': rule.creator_id,
                'creator_name': rule.creator_name,
                'version': rule.version,
                'update_time': rule.update_time
            }
            rules_data.append(rule_data)
        
        if not rules_data:
            return SaveSelectedRulesResponse(
                code=400,
                message="没有选择任何审查规则",
                data={"saved_count": 0}
            )
        
        # 使用后台任务异步保存到数据库
        background_tasks.add_task(run_async_db_save, rules_data)
        
        return SaveSelectedRulesResponse(
            code=200,
            message=f"已启动后台任务保存 {len(rules_data)} 条勾选的审查规则到数据库",
            data={
                "selected_count": len(request.selected_rules),
                "saved_count": len(rules_data),
                "user_id": request.user_id,
                "project_name": request.project_name,
                "description": request.description
            }
        )
        
    except Exception as e:
        print(f"保存勾选审查规则异常: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"保存勾选审查规则失败: {str(e)}"
        )

@unified_response
@router.post("/review-rules/save-selected-sync", response_model=SaveSelectedRulesResponse)
async def save_selected_review_rules_sync(request: SaveSelectedRulesRequest, db: Session = Depends(get_session)):
    """
    同步保存选中的审查规则到数据库
    """
    try:
        # 获取或创建规则组
        rule_group_name = request.description or "默认规则组"
        
        # 批量创建规则
        created_rules = []
        for rule_dto in request.selected_rules:
            rule_data = {
                'id': rule_dto.rule_id,  # 使用外部ID
                'rule_name': rule_dto.rule_name,
                'type': rule_dto.type,
                'risk_level': rule_dto.risk_level,
                'risk_attribution_id': rule_dto.risk_attribution_id,
                'risk_attribution_name': rule_dto.risk_attribution_name,
                'censored_search_engine': rule_dto.censored_search_engine,
                'rule_group_id': rule_dto.rule_group_id,
                'rule_group_name': rule_dto.rule_group_name or rule_group_name,
                'include_rule': rule_dto.include_rule,
                'logic_rule_list': rule_dto.logic_rule_list,
                'example_list': rule_dto.example_list,
                'conditional_identifier': rule_dto.conditional_identifier,
                'condition_list': rule_dto.condition_list,
                'revise_opinion': rule_dto.revise_opinion,
                'creator_id': rule_dto.creator_id,
                'creator_name': rule_dto.creator_name,
                'version': rule_dto.version,
                'update_time': rule_dto.update_time
            }
            
            # 检查是否已存在
            existing_rule = get_review_rule_by_external_id(db, rule_dto.rule_id)
            if existing_rule:
                print(f"规则已存在，跳过: {rule_dto.rule_name}")
                continue
                
            created_rule = bulk_create_review_rules(db, [rule_data])
            if created_rule:
                created_rules.extend(created_rule)
        
        return SaveSelectedRulesResponse(
            code=200,
            message=f"成功保存 {len(created_rules)} 条审查规则",
            data={
                "saved_count": len(created_rules),
                "rule_ids": [rule.id for rule in created_rules],
                "user_id": request.user_id,
                "project_name": request.project_name
            }
        )
        
    except Exception as e:
        print(f"保存审查规则失败: {e}")
        return SaveSelectedRulesResponse(
            code=500,
            message=f"保存失败: {str(e)}",
            data=None
        )

# 新增：Confirm接口审查结果相关API

class ConfirmReviewSessionOut(BaseModel):
    """Confirm审查会话输出模型"""
    id: int
    session_id: str
    user_id: Optional[str] = None
    project_name: Optional[str] = None
    review_stage: Optional[str] = None
    review_rules_count: int
    total_issues: int
    high_risk_items: int
    medium_risk_items: int
    low_risk_items: int
    overall_risk_level: str
    overall_summary: Optional[str] = None
    confidence_score: int
    critical_recommendations: Optional[list] = None
    action_items: Optional[list] = None
    processing_time: int
    model_used: str
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

class ConfirmReviewRuleResultOut(BaseModel):
    """Confirm规则审查结果输出模型"""
    id: int
    session_id: str
    rule_id: int
    rule_name: str
    rule_index: int
    review_result: str
    risk_level: str
    matched_content: Optional[List[Any]] = None
    analysis: Optional[List[Any]] = None
    issues: Optional[List[Any]] = None
    suggestions: Optional[List[Any]] = None
    confidence_score: int
    user_feedback: Optional[int] = None  # 0=点踩, 1=点赞, null=无反馈
    feedback_suggestion: Optional[str] = None  # 反馈建议内容
    is_approved: Optional[bool] = None  # 审核是否通过标志
    contract_id: Optional[str] = None  # 合同ID
    contract_name: Optional[str] = None  # 合同名称
    risk_attribution_id: Optional[int] = None  # 风险归属ID
    contract_type: Optional[str] = None  # 合同类型
    risk_attribution_name: Optional[str] = None  # 新增：风险归属名
    manual_correction_en: Optional[str] = None  # 新增：人工修正英文
    error_type: Optional[str] = None  # 新增：错误类型
    audit_quality: Optional[int] = None  # 新增：审计质量评分
    created_at: Optional[datetime] = None

    @validator('issues', 'suggestions', 'analysis', 'matched_content', pre=True)
    def parse_json_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                loaded = json.loads(v)
                if isinstance(loaded, list):
                    return loaded
                return [loaded]
            except Exception:
                # 普通字符串直接包一层
                return [v]
        if isinstance(v, list):
            return v
        return [v]

    class Config:
        orm_mode = True
        
    @classmethod
    def from_orm(cls, obj):
        """自定义序列化方法"""
        data = {
            'id': obj.id,
            'session_id': obj.session_id,
            'rule_id': obj.rule_id,
            'rule_name': obj.rule_name,
            'rule_index': obj.rule_index,
            'review_result': obj.review_result,
            'risk_level': obj.risk_level,
            'matched_content': obj.matched_content,
            'analysis': obj.analysis,
            'issues': obj.issues,
            'suggestions': obj.suggestions,
            'confidence_score': obj.confidence_score,
            'user_feedback': obj.user_feedback,
            'feedback_suggestion': obj.feedback_suggestion,
            'is_approved': obj.is_approved,
            'contract_id': obj.contract_id,
            'contract_name': obj.contract_name,
            'risk_attribution_id': getattr(obj, 'risk_attribution_id', None),
            'risk_attribution_name': getattr(obj, 'risk_attribution_name', None),
            'riskAttributionId': getattr(obj, 'risk_attribution_id', None),
            'riskAttributionName': getattr(obj, 'risk_attribution_name', None),
            'contract_type': getattr(obj, 'contract_type', None),
            'manual_correction_en': getattr(obj, 'manual_correction_en', None),  # 新增
            'error_type': getattr(obj, 'error_type', None),  # 新增
            'audit_quality': getattr(obj, 'audit_quality', None),  # 新增
            'created_at': obj.created_at.isoformat() if obj.created_at else None
        }
        return cls(**data)

class ConfirmReviewRuleResultIn(BaseModel):
    """Confirm规则审查结果输入模型（创建时使用）"""
    session_id: str
    rule_id: int
    rule_name: str
    rule_index: int
    review_result: str
    risk_level: str
    matched_content: Optional[str] = None
    analysis: Optional[str] = None
    issues: Optional[list] = None
    suggestions: Optional[list] = None
    confidence_score: int = 50
    user_feedback: Optional[int] = None  # 0=点踩, 1=点赞, null=无反馈
    feedback_suggestion: Optional[str] = None  # 反馈建议内容
    is_approved: Optional[bool] = None  # 审核是否通过标志
    contract_id: Optional[str] = None  # 合同ID
    contract_name: Optional[str] = None  # 合同名称
    risk_attribution_id: Optional[int] = None  # 风险归属ID
    contract_type: Optional[str] = None  # 合同类型

class ConfirmReviewDetailOut(BaseModel):
    """Confirm审查详情输出模型"""
    session: ConfirmReviewSessionOut
    rule_results: List[ConfirmReviewRuleResultOut]

@unified_response
@router.get("/confirm-reviews")
def get_confirm_review_sessions(
    user_id: Optional[str] = Query(None, description="用户ID"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_session)
):
    """
    获取Confirm审查会话列表
    """
    from .models import list_confirm_review_sessions
    sessions = list_confirm_review_sessions(db, user_id=user_id, skip=skip, limit=limit)
    return {"items": sessions}

@unified_response
@router.get("/confirm-reviews/{session_id}", response_model=ConfirmReviewDetailOut)
def get_confirm_review_detail(session_id: str, db: Session = Depends(get_session)):
    """
    获取指定会话的Confirm审查详情
    """
    from .models import get_confirm_review_session, get_confirm_review_rule_results
    
    session = get_confirm_review_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="审查会话不存在")
    
    rule_results = get_confirm_review_rule_results(db, session_id)
    
    return ConfirmReviewDetailOut(session=session, rule_results=rule_results)

@unified_response
@router.get("/confirm-reviews/statistics")
def get_confirm_review_statistics(
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_session)
):
    """
    获取Confirm审查统计信息
    """
    from .models import get_confirm_review_statistics
    stats = get_confirm_review_statistics(db, user_id=user_id)
    return {
        "code": 200,
        "message": "获取统计信息成功",
        "data": stats
    }

@unified_response
@router.delete("/confirm-reviews/{session_id}")
def delete_confirm_review_session(session_id: str, db: Session = Depends(get_session)):
    """
    删除Confirm审查会话（软删除）
    """
    from .models import get_confirm_review_session, ConfirmReviewRuleResult
    
    session = get_confirm_review_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="审查会话不存在")
    
    # 软删除会话
    session.status = "deleted"
    db.commit()
    
    # 删除相关的规则结果
    rule_results = db.query(ConfirmReviewRuleResult).filter(
        ConfirmReviewRuleResult.session_id == session_id
    ).all()
    
    for result in rule_results:
        db.delete(result)
    
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": {
            "deleted_session_id": session_id,
            "deleted_rule_results_count": len(rule_results)
        }
    }

# Create
@unified_response
@router.post("/confirm-review-rule-result", response_model=ConfirmReviewRuleResultOut)
def create_confirm_rule_result(result: ConfirmReviewRuleResultIn, db: Session = Depends(get_session)):
    result_data = result.dict(exclude_unset=True)
    # 确保contract_name写入
    if 'contract_name' not in result_data:
        result_data['contract_name'] = None
    created = create_confirm_review_rule_result(db, result_data)
    return created

# Read by id
@unified_response
@router.get("/confirm-review-rule-result/{id}", response_model=ConfirmReviewRuleResultOut)
def get_confirm_rule_result(id: int, db: Session = Depends(get_session)):
    obj = db.query(ConfirmReviewRuleResult).filter(ConfirmReviewRuleResult.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="规则结果不存在")
    return ConfirmReviewRuleResultOut.from_orm(obj)

# Update by id
@unified_response
@router.put("/confirm-review-rule-result/{id}", response_model=ConfirmReviewRuleResultOut)
def update_confirm_rule_result(id: int, result: ConfirmReviewRuleResultOut, db: Session = Depends(get_session)):
    obj = db.query(ConfirmReviewRuleResult).filter(ConfirmReviewRuleResult.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="规则结果不存在")
    for k, v in result.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

# Delete by id
@unified_response
@router.delete("/confirm-review-rule-result/{id}")
def delete_confirm_rule_result(id: int, db: Session = Depends(get_session)):
    obj = db.query(ConfirmReviewRuleResult).filter(ConfirmReviewRuleResult.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="规则结果不存在")
    db.delete(obj)
    db.commit()
    return {"code": 200, "message": "删除成功", "id": id}

# 用户反馈接口
class UserFeedbackRequest(BaseModel):
    rule_id: int = Field(..., description="规则ID")
    feedback: int = Field(..., description="用户反馈: 0=点踩, 1=点赞")
    feedback_suggestion: Optional[str] = Field(None, description="反馈建议内容")
    is_approved: Optional[bool] = Field(None, description="审核是否通过标志")
    contract_id: Optional[str] = Field(None, description="合同ID")
    manual_correction_en: Optional[str] = Field(None, description="人工修正英文")  # 新增
    error_type: Optional[str] = Field(None, description="错误类型")  # 新增
    audit_quality: Optional[int] = Field(None, ge=1, le=5, description="审计质量评分(1-5分)")  # 新增

@unified_response
@router.post("/confirm-review-rule-result/feedback")
def update_user_feedback_by_rule_id(request: UserFeedbackRequest = Body(...), db: Session = Depends(get_session)):
    """
    用 rule_id 点赞/点踩（支持反馈建议和审核状态）
    """
    rule_id = getattr(request, 'rule_id', None)
    feedback = getattr(request, 'feedback', None)
    feedback_suggestion = getattr(request, 'feedback_suggestion', None)
    is_approved = getattr(request, 'is_approved', None)
    
    if rule_id is None or feedback not in [0, 1]:
        raise HTTPException(status_code=400, detail="必须提供 rule_id 和 feedback(0或1)")
    
    obj = db.query(ConfirmReviewRuleResult).filter(ConfirmReviewRuleResult.rule_id == rule_id).order_by(ConfirmReviewRuleResult.id.desc()).first()
    if not obj:
        raise HTTPException(status_code=404, detail="规则结果不存在")
    
    # 更新用户反馈
    obj.user_feedback = feedback
    
    # 更新反馈建议（如果提供）
    if feedback_suggestion is not None:
        obj.feedback_suggestion = feedback_suggestion
    
    # 更新审核状态（如果提供）
    if is_approved is not None:
        obj.is_approved = is_approved
    
    # 更新人工修正英文（如果提供）
    manual_correction_en = getattr(request, 'manual_correction_en', None)
    if manual_correction_en is not None:
        obj.manual_correction_en = manual_correction_en
    
    # 更新错误类型（如果提供）
    error_type = getattr(request, 'error_type', None)
    if error_type is not None:
        obj.error_type = error_type
    
    # 更新审计质量评分（如果提供）
    audit_quality = getattr(request, 'audit_quality', None)
    if audit_quality is not None:
        obj.audit_quality = audit_quality
    
    db.commit()
    db.refresh(obj)
    
    feedback_text = "点赞" if feedback == 1 else "点踩"
    return {
        "code": 200,
        "message": f"{feedback_text}成功",
        "user_feedback": obj.user_feedback,
        "feedback_suggestion": obj.feedback_suggestion,
        "is_approved": obj.is_approved,
        "manual_correction_en": obj.manual_correction_en,  # 新增
        "error_type": obj.error_type,  # 新增
        "audit_quality": obj.audit_quality,  # 新增
        "rule_id": rule_id,
        "id": obj.id
    }

# 分页查询接口
@unified_response
@router.get("/confirm-review-rule-results")
def list_confirm_rule_results(
    session_id: Optional[str] = Query(None),
    rule_id: Optional[int] = Query(None),
    rule_name: Optional[str] = Query(None),
    review_result: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_session)
):
    query = db.query(ConfirmReviewRuleResult)
    if session_id:
        query = query.filter(ConfirmReviewRuleResult.session_id == session_id)
    if rule_id:
        query = query.filter(ConfirmReviewRuleResult.rule_id == rule_id)
    if rule_name:
        query = query.filter(ConfirmReviewRuleResult.rule_name.like(f"%{rule_name}%"))
    if review_result:
        query = query.filter(ConfirmReviewRuleResult.review_result == review_result)
    results = query.order_by(ConfirmReviewRuleResult.id.desc()).offset(skip).limit(limit).all()
    return {"items": [ConfirmReviewRuleResultOut.from_orm(obj) for obj in results]}

class PaginatedConfirmReviewRuleResult(BaseModel):
    total: int
    items: List['ConfirmReviewRuleResultOut']

class ContractInfo(BaseModel):
    """合同信息模型"""
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None

@router.get("/confirm-review-rule-results/page")
def paginated_confirm_review_rule_results(
    rule_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    review_result: Optional[str] = Query(None),
    rule_name: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    contract_name: Optional[str] = Query(None),
    risk_attribution_id: Optional[int] = Query(None),
    contract_type: Optional[str] = Query(None),
    created_time: Optional[str] = Query(None, description="创建时间，格式YYYY-MM-DD HH:MM:SS"),
    created_at: Optional[str] = Query(None, description="创建时间（兼容参数），格式YYYY-MM-DD HH:MM:SS"),
    keyword: Optional[str] = Query(None, description="关键字模糊查找"),
    skip: Optional[int] = Query(None, ge=0, description="跳过记录数"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="每页数量"),
    page: Optional[int] = Query(None, description="页码（兼容参数）"),
    pageSize: Optional[int] = Query(None, description="每页数量（兼容参数）"),
    db: Session = Depends(get_session)
):
    if page is not None and pageSize is not None:
        skip = (page - 1) * pageSize
        limit = pageSize
    if skip is None:
        skip = 0
    if limit is None:
        limit = 20
    query = db.query(ConfirmReviewRuleResult)
    if rule_id:
        query = query.filter(ConfirmReviewRuleResult.rule_id == rule_id)
    if session_id:
        query = query.filter(ConfirmReviewRuleResult.session_id == session_id)
    if review_result:
        query = query.filter(ConfirmReviewRuleResult.review_result == review_result)
    if rule_name:
        query = query.filter(ConfirmReviewRuleResult.rule_name == rule_name)
    if risk_level:
        query = query.filter(ConfirmReviewRuleResult.risk_level == risk_level)
    if contract_id:
        query = query.filter(ConfirmReviewRuleResult.contract_id == contract_id)
    if contract_name:
        query = query.filter(ConfirmReviewRuleResult.contract_name == contract_name)
    if risk_attribution_id:
        query = query.filter(ConfirmReviewRuleResult.risk_attribution_id == risk_attribution_id)
    if contract_type:
        query = query.filter(ConfirmReviewRuleResult.contract_type == contract_type)
    # 处理时间过滤，支持 created_time 和 created_at 两个参数
    time_filter = created_time or created_at
    if time_filter:
        try:
            # 支持多种时间格式
            dt = None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(time_filter, fmt)
                    break
                except ValueError:
                    continue
            
            if dt:
                # 先加中国时区，再去掉时区，确保与数据库无时区字段比较
                china_tz = pytz.timezone('Asia/Shanghai')
                if dt.tzinfo is None:
                    dt = china_tz.localize(dt)
                # 去掉时区信息
                dt = dt.replace(tzinfo=None)
                # 根据格式类型进行不同的过滤
                if len(time_filter) == 19:  # YYYY-MM-DD HH:MM:SS - 精确到秒
                    start_time = dt
                    end_time = dt + timedelta(seconds=1)
                    query = query.filter(
                        ConfirmReviewRuleResult.created_at >= start_time,
                        ConfirmReviewRuleResult.created_at < end_time
                    )
                elif len(time_filter) == 16:  # YYYY-MM-DD HH:MM - 精确到分钟
                    start_time = dt
                    end_time = dt + timedelta(minutes=1)
                    query = query.filter(
                        ConfirmReviewRuleResult.created_at >= start_time,
                        ConfirmReviewRuleResult.created_at < end_time
                    )
                elif len(time_filter) == 10:  # YYYY-MM-DD - 精确到天
                    start_time = dt
                    end_time = dt + timedelta(days=1)
                    query = query.filter(
                        ConfirmReviewRuleResult.created_at >= start_time,
                        ConfirmReviewRuleResult.created_at < end_time
                    )
        except Exception as e:
            print(f"时间过滤解析错误: {e}, 时间参数: {time_filter}")
            # 不抛出异常，继续查询但不进行时间过滤
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                ConfirmReviewRuleResult.rule_name.ilike(like_pattern),
                ConfirmReviewRuleResult.analysis.ilike(like_pattern),
                ConfirmReviewRuleResult.matched_content.ilike(like_pattern)
            )
        )
    total = query.count()
    results = query.order_by(ConfirmReviewRuleResult.id.desc()).offset(skip).limit(limit).all()
    max_page = (total + limit - 1) // limit if limit > 0 else 1
    return {
        "code": 0,
        "data": [ConfirmReviewRuleResultOut.from_orm(obj) for obj in results],
        "maxPage": max_page,
        "message": "",
        "total": total
    }
@router.get("/confirm-review-rule-results/by-contract")
def get_rule_results_by_contract_id(
    contract_id: Optional[str] = Query(None, description="合同ID，可选"),
    db: Session = Depends(get_session)
):
    """
    获取合同信息列表，只返回contract_id和contract_name
    """
    query = db.query(ConfirmReviewRuleResult.contract_id, ConfirmReviewRuleResult.contract_name)
    if contract_id:
        query = query.filter(ConfirmReviewRuleResult.contract_id == contract_id)
    # 过滤掉contract_id为null的记录
    query = query.filter(ConfirmReviewRuleResult.contract_id.isnot(None))
    query = query.filter(ConfirmReviewRuleResult.contract_id != '')
    results = query.distinct().order_by(ConfirmReviewRuleResult.contract_id.desc()).all()
    data = [ContractInfo(contract_id=result[0], contract_name=result[1]) for result in results]
    return {
        "code": 0,
        "data": data,
        "maxPage": 1,
        "message": ""
    }

@router.get("/confirm-review-rule-results/created-times")
def get_confirm_rule_result_created_times(
    contract_id: str = Query(None, description="合同ID，可选"),
    db: Session = Depends(get_session)
):
    """
    获取所有规则结果的去重创建时间（精确到秒，可按合同ID筛选，用于下拉筛选）
    """
    query = db.query(ConfirmReviewRuleResult.created_at)
    if contract_id:
        query = query.filter(ConfirmReviewRuleResult.contract_id == contract_id)
    datetimes = query.distinct().order_by(ConfirmReviewRuleResult.created_at.desc()).all()
    datetime_list = [d[0].strftime('%Y-%m-%d %H:%M:%S') for d in datetimes if d[0] is not None]
    return {
        "code": 0,
        "data": datetime_list,  # 精确到秒
        "maxPage": 1,
        "message": ""
    }

@unified_response
@router.get("/test-unified-response")
def test_unified_response():
    """
    测试统一响应格式装饰器
    """
    return "hello world"

# 新增的API端点
class DocParserRequest(BaseModel):
    """文档解析请求模型"""
    contract_id: str = Field(..., description="合同ID")
    url: str = Field(..., description="文档URL")

class DocParserResponse(BaseModel):
    """文档解析响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[dict] = Field(None, description="解析结果数据")

class ContractViewRequest(BaseModel):
    """合同查看请求模型"""
    contract_id: Optional[str] = Field(None, description="合同ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    query: Optional[str] = Field(None, description="查询内容")
    user_id: Optional[str] = Field(None, description="用户ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    review_type: Optional[str] = Field("comprehensive", description="审查类型")
    risk_level_filter: Optional[str] = Field("all", description="风险等级过滤")
    include_details: Optional[bool] = Field(True, description="是否包含详细信息")

class ContractViewResponse(BaseModel):
    """合同查看响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[dict] = Field(None, description="查询结果数据")

@router.post("/v1/doc_parser", response_model=DocParserResponse)
async def doc_parser(request: DocParserRequest):
    """
    文档解析接口
    
    根据提供的合同ID和URL进行文档解析
    """
    try:
        import requests
        from urllib.parse import urlparse
        import hashlib
        
        # 验证URL格式
        parsed_url = urlparse(request.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("无效的URL格式")
        
        # 生成会话ID
        session_id = hashlib.md5(f"{request.contract_id}_{request.url}".encode()).hexdigest()
        
        # 尝试下载文档内容
        try:
            response = requests.get(request.url, timeout=30)
            response.raise_for_status()
            content_length = len(response.content)
            content_type = response.headers.get('content-type', 'unknown')
        except requests.RequestException as e:
            # 如果无法直接下载，记录URL信息
            content_length = 0
            content_type = 'url_only'
        
        # 创建解析任务记录
        result_data = {
            "contract_id": request.contract_id,
            "url": request.url,
            "session_id": session_id,
            "parsed_content": {
                "url": request.url,
                "content_length": content_length,
                "content_type": content_type,
                "parsed_at": datetime.now().isoformat(),
                "status": "completed" if content_length > 0 else "url_recorded"
            },
            "processing_info": {
                "method": "url_parser",
                "timestamp": datetime.now().isoformat(),
                "user_agent": "ContractAudit-Parser/1.0"
            },
            "metadata": {
                "domain": parsed_url.netloc,
                "path": parsed_url.path,
                "query": parsed_url.query,
                "fragment": parsed_url.fragment
            }
        }
        
        # 如果成功获取内容，可以进一步处理
        if content_length > 0:
            result_data["parsed_content"]["extracted_text"] = f"已从 {request.url} 提取文档内容，大小: {content_length} 字节"
            result_data["parsed_content"]["word_count"] = len(response.text.split()) if response.text else 0
        
        return DocParserResponse(
            code=200,
            message="文档解析成功",
            data=result_data
        )
        
    except Exception as e:
        return DocParserResponse(
            code=500,
            message=f"文档解析失败: {str(e)}",
            data=None
        )

@router.post("/forward/contract-view")
async def forward_contract_view(request: Request, db: Session = Depends(get_session)):
    """
    新增接口：前端传数据过来，如果有 censoredSearchEngine=0 的规则，则转发给 contract_view_query
    """
    try:
        data = await request.json()
        print(f"[forward_contract_view] 收到请求: {data}")
        # 检查 reviewRules 字段
        review_rules = data.get("reviewRules") or data.get("review_rules")
        if not review_rules:
            print("[forward_contract_view] 缺少 reviewRules 字段")
            return JSONResponse({"code": 400, "message": "缺少 reviewRules 字段"}, status_code=400)
        # 判断是否有 censoredSearchEngine=0 的规则
        has_censored_0 = any(
            (rule.get("censoredSearchEngine") == 0 or rule.get("censored_search_engine") == 0)
            for rule in review_rules
        )
        if has_censored_0:
            print("[forward_contract_view] 有 censoredSearchEngine=0 的规则，转发给 contract_view_query")
            # 直接调用 contract_view_query
            # 构造 ContractViewRequest 对象
            from pydantic import ValidationError
            try:
                req_obj = ContractViewRequest(**data)
                print(f"[forward_contract_view] 构造 ContractViewRequest 对象成功: {req_obj}")
            except ValidationError as ve:
                print(f"[forward_contract_view] 参数校验失败: {ve}")
                return JSONResponse({"code": 400, "message": f"参数校验失败: {ve}"}, status_code=400)
            print("[forward_contract_view] 调用 contract_view_query")
            resp = await contract_view_query(req_obj, db)
            print(f"[forward_contract_view] contract_view_query 返回: {resp}")
            return resp
        else:
            print("[forward_contract_view] 无 censoredSearchEngine=0 的规则，无需转发")
            return JSONResponse({"code": 200, "message": "无 censoredSearchEngine=0 的规则，无需转发"})
    except Exception as e:
        print(f"[forward_contract_view] 服务异常: {str(e)}")
        traceback.print_exc()
        return JSONResponse({"code": 500, "message": f"服务异常: {str(e)}"}, status_code=500)

class LogicRuleDto(BaseModel):
    pass
class ExampleDto(BaseModel):
    pass
class ConditionDto(BaseModel):
    pass

class ReviewRuleDto(BaseModel):
    id: Optional[int]
    ruleName: Optional[str]
    type: Optional[int]
    riskLevel: Optional[int]
    riskAttributionId: Optional[int]
    riskAttributionName: Optional[str]
    censoredSearchEngine: Optional[int]
    ruleGroupId: Optional[int]
    ruleGroupName: Optional[str]
    includeRule: Optional[str]
    logicRuleList: Optional[List[LogicRuleDto]]
    exampleList: Optional[List[ExampleDto]]
    conditionalIdentifier: Optional[str]
    conditionList: Optional[List[ConditionDto]]
    reviseOpinion: Optional[str]
    creatorId: Optional[int]
    creatorName: Optional[str]
    version: Optional[int]
    updateTime: Optional[datetime]

class JudgeResultDto(BaseModel):
    contractId: Optional[str]
    ruleId: Optional[int]
    result: Optional[bool]

@router.post("/review-rules/judge", response_model=List[JudgeResultDto])
def judge_review_rules(
    rules: List[ReviewRuleDto] = Body(..., description="审查规则列表"),
    contract_id: Optional[str] = None
):
    """
    接收规则列表，返回审查结果列表（集合）
    """
    results = []
    for rule in rules:
        # 示例逻辑：全部通过
        results.append(JudgeResultDto(
            contractId=contract_id or "test_contract_id",
            ruleId=rule.id,
            result=True
        ))
    return results

if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 直接运行时，同步调用 upload_local_docx 并输出结果
    import asyncio
    try:
        result = asyncio.run(upload_local_docx())
        print("最终返回:", result)
    except Exception as e:
        print("主程序异常:", e) 