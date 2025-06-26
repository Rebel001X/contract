# 合同审计系统Dockerfile
# 企业级多阶段构建，优化镜像大小和安全性

# 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到用户目录
RUN pip install --no-cache-dir --user -r requirements.txt

# 复制应用代码
COPY ContractAudit/ ./ContractAudit/
COPY tests/ ./tests/
COPY pytest.ini .
COPY .env.example .env

# 运行阶段
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /usr/local

# 复制应用代码
COPY --from=builder /app/ContractAudit ./ContractAudit
COPY --from=builder /app/tests ./tests
COPY --from=builder /app/pytest.ini .
COPY --from=builder /app/.env .env

# 创建必要的目录
RUN mkdir -p logs uploads temp && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
ENTRYPOINT ["python", "-m", "uvicorn", "ContractAudit.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8001"] 