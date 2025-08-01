#!/bin/bash

# 测试分页接口audit_quality字段的curl脚本
BASE_URL="http://localhost:8001"

echo "============================================================"
echo "测试分页接口audit_quality字段"
echo "============================================================"

echo ""
echo "1. 测试基础分页查询"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=3" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "2. 测试按规则ID过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=3&rule_id=1" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "3. 测试按风险等级过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=3&risk_level=high" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "4. 测试关键字搜索"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=3&keyword=合同" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "5. 测试按合同ID过滤"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=3&contract_id=CONTRACT_001" \
  -H "Content-Type: application/json" \
  | python -m json.tool

echo ""
echo "6. 测试获取单条记录详情（验证字段结构）"
echo "------------------------------------------------------------"
curl -X GET "${BASE_URL}/api/confirm-review-rule-results/page?page=1&pageSize=1" \
  -H "Content-Type: application/json" \
  | python -c "
import json
import sys
data = json.load(sys.stdin)
if data.get('data') and len(data['data']) > 0:
    item = data['data'][0]
    audit_quality = item.get('audit_quality')
    print(f'audit_quality字段值: {audit_quality}')
    print(f'audit_quality字段类型: {type(audit_quality).__name__}')
    if audit_quality is not None:
        if isinstance(audit_quality, int) and 1 <= audit_quality <= 5:
            print('✅ audit_quality字段正确')
        else:
            print('❌ audit_quality字段类型或范围不正确')
    else:
        print('ℹ️ audit_quality字段为null（正常）')
else:
    print('没有查询到数据')
"

echo ""
echo "测试完成！" 