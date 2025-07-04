#!/usr/bin/env python3
"""
合同审计聊天系统启动脚本
Contract Audit Chat Startup Script
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """启动聊天系统"""
    try:
        # 检查chat.py文件是否存在
        chat_file = os.path.join(current_dir, "chat.py")
        if not os.path.exists(chat_file):
            print("❌ 错误: chat.py 文件不存在")
            sys.exit(1)
        
        # 直接执行chat.py文件，而不是导入
        print("🚀 启动合同审计聊天系统 (企业级版本)...")
        print("=" * 60)
        
        # 使用exec执行文件内容
        with open(chat_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 设置模块的__name__为__main__，这样if __name__ == "__main__"会执行
        exec_globals = {
            '__name__': '__main__',
            '__file__': chat_file,
            '__builtins__': __builtins__
        }
        
        exec(code, exec_globals)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保 chat.py 文件存在")
        print("如果依赖缺失，请运行: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查依赖是否正确安装")
        sys.exit(1)

if __name__ == "__main__":
    main() 