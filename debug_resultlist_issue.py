#!/usr/bin/env python3
"""
调试 resultList 字段缺失问题
"""

import json

def debug_resultlist_issue():
    """调试 resultList 字段缺失问题"""
    
    # 模拟您提供的数据
    test_data = {
        "event": "rule_completed",
        "timestamp": 1754567274.8624866,
        "data": {
            "session_id": "mock_session_id",
            "status": "rule_completed",
            "completed_rule": {
                "id": 18,
                "ruleName": "规则_丙方信息",
                "type": 1,
                "riskLevel": 1,
                "riskAttributionId": 4,
                "riskAttributionName": "其他风险",
                "censoredSearchEngine": 1,
                "ruleGroupId": 4,
                "ruleGroupName": "规则引擎分组",
                "includeRule": None,
                "exampleList": None,
                "conditionalIdentifier": "anyone",
                "conditionList": [
                    {
                        "conditionInfo": "[{\"body\":\"丙方邮政编码\",\"logicalSymbol\":\"为空\"},{\"body\":\"丙方联系邮箱\",\"logicalSymbol\":\"不为空\"},{\"body\":\"丙方联系人\",\"logicalSymbol\":\"不为空\"}]"
                    }
                ],
                "reviseOpinion": "添加丙方信息",
                "creatorId": 0,
                "creatorName": "admin",
                "version": 3,
                "updateTime": "2025-08-05 08:57:59",
                "verbatimTextList": "[\"丙方邮政编码：510000\", \"丙方联系邮箱：contact@sanfang.com\", \"丙方联系人：王五\"]",
                "matchedContent": "丙方邮政编码：510000；丙方联系邮箱：contact@sanfang.com；丙方联系人：王五",
                "suggestions": "添加丙方信息",
                "reviewResult": "done",
                "ruleConfirmResult": False,
                "contractId": "1234",
                "issues": "[]",
                "ruleId": 18,
                "ruleIndex": 2,
                "analysis": "[]",
                "confidenceScore": 50,
                "sessionId": "mock_session_id",
                "createdAt": "2025-08-07T19:47:51.823715+08:00"
            },
            "processed_count": 3,
            "total_rules": 6,
            "message": "规则 规则_丙方信息 审查完成"
        }
    }
    
    print("🔍 开始调试 resultList 字段缺失问题")
    print("=" * 60)
    
    # 获取 completed_rule
    completed_rule = test_data["data"]["completed_rule"]
    
    print("📋 原始数据检查:")
    print(f"  - suggestions: {completed_rule.get('suggestions')} (类型: {type(completed_rule.get('suggestions'))})")
    print(f"  - matchedContent: {completed_rule.get('matchedContent')} (类型: {type(completed_rule.get('matchedContent'))})")
    print(f"  - 是否有 suggestions: {'suggestions' in completed_rule}")
    print(f"  - 是否有 matchedContent: {'matchedContent' in completed_rule}")
    
    # 模拟 process_rule_for_frontend 函数的逻辑
    def process_rule_for_frontend(rule):
        """模拟 process_rule_for_frontend 函数"""
        print("\n🔧 开始处理 rule:")
        print(f"  - rule 类型: {type(rule)}")
        print(f"  - rule 键: {list(rule.keys())}")
        
        # 添加 resultList 字段，包含 suggestions 和 matchedContent
        result_list = []
        
        # 构建一个包含所有字段的 result_item，与 contract/view 格式保持一致
        result_item = {}
        
        print("\n📝 检查 suggestions:")
        print(f"  - 'suggestions' in rule: {'suggestions' in rule}")
        print(f"  - rule['suggestions']: {rule.get('suggestions')}")
        print(f"  - rule['suggestions'] 类型: {type(rule.get('suggestions'))}")
        print(f"  - rule['suggestions'] 是否为空: {not rule.get('suggestions')}")
        
        if 'suggestions' in rule and rule['suggestions']:
            print("  ✅ suggestions 条件满足，添加到 result_item")
            result_item["suggestions"] = str(rule['suggestions'])
        else:
            print("  ❌ suggestions 条件不满足")
        
        print("\n📝 检查 matchedContent:")
        print(f"  - 'matchedContent' in rule: {'matchedContent' in rule}")
        print(f"  - rule['matchedContent']: {rule.get('matchedContent')}")
        print(f"  - rule['matchedContent'] 类型: {type(rule.get('matchedContent'))}")
        print(f"  - rule['matchedContent'] 是否为空: {not rule.get('matchedContent')}")
        
        if 'matchedContent' in rule and rule['matchedContent']:
            print("  ✅ matchedContent 条件满足，添加到 result_item")
            result_item["matched_content"] = str(rule['matchedContent'])
        else:
            print("  ❌ matchedContent 条件不满足")
        
        print(f"\n📊 result_item: {result_item}")
        print(f"📊 result_item 是否为空: {not result_item}")
        
        # 如果有数据，添加到 resultList
        if result_item:
            print("  ✅ result_item 不为空，添加到 result_list")
            result_list.append(result_item)
        else:
            print("  ❌ result_item 为空，不添加到 result_list")
        
        print(f"📊 result_list: {result_list}")
        
        rule['resultList'] = result_list
        print(f"📊 设置 rule['resultList'] = {result_list}")
        
        return rule
    
    # 处理数据
    print("\n🔄 开始处理数据...")
    processed_rule = process_rule_for_frontend(completed_rule.copy())
    
    print("\n📊 处理后的数据:")
    print(f"  - resultList 长度: {len(processed_rule.get('resultList', []))}")
    print(f"  - resultList 内容: {processed_rule.get('resultList')}")
    
    if processed_rule.get('resultList'):
        print("  ✅ resultList 包含数据:")
        for i, item in enumerate(processed_rule['resultList']):
            print(f"    条目 {i+1}:")
            for key, value in item.items():
                print(f"      {key}: {value}")
    else:
        print("  ❌ resultList 为空")
    
    # 检查最终输出
    print("\n🎯 最终输出检查:")
    final_output = {
        "event": "rule_completed",
        "timestamp": 1754567274.8624866,
        "data": {
            "session_id": "mock_session_id",
            "status": "rule_completed",
            "completed_rule": processed_rule
        }
    }
    
    print(f"  - completed_rule 中是否有 resultList: {'resultList' in processed_rule}")
    print(f"  - resultList 内容: {processed_rule.get('resultList')}")
    
    # 转换为 JSON 检查
    try:
        json_output = json.dumps(final_output, ensure_ascii=False, indent=2)
        print("\n📄 JSON 输出:")
        print(json_output)
    except Exception as e:
        print(f"❌ JSON 序列化失败: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 调试完成")

if __name__ == "__main__":
    debug_resultlist_issue() 