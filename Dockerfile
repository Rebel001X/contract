# 合同审计系统Dockerfile
# 优化后的企业级多阶段构建，确保镜像大小和安全性

# --- 构建阶段 ---
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt .

# 关键修正：确保 pip 安装到全局目录
# 在构建阶段，默认就是root用户，所以直接安装即可
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码和配置文件
COPY ContractAudit/ ./ContractAudit/
COPY tests/ ./tests/
COPY pytest.ini .
COPY .env.example .env

# --- 运行阶段 ---
FROM python:3.11-slim

# 创建非root用户和组
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制安装好的Python包（全局安装目录）
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用程序代码和配置文件
COPY --from=builder /app/ContractAudit ./ContractAudit
COPY --from=builder /app/tests ./tests
COPY --from=builder /app/pytest.ini .
COPY --from=builder /app/.env .env

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/uploads /app/temp && \
    chown -R appuser:appuser /app

# 切换到非root用户，增强安全性
USER appuser

# 暴露端口
EXPOSE 8001

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "-m", "uvicorn", "ContractAudit.main:app", "--host", "0.0.0.0", "--port", "8010"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8010/health')" || exit 1