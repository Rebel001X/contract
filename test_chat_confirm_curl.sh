#!/bin/bash

# 测试 /chat/confirm 接口的 curl 脚本
# 包含 risk_attribution_id 和 risk_attribution_name 字段测试

echo "开始测试 /chat/confirm 接口..."
echo "=================================="

# 生成唯一的 session_id
SESSION_ID="test_session_$(date +%s)"
echo "Session ID: $SESSION_ID"

# 创建测试数据
cat > test_data.json << 'EOF'
{
  "session_id": "SESSION_ID_PLACEHOLDER",
  "message": "{\"review_stage\":\"合同主体审查\",\"review_list\":2,\"contract_id\":\"test_contract_001\",\"review_rules\":[{\"id\":1,\"ruleName\":\"付款条款风险审查\",\"type\":\"付款条款审查\",\"riskLevel\":\"high\",\"riskAttributionId\":101,\"riskAttributionName\":\"财务部\",\"ruleGroupId\":1,\"ruleGroupName\":\"付款条款组\",\"reviseOpinion\":\"建议修改付款条件\",\"conditionList\":[{\"condition\":\"付款期限超过30天\",\"description\":\"检查合同中是否有付款期限超过30天的条款\"}]},{\"id\":2,\"ruleName\":\"违约责任审查\",\"type\":\"违约条款审查\",\"riskLevel\":\"medium\",\"riskAttributionId\":102,\"riskAttributionName\":\"法务部\",\"ruleGroupId\":2,\"ruleGroupName\":\"违约责任组\",\"reviseOpinion\":\"建议明确违约责任\",\"conditionList\":[{\"condition\":\"违约责任不明确\",\"description\":\"检查违约责任条款是否明确具体\"}]}]}",
  "auto_save": true,
  "user_id": "test_user_001",
  "project_name": "测试合同审查项目"
}
EOF

# 替换 session_id
sed -i "s/SESSION_ID_PLACEHOLDER/$SESSION_ID/g" test_data.json

echo "发送请求到 /chat/confirm..."
echo "请求数据:"
cat test_data.json | jq '.' 2>/dev/null || cat test_data.json
echo ""

# 发送请求并处理流式响应
curl -X POST "http://localhost:8001/chat/confirm" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d @test_data.json \
  --no-buffer \
  --max-time 120 \
  | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
      # 提取 JSON 数据
      json_data="${line#data: }"
      echo "收到事件: $json_data"
      
      # 尝试解析 JSON 并提取关键信息
      if command -v jq &> /dev/null; then
        event_type=$(echo "$json_data" | jq -r '.event // "unknown"' 2>/dev/null)
        echo "  事件类型: $event_type"
        
        if [[ "$event_type" == "structured_result" ]]; then
          echo "  📊 结构化结果:"
          total_issues=$(echo "$json_data" | jq -r '.data.total_issues // 0' 2>/dev/null)
          echo "    总问题数: $total_issues"
          
          # 检查风险归属字段
          rule_count=$(echo "$json_data" | jq -r '.data.list | length // 0' 2>/dev/null)
          echo "    规则数量: $rule_count"
          
          for i in $(seq 0 $((rule_count-1))); do
            rule_name=$(echo "$json_data" | jq -r ".data.list[$i].ruleName // \"N/A\"" 2>/dev/null)
            risk_attribution_id=$(echo "$json_data" | jq -r ".data.list[$i].riskAttributionId // \"N/A\"" 2>/dev/null)
            risk_attribution_name=$(echo "$json_data" | jq -r ".data.list[$i].riskAttributionName // \"N/A\"" 2>/dev/null)
            review_result=$(echo "$json_data" | jq -r ".data.list[$i].review_result // \"N/A\"" 2>/dev/null)
            
            echo "      规则 $((i+1)): $rule_name"
            echo "        风险归属ID: $risk_attribution_id"
            echo "        风险归属名: $risk_attribution_name"
            echo "        审查结果: $review_result"
          done
        elif [[ "$event_type" == "auto_save_success" ]]; then
          echo "  💾 自动保存成功"
          saved_count=$(echo "$json_data" | jq -r '.data.saved_rule_results_count // 0' 2>/dev/null)
          echo "    保存的规则结果数: $saved_count"
        elif [[ "$event_type" == "complete" ]]; then
          echo "  ✅ 处理完成"
        elif [[ "$event_type" == "error" ]]; then
          echo "  ❌ 错误:"
          error_msg=$(echo "$json_data" | jq -r '.data.error // "未知错误"' 2>/dev/null)
          echo "    $error_msg"
        fi
      else
        echo "  原始数据: $json_data"
      fi
      echo ""
    fi
  done

echo "测试完成"
echo "清理临时文件..."
rm -f test_data.json

echo "=================================="
echo "测试结束" 