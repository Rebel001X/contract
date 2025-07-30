#!/usr/bin/env python3
"""
调试 rule/confirm 逻辑的简单脚本
"""

import json

def test_rule_confirm_logic():
    """测试 rule/confirm 逻辑"""
    
    # 模拟前端数据
    test_message = {
        "contractId": "test_contract_001",
        "reviewRules": [
            {
                "ruleId": 6,
                "ruleName": "测试规则6",
                "censoredSearchEngine": 1,  # 需要调用 rule/confirm
                "riskLevel": 2,
                "riskAttributionId": 101,
                "riskAttributionName": "法律部",
                "ruleGroupId": 10,
                "ruleGroupName": "签署规范",
                "includeRule": "签字页必须填写"
            },
            {
                "ruleId": 8,
                "ruleName": "测试规则8",
                "censoredSearchEngine": 1,  # 需要调用 rule/confirm
                "riskLevel": 1,
                "riskAttributionId": 102,
                "riskAttributionName": "财务部",
                "ruleGroupId": 11,
                "ruleGroupName": "财务规范",
                "includeRule": "金额必须大写"
            },
            {
                "ruleId": 9,
                "ruleName": "测试规则9",
                "censoredSearchEngine": 0,  # 不需要调用 rule/confirm
                "riskLevel": 1,
                "riskAttributionId": 103,
                "riskAttributionName": "技术部",
                "ruleGroupId": 12,
                "ruleGroupName": "技术规范",
                "includeRule": "技术条款必须明确"
            }
        ]
    }
    
    # 模拟 rule/confirm 响应
    rule_engine_result = {
        'code': 10000000, 
        'data': False, 
        'message': '规则检查未通过', 
        'description': '存在规则验证失败', 
        'total': 0, 
        'maxPage': 0
    }
    
    print("🚀 开始测试 rule/confirm 逻辑...")
    print(f"📋 测试数据: {json.dumps(test_message, ensure_ascii=False, indent=2)}")
    print(f"📥 rule/confirm 响应: {json.dumps(rule_engine_result, ensure_ascii=False, indent=2)}")
    
    # 模拟 find_censored_search_engine 函数
    def find_censored_search_engine(obj, path=""):
        """递归查找 censoredSearchEngine 字段"""
        if isinstance(obj, dict):
            # 检查当前层级是否有 censoredSearchEngine 字段
            censored_search_engine = obj.get('censoredSearchEngine') or obj.get('censored_search_engine')
            if censored_search_engine is not None:
                return censored_search_engine, path
            
            # 递归查找子对象
            for key, value in obj.items():
                result, new_path = find_censored_search_engine(value, f"{path}.{key}" if path else key)
                if result is not None:
                    return result, new_path
                    
        elif isinstance(obj, list):
            # 递归查找列表中的每个元素
            for i, item in enumerate(obj):
                result, new_path = find_censored_search_engine(item, f"{path}[{i}]" if path else f"[{i}]")
                if result is not None:
                    return result, new_path
        
        return None, path
    
    # 检查前端传入的规则中是否有 censoredSearchEngine 为 1 的规则
    frontend_rules = test_message.get('reviewRules') or test_message.get('review_rules') or []
    censored_rules = []
    
    print(f"\n📊 前端规则数量: {len(frontend_rules)}")
    
    for rule in frontend_rules:
        # 递归查找 censoredSearchEngine 字段
        censored_search_engine, found_path = find_censored_search_engine(rule)
        rule_id = rule.get('ruleId') or rule.get('id')
        print(f"📝 规则 {rule_id} 的 censoredSearchEngine: {censored_search_engine} (路径: {found_path})")
        
        if censored_search_engine == 1:
            censored_rules.append(rule)
            print(f"✅ 发现需要调用 rule/confirm 的规则: {rule_id}")
    
    print(f"\n🔢 censored_rules 数量: {len(censored_rules)}")
    
    # 模拟处理每个规则
    for idx, fr in enumerate(frontend_rules):
        rule_id = fr.get('ruleId') or fr.get('id')
        print(f"\n🔍 处理规则 {rule_id}:")
        
        # 检查当前规则是否有 censoredSearchEngine=1
        current_rule_censored = False
        censored_search_engine, found_path = find_censored_search_engine(fr)
        if censored_search_engine == 1:
            current_rule_censored = True
            print(f"  ✅ 规则 {rule_id} 有 censoredSearchEngine=1")
        
        if current_rule_censored and rule_engine_result and isinstance(rule_engine_result, dict) and not rule_engine_result.get('error'):
            # 从 rule/confirm 响应中获取布尔值结果
            rule_confirm_success = rule_engine_result.get('data', False)
            print(f"  📥 rule/confirm 响应结果: rule_id={rule_id}, success={rule_confirm_success}")
            
            # 根据布尔值设置 review_result：true -> "pass", false -> "done"
            if rule_confirm_success:
                review_result = "pass"
                print(f"  ✅ 规则 {rule_id} 通过 rule/confirm 验证，设置 review_result=pass")
            else:
                review_result = "done"
                print(f"  ❌ 规则 {rule_id} 未通过 rule/confirm 验证，设置 review_result=done")
        else:
            print(f"  ⚠️  无需处理 rule/confirm 响应: current_rule_censored={current_rule_censored}")
            review_result = "pass"  # 默认值
        
        print(f"  📋 最终 review_result: {review_result}")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    test_rule_confirm_logic() 