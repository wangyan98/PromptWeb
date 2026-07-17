# PromptWeb — 文生图 Prompt 管理展示网站

一个面向个人的文生图 Prompt 管理与展示工具，支持 Prompt 的智能拆分、难词提取、图片关联管理。

## 技术栈

- **前端**: Vue 3 + Vite + TypeScript
- **后端**: Python FastAPI + SQLAlchemy 2.0
- **数据库**: PostgreSQL 16
- **图片存储**: MinIO
- **AI**: Claude API

## 快速开始

### 前置要求

- Docker & Docker Compose
- Anthropic API Key (用于 AI 拆分功能)

### 启动

```bash
# 1. 复制环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 2. 启动所有服务
docker compose up -d

# 3. 运行数据库迁移
docker compose run --rm backend alembic upgrade head

# 4. 填充预设数据
docker compose run --rm backend python -m app.seed

# 5. 初始化 MinIO bucket (首次启动自动完成)
```

### 访问

- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### 导入现有的 Excel 数据

1. 打开 http://localhost:5173/import
2. 上传 Excel 文件（支持 `.xlsx`）
3. 预览解析结果
4. 确认导入

### 使用 AI 拆分 Prompt

导入 Prompt 后，使用 Claude Code Skill 进行拆分：

```bash
# 拆分单条 Prompt
claude "使用 prompt-split skill 拆分 prompt_id=1"

# 批量导入并拆分
claude "使用 prompt-import skill 导入 ./data/prompts.xlsx"
```

## 项目结构

```
prompt-web/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── api/             # API 路由
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 校验
│   │   ├── services/        # 业务逻辑
│   │   └── skills/          # AI Skill 定义
│   └── alembic/             # 数据库迁移
├── frontend/
│   └── src/
│       ├── views/           # 页面组件
│       ├── components/      # 通用组件
│       ├── api/             # API 封装
│       └── styles/          # 主题样式
└── docs/
    └── superpowers/
        ├── specs/           # 设计文档
        └── plans/           # 实现计划
```
