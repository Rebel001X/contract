#!/bin/bash

# 测试带page后缀的分页接口
BASE_URL="http://localhost:8001"

echo "============================================================"
echo "测试分页接口"
echo "============================================================"

echo ""
echo "1. 测试 /confirm-review-rule-results/page 基础分页"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/confirm-review-rule-results/page?page=1&pageSize=5" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "2. 测试 /confirm-review-rule-results/page 按风险等级过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/confirm-review-rule-results/page?page=1&pageSize=5&risk_level=高" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "3. 测试 /confirm-review-rule-results/page 按风险归属过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/confirm-review-rule-results/page?page=1&pageSize=5&risk_attribution_id=1" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "4. 测试 /contract-audit-reviews/page 基础分页"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/contract-audit-reviews/page?page=1&page_size=5" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "5. 测试 /contract-audit-reviews/page 按风险等级过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/contract-audit-reviews/page?page=1&page_size=5&risk_level=高" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "6. 测试获取合同列表"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/confirm-review-rule-results/by-contract" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "7. 测试获取创建时间列表"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/confirm-review-rule-results/created-times" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "8. 测试统计接口"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/contract-audit-reviews/stats" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "============================================================"
echo "测试完成"
echo "============================================================" 