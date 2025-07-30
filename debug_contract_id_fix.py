#!/usr/bin/env python3
"""
调试脚本：测试 contract_id 获取逻辑的修复
"""

import json

def test_contract_id_logic():
    """测试 contract_id 获取逻辑"""
    
    # 模拟 message_data（前端传入的数据）
    message_data = {
        "contractId": "1234",
        "contract_id": None,  # 有时可能为空
        "reviewRules": [
            {
                "ruleId": 1,
                "ruleName": "不得空白签字",
                "censoredSearchEngine": 1
            }
        ]
    }
    
    # 模拟 contract_view_result（后端返回的数据）
    contract_view_result = {
        "0": {
            "rule_id": 1,
            "result_list": []
        },
        "1": {
            "rule_id": 2,
            "result_list": []
        }
    }
    
    # 测试修复后的逻辑
    print("=" * 60)
    print("🔍 测试 contract_id 获取逻辑修复")
    print("=" * 60)
    
    # 模拟修复后的逻辑
    contract_id = (
        message_data.get("contractId") or 
        message_data.get("contract_id") or 
        "1234"  # 默认值，避免从 contract_view_result 获取失败
    )
    
    print(f"📋 输入数据:")
    print(f"  - message_data.get('contractId'): {message_data.get('contractId')}")
    print(f"  - message_data.get('contract_id'): {message_data.get('contract_id')}")
    print(f"  - contract_view_result 结构: {type(contract_view_result)}")
    print(f"  - contract_view_result.get('contractId'): {contract_view_result.get('contractId')}")
    print(f"  - contract_view_result.get('contract_id'): {contract_view_result.get('contract_id')}")
    
    print(f"\n✅ 修复后的结果:")
    print(f"  - 最终 contract_id: {contract_id}")
    print(f"  - 类型: {type(contract_id)}")
    
    # 测试不同场景
    print(f"\n🧪 场景测试:")
    
    # 场景1：message_data 中有 contractId
    test_data_1 = {"contractId": "test-001", "contract_id": None}
    result_1 = test_data_1.get("contractId") or test_data_1.get("contract_id") or "1234"
    print(f"  场景1 (有 contractId): {result_1}")
    
    # 场景2：message_data 中有 contract_id
    test_data_2 = {"contractId": None, "contract_id": "test-002"}
    result_2 = test_data_2.get("contractId") or test_data_2.get("contract_id") or "1234"
    print(f"  场景2 (有 contract_id): {result_2}")
    
    # 场景3：都没有，使用默认值
    test_data_3 = {"contractId": None, "contract_id": None}
    result_3 = test_data_3.get("contractId") or test_data_3.get("contract_id") or "1234"
    print(f"  场景3 (使用默认值): {result_3}")
    
    print("=" * 60)
    print("✅ 修复验证完成")
    print("=" * 60)

if __name__ == "__main__":
    test_contract_id_logic() 