#!/usr/bin/env python3
"""
合同审计系统启动脚本
用于正确启动FastAPI应用
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    try:
        print("=" * 50)
        print("合同审计系统启动中...")
        print("=" * 50)
        
        # 启动服务器，使用模块导入方式
        uvicorn.run(
            "ContractAudit.main:app",  # 使用模块导入字符串
            host="0.0.0.0",
            port=8001,
            reload=True,  # 开发模式，自动重载
            log_level="info"
        )
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 