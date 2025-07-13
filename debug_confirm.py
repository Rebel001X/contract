#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 confirm 接口问题
"""

import requests
import json

def test_confirm_with_error_handling():
    """测试confirm接口并处理错误"""
    
    base_url = "http://172.20.237.99:8001"
    
    # 测试数据
    test_data = {
        "session_id": "debug_test_session",
        "message": "请分析这个合同的风险点"
    }
    
    print("🔍 调试 confirm 接口...")
    print(f"服务地址: {base_url}")
    print(f"请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 先测试服务是否响应
        print("\n1️⃣ 测试服务响应...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        
        # 测试confirm接口
        print("\n2️⃣ 测试 confirm 接口...")
        response = requests.post(
            f"{base_url}/chat/confirm",
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=10
        )
        
        print(f"Confirm接口状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Confirm接口响应成功")
            
            # 尝试读取响应
            print("\n3️⃣ 尝试读取流式响应...")
            line_count = 0
            
            for line in response.iter_lines():
                line_count += 1
                if line:
                    line_str = line.decode('utf-8')
                    print(f"行 {line_count}: {line_str}")
                    
                    if line_str.startswith('data: '):
                        try:
                            event_data = json.loads(line_str[6:])
                            print(f"✅ 成功解析事件: {event_data.get('event')}")
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON解析失败: {e}")
                            print(f"原始数据: {line_str}")
                        except Exception as e:
                            print(f"❌ 事件处理失败: {e}")
                    
                    # 只读取前10行进行调试
                    if line_count >= 10:
                        print("🔍 已读取10行，停止调试")
                        break
            else:
                print("📡 流式响应结束")
                
        else:
            print(f"❌ Confirm接口失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_alternative_endpoints():
    """测试其他端点"""
    
    base_url = "http://172.20.237.99:8001"
    
    print("\n🔍 测试其他端点...")
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"根路径状态码: {response.status_code}")
    except Exception as e:
        print(f"根路径测试失败: {e}")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"服务状态: {health_data}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 测试会话创建
    try:
        response = requests.post(
            f"{base_url}/sessions",
            json={"user_id": "debug_user"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"会话创建状态码: {response.status_code}")
    except Exception as e:
        print(f"会话创建失败: {e}")

if __name__ == "__main__":
    # 测试其他端点
    test_alternative_endpoints()
    
    # 测试confirm接口
    test_confirm_with_error_handling() 