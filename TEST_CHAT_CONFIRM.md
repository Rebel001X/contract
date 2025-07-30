# /chat/confirm 接口测试指南

## 概述

本文档提供了测试 `/chat/confirm` 接口的详细指南，特别关注 `risk_attribution_id` 和 `risk_attribution_name` 字段的处理。

## 前置条件

1. **启动服务器**
   ```bash
   cd rag642
   python run.py
   ```

2. **执行数据库迁移**
   ```sql
   -- 执行 add_risk_attribution_fields.sql
   mysql -u username -p database_name < add_risk_attribution_fields.sql
   ```

3. **检查服务器状态**
   ```bash
   curl http://localhost:8001/health
   ```

## 测试方法

### 方法1：使用 Python 测试脚本（推荐）

```bash
cd rag642
python test_chat_confirm.py
```

这个脚本会：
- 自动生成唯一的 session_id
- 发送包含风险归属字段的测试数据
- 实时显示流式响应
- 验证风险归属字段是否正确处理
- 检查数据库保存结果

### 方法2：使用 curl 脚本

```bash
cd rag642
chmod +x test_chat_confirm_curl.sh
./test_chat_confirm_curl.sh
```

### 方法3：使用 curl 命令

```bash
curl -X POST "http://localhost:8000/chat/confirm" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d @test_data.json \
  --no-buffer
```

### 方法4：使用 Postman

1. 创建新的 POST 请求
2. URL: `http://localhost:8001/chat/confirm`
3. Headers:
   - `Content-Type: application/json`
   - `Accept: text/event-stream`
4. Body (raw JSON):
   ```json
   {
     "session_id": "test_session_1234567890",
     "message": "{\"review_stage\":\"合同主体审查\",\"review_list\":2,\"contract_id\":\"test_contract_001\",\"review_rules\":[{\"id\":1,\"ruleName\":\"付款条款风险审查\",\"type\":\"付款条款审查\",\"riskLevel\":\"high\",\"riskAttributionId\":101,\"riskAttributionName\":\"财务部\",\"ruleGroupId\":1,\"ruleGroupName\":\"付款条款组\",\"reviseOpinion\":\"建议修改付款条件\",\"conditionList\":[{\"condition\":\"付款期限超过30天\",\"description\":\"检查合同中是否有付款期限超过30天的条款\"}]},{\"id\":2,\"ruleName\":\"违约责任审查\",\"type\":\"违约条款审查\",\"riskLevel\":\"medium\",\"riskAttributionId\":102,\"riskAttributionName\":\"法务部\",\"ruleGroupId\":2,\"ruleGroupName\":\"违约责任组\",\"reviseOpinion\":\"建议明确违约责任\",\"conditionList\":[{\"condition\":\"违约责任不明确\",\"description\":\"检查违约责任条款是否明确具体\"}]}]}",
     "auto_save": true,
     "user_id": "test_user_001",
     "project_name": "测试合同审查项目"
   }
   ```

## 测试数据说明

### 测试规则1：付款条款风险审查
- **规则ID**: 1
- **规则名称**: 付款条款风险审查
- **风险等级**: high
- **风险归属ID**: 101
- **风险归属名**: 财务部
- **规则分组**: 付款条款组

### 测试规则2：违约责任审查
- **规则ID**: 2
- **规则名称**: 违约责任审查
- **风险等级**: medium
- **风险归属ID**: 102
- **风险归属名**: 法务部
- **规则分组**: 违约责任组

## 预期结果

### 1. 流式响应事件

你应该看到以下事件序列：

1. **start** - 开始处理
2. **rule_completed** - 每个规则完成时
3. **structured_result** - 结构化结果
4. **auto_save_success** - 自动保存成功
5. **complete** - 处理完成

### 2. 风险归属字段验证

在 `structured_result` 事件中，检查 `data.list` 数组中的每个规则是否包含：

```json
{
  "ruleName": "付款条款风险审查",
  "riskAttributionId": 101,
  "riskAttributionName": "财务部",
  "review_result": "FAIL"
}
```

### 3. 数据库验证

检查 `confirm_review_rule_result` 表中是否正确保存了风险归属信息：

```sql
SELECT 
  session_id,
  rule_name,
  risk_attribution_id,
  risk_attribution_name,
  review_result,
  created_at
FROM confirm_review_rule_result 
WHERE session_id LIKE 'test_session_%'
ORDER BY created_at DESC;
```

## 常见问题排查

### 1. 服务器连接失败
```
❌ 无法连接到服务器，请确保服务器正在运行
```
**解决方案**: 检查服务器是否启动，端口是否正确

### 2. 数据库字段不存在
```
❌ 数据库字段缺失
```
**解决方案**: 执行数据库迁移脚本

### 3. 风险归属字段缺失
```
❌ 风险归属ID: 缺失
❌ 风险归属名: 缺失
```
**解决方案**: 
- 检查前端传递的数据格式
- 检查后端字段处理逻辑
- 检查数据库字段是否存在

### 4. 自动保存失败
```
❌ 自动保存失败或未执行
```
**解决方案**:
- 检查数据库连接
- 检查表结构
- 查看服务器日志

## 调试技巧

### 1. 查看服务器日志
```bash
tail -f logs/app.log
```

### 2. 检查数据库连接
```python
# 在 Python 中测试数据库连接
from ContractAudit.config import get_session
db = next(get_session())
print("数据库连接成功")
```

### 3. 验证字段处理
在 `main.py` 中添加调试日志：
```python
print(f"[DEBUG] 风险归属ID: {risk_attribution_id}")
print(f"[DEBUG] 风险归属名: {risk_attribution_name}")
```

## 测试报告模板

```
测试结果报告
============

✅ 服务器连接: 正常
✅ 数据库连接: 正常
✅ 流式响应: 正常
✅ 风险归属字段: 正常
✅ 自动保存: 正常

测试详情:
- 规则1: 付款条款风险审查 (风险归属: 财务部)
- 规则2: 违约责任审查 (风险归属: 法务部)
- 保存记录数: 2
- 处理时间: XX秒

结论: 测试通过 ✅
```

## 性能测试

对于大量规则的测试：

```bash
# 修改测试脚本中的规则数量
"review_rules": [
  // 添加更多规则...
]
```

建议测试场景：
- 10条规则
- 50条规则  
- 100条规则

监控指标：
- 响应时间
- 内存使用
- 数据库写入速度 