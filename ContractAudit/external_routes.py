from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field
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
    list_review_rules
)
from .config import get_session
import requests
import os
from fastapi.responses import StreamingResponse
import asyncio
import threading

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
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    risk_level: Optional[str] = Query(None, description="风险等级过滤"),
    review_status: Optional[str] = Query(None, description="审查状态过滤"),
    db: Session = Depends(get_session)
):
    skip = (page - 1) * page_size
    query = db.query(ContractAuditReview).filter(ContractAuditReview.is_deleted == False)
    
    # 添加过滤条件
    if session_id:
        query = query.filter(ContractAuditReview.ext_json.contains({"session_id": session_id}))
    if risk_level:
        query = query.filter(ContractAuditReview.risk_level == risk_level)
    if review_status:
        query = query.filter(ContractAuditReview.review_status == review_status)
    
    total = query.count()
    items = query.order_by(ContractAuditReview.updated_at.desc()).offset(skip).limit(page_size).all()
    return PaginatedContractAuditReview(total=total, items=items)

@router.get("/contract-audit-reviews/by-session/{session_id}", response_model=List[ContractAuditReviewOut])
def get_reviews_by_session(session_id: str, db: Session = Depends(get_session)):
    """
    根据会话ID获取审查记录
    """
    reviews = db.query(ContractAuditReview).filter(
        ContractAuditReview.ext_json.contains({"session_id": session_id}),
        ContractAuditReview.is_deleted == False
    ).order_by(ContractAuditReview.created_at.desc()).all()
    
    return reviews

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
    
    return {
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
    }

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

@router.get("/review-rules", response_model=List[dict])
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
        return [
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
        ]
    except Exception as e:
        print(f"获取保存的审查规则异常: {e}")
        raise HTTPException(status_code=500, detail=f"获取审查规则失败: {str(e)}")

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

@router.post("/review-rules/save-selected-sync", response_model=SaveSelectedRulesResponse)
async def save_selected_review_rules_sync(request: SaveSelectedRulesRequest, db: Session = Depends(get_session)):
    """
    同步保存用户勾选的审查规则到数据库（立即执行，不使用后台任务）
    """
    try:
        # 转换数据格式
        rules_data = []
        saved_count = 0
        skipped_count = 0
        
        for rule in request.selected_rules:
            # 检查是否已存在（根据外部ID）
            existing_rule = get_review_rule_by_external_id(db, rule.rule_id)
            if existing_rule:
                print(f"规则已存在，跳过: {rule.rule_name}")
                skipped_count += 1
                continue
                
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
        
        if rules_data:
            # 批量插入数据
            created_rules = bulk_create_review_rules(db, rules_data)
            saved_count = len(created_rules)
            print(f"成功保存 {saved_count} 条勾选的审查规则到数据库")
        
        return SaveSelectedRulesResponse(
            code=200,
            message=f"成功保存 {saved_count} 条勾选的审查规则，跳过 {skipped_count} 条已存在的规则",
            data={
                "selected_count": len(request.selected_rules),
                "saved_count": saved_count,
                "skipped_count": skipped_count,
                "user_id": request.user_id,
                "project_name": request.project_name,
                "description": request.description
            }
        )
        
    except Exception as e:
        print(f"同步保存勾选审查规则异常: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"同步保存勾选审查规则失败: {str(e)}"
        )

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