# 合同审计系统Makefile
# 企业级开发和部署工具

.PHONY: help install test lint format clean build run docker-build docker-run docker-stop docker-clean

# 默认目标
help:
	@echo "合同审计系统 - 可用命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  install     - 安装依赖"
	@echo "  test        - 运行测试"
	@echo "  test-cov    - 运行测试并生成覆盖率报告"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo ""
	@echo "运行命令:"
	@echo "  run         - 启动开发服务器"
	@echo "  run-prod    - 启动生产服务器"
	@echo ""
	@echo "Docker命令:"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 启动Docker服务"
	@echo "  docker-stop  - 停止Docker服务"
	@echo "  docker-clean - 清理Docker资源"
	@echo ""
	@echo "部署命令:"
	@echo "  deploy      - 部署到生产环境"
	@echo "  backup      - 备份数据"
	@echo "  restore     - 恢复数据"

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "安装开发依赖..."
	pip install -r requirements-dev.txt || echo "开发依赖文件不存在，跳过"

# 运行测试
test:
	@echo "运行单元测试..."
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	@echo "运行测试并生成覆盖率报告..."
	pytest tests/ -v --cov=ContractAudit --cov-report=html --cov-report=term-missing

# 代码检查
lint:
	@echo "运行代码检查..."
	flake8 ContractAudit/ tests/
	mypy ContractAudit/

# 代码格式化
format:
	@echo "格式化代码..."
	black ContractAudit/ tests/
	isort ContractAudit/ tests/

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage

# 启动开发服务器
run:
	@echo "启动开发服务器..."
	uvicorn ContractAudit.main:app --host 0.0.0.0 --port 8010 --reload

# 启动生产服务器
run-prod:
	@echo "启动生产服务器..."
	uvicorn ContractAudit.main:app --host 0.0.0.0 --port 8010 --workers 4

# 构建Docker镜像
docker-build:
	@echo "构建Docker镜像..."
	docker build -t contract-audit:latest .

# 启动Docker服务
docker-run:
	@echo "启动Docker服务..."
	docker-compose up -d

# 停止Docker服务
docker-stop:
	@echo "停止Docker服务..."
	docker-compose down

# 清理Docker资源
docker-clean:
	@echo "清理Docker资源..."
	docker-compose down -v
	docker system prune -f

# 查看Docker日志
docker-logs:
	@echo "查看Docker日志..."
	docker-compose logs -f

# 部署到生产环境
deploy:
	@echo "部署到生产环境..."
	@echo "请确保已配置生产环境变量"
	docker-compose -f docker-compose.prod.yml up -d

# 备份数据
backup:
	@echo "备份数据..."
	@mkdir -p backups
	docker-compose exec milvus-standalone milvus backup --collection-name contract_vectors --backup-path /backup
	docker cp contract-audit-milvus-standalone-1:/backup ./backups/milvus-$(shell date +%Y%m%d_%H%M%S)

# 恢复数据
restore:
	@echo "恢复数据..."
	@echo "请指定备份文件路径: make restore BACKUP_PATH=backups/milvus_20240101_120000"

# 健康检查
health-check:
	@echo "检查服务健康状态..."
	curl -f http://localhost:8001/health || echo "服务未运行"

# 性能测试
perf-test:
	@echo "运行性能测试..."
	python -m pytest tests/test_performance.py -v

# 安全扫描
security-scan:
	@echo "运行安全扫描..."
	safety check
	bandit -r ContractAudit/

# 生成API文档
docs:
	@echo "生成API文档..."
	python -c "import uvicorn; uvicorn.run('ContractAudit.main:app', host='0.0.0.0', port=8001)" &
	@sleep 5
	curl http://localhost:8001/docs > docs/api_docs.html
	@kill %1

# 数据库迁移
migrate:
	@echo "运行数据库迁移..."
	@echo "当前版本暂不支持数据库迁移"

# 初始化数据库
init-db:
	@echo "初始化数据库..."
	@echo "请确保Milvus服务已启动"

# 监控服务状态
monitor:
	@echo "监控服务状态..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"
	@echo "Kibana: http://localhost:5601"

# 快速开发设置
dev-setup:
	@echo "设置开发环境..."
	cp env.example .env
	@echo "请编辑 .env 文件配置环境变量"
	make install
	make format
	@echo "开发环境设置完成"

# 生产环境设置
prod-setup:
	@echo "设置生产环境..."
	@echo "请确保已配置生产环境变量"
	make docker-build
	make docker-run
	@echo "生产环境设置完成"

# 完整测试套件
test-all:
	@echo "运行完整测试套件..."
	make lint
	make test-cov
	make security-scan
	make perf-test
	@echo "所有测试完成"

# 发布准备
release-prep:
	@echo "准备发布..."
	make clean
	make test-all
	make docker-build
	@echo "发布准备完成"

# 显示系统信息
info:
	@echo "系统信息:"
	@echo "Python版本: $(shell python --version)"
	@echo "Docker版本: $(shell docker --version)"
	@echo "Docker Compose版本: $(shell docker-compose --version)"
	@echo "当前目录: $(shell pwd)"
	@echo "Git分支: $(shell git branch --show-current 2>/dev/null || echo '未在Git仓库中')" 