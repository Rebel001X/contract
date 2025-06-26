#!/usr/bin/env python3
"""
简单的服务器启动脚本
"""

import uvicorn

if __name__ == "__main__":
    print("启动合同审计系统...")
    uvicorn.run(
        "ContractAudit.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # 关闭reload避免问题
        log_level="info"
    ) 