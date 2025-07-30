#!/usr/bin/env python3
"""
调试 find_censored_search_engine 函数
"""

def find_censored_search_engine(obj, path=""):
    """递归查找 censoredSearchEngine 字段"""
    print(f"DEBUG: 检查对象 {type(obj)} 路径: {path}")
    
    if isinstance(obj, dict):
        print(f"DEBUG: 是字典，键: {list(obj.keys())}")
        # 检查当前层级是否有 censoredSearchEngine 字段
        censored_search_engine = obj.get('censoredSearchEngine') or obj.get('censored_search_engine')
        print(f"DEBUG: 当前层级 censoredSearchEngine: {censored_search_engine}")
        if censored_search_engine is not None:
            print(f"DEBUG: 找到 censoredSearchEngine: {censored_search_engine}")
            return censored_search_engine, path
        
        # 递归查找子对象
        for key, value in obj.items():
            print(f"DEBUG: 递归检查键: {key}")
            result, new_path = find_censored_search_engine(value, f"{path}.{key}" if path else key)
            if result is not None:
                print(f"DEBUG: 在子对象中找到: {result}")
                return result, new_path
                
    elif isinstance(obj, list):
        print(f"DEBUG: 是列表，长度: {len(obj)}")
        # 递归查找列表中的每个元素
        for i, item in enumerate(obj):
            result, new_path = find_censored_search_engine(item, f"{path}[{i}]" if path else f"[{i}]")
            if result is not None:
                return result, new_path
    
    print(f"DEBUG: 未找到 censoredSearchEngine，返回 None")
    return None, path

# 测试
test_data = {"nested": {"censoredSearchEngine": 0}}
print("测试数据:", test_data)
result, path = find_censored_search_engine(test_data)
print(f"最终结果: {result}, 路径: {path}") 