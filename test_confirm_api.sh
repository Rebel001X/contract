#!/bin/bash

# 测试 /chat/confirm 自动保存功能

API_URL="http://localhost:8001/chat/confirm"
SESSION_ID="test_session_final5"
MESSAGE='{"reviewStage": "初审", "reviewList": 2, "reviewRules": [{"id": 1, "ruleName": "不得空白签字", "type": 0, "riskLevel": 2, "riskAttributionId": 101, "riskAttributionName": "法律部", "censoredSearchEngine": 0, "ruleGroupId": 10, "ruleGroupName": "签署规范", "includeRule": "签字页必须填写", "exampleList": ["签字页空白", "未签署日期"], "conditionalIdentifier": "A1", "conditionList": [{"field": "签字页", "operator": "不为空", "value": ""}], "reviseOpinion": "所有签字页必须填写签署人姓名和日期", "creatorId": 1001, "creatorName": "张三", "version": 1, "updateTime": "2024-07-16T12:00:00"}], "contract_id": "90123i481"}'

# 组装JSON
JSON_DATA=$(jq -nc --arg sid "$SESSION_ID" --arg msg "$MESSAGE" '{session_id: $sid, message: $msg}')

echo "请求内容: $JSON_DATA"

echo "\n--- 开始请求 $API_URL ---\n"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$JSON_DATA" \
  -w "\nHTTP状态码: %{http_code}\n"

echo "\n--- 请求结束 ---\n" 