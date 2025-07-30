@echo off
REM 测试 censoredSearchEngine 字段处理逻辑的 Windows 批处理脚本

echo 🧪 开始测试 censoredSearchEngine 字段处理逻辑
echo ============================================================

REM 测试数据：包含 censoredSearchEngine 为 1 的规则
echo 📋 测试场景 1: 有 censoredSearchEngine 为 1 的规则
echo ============================================================

curl -X POST "http://localhost:8001/chat/confirm" ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"test_session_123\",\"message\":\"{\\\"contractId\\\":\\\"test_contract_456\\\",\\\"reviewRules\\\":[{\\\"id\\\":1,\\\"ruleId\\\":1,\\\"ruleName\\\":\\\"不得空白签字\\\",\\\"censoredSearchEngine\\\":1,\\\"riskLevel\\\":2,\\\"riskAttributionId\\\":101,\\\"riskAttributionName\\\":\\\"法律部\\\"},{\\\"id\\\":2,\\\"ruleId\\\":2,\\\"ruleName\\\":\\\"合同金额检查\\\",\\\"censoredSearchEngine\\\":0,\\\"riskLevel\\\":1,\\\"riskAttributionId\\\":102,\\\"riskAttributionName\\\":\\\"财务部\\\"}]}\"}" ^
  --max-time 120

echo.
echo.
echo 🧪 测试场景 2: 没有 censoredSearchEngine 为 1 的规则
echo ============================================================

curl -X POST "http://localhost:8001/chat/confirm" ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"test_session_456\",\"message\":\"{\\\"contractId\\\":\\\"test_contract_789\\\",\\\"reviewRules\\\":[{\\\"id\\\":1,\\\"ruleId\\\":1,\\\"ruleName\\\":\\\"不得空白签字\\\",\\\"censoredSearchEngine\\\":0,\\\"riskLevel\\\":2,\\\"riskAttributionId\\\":101,\\\"riskAttributionName\\\":\\\"法律部\\\"},{\\\"id\\\":2,\\\"ruleId\\\":2,\\\"ruleName\\\":\\\"合同金额检查\\\",\\\"censoredSearchEngine\\\":0,\\\"riskLevel\\\":1,\\\"riskAttributionId\\\":102,\\\"riskAttributionName\\\":\\\"财务部\\\"}]}\"}" ^
  --max-time 120

echo.
echo.
echo ✅ 测试完成
pause 