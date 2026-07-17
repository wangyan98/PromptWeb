# PromptWeb — 文生图 Prompt 管理展示网站 设计文档

> 日期：2026-07-17
> 状态：已确认

## 1. 项目概述

一个面向个人的文生图 Prompt 管理与展示工具，支持 Prompt 的智能拆分、难词提取、图片关联管理。架构预留公开展示扩展能力。

---

## 2. 技术栈

| 层 | 选择 |
|------|------|
| 前端 | Vue 3 (Composition API) + Vite |
| 后端 | Python FastAPI |
| 数据库 | PostgreSQL |
| 图片存储 | MinIO（上传） + 外链 URL 双模式 |
| AI 能力 | Claude API，通过 Claude Code Skill 调用 |
| 容器化 | Docker Compose（一键启动） |

---

## 3. 数据模型

```
┌─────────────────┐
│ StatementType   │  语句类型标签（镜头角度、场景主体...）
│  - id           │
│  - name         │  显示名称
│  - color        │  展示颜色标记（HEX）
│  - sort_order   │  排序
└────────┬────────┘
         │ 逻辑关联（无 DB 外键）
         ▼
┌─────────────────┐       ┌──────────────────┐
│   Statement     │       │   PromptWord     │  高亮难词
│  - id           │ 1:N   │  - id            │
│  - prompt_id ───┼──────►│  - word_en       │  英文单词
│  - text_en      │       │  - word_zh       │  中文释义
│  - text_zh      │       │  - statement_id  │  所属语句
│  - sort_order   │       │  - prompt_id     │  所属 Prompt
│  - type_id      │       │  - position_start│  在原文中的起始位置
└────────┬────────┘       │  - position_end  │  在原文中的结束位置
         │ N:1             └──────────────────┘
         ▼
┌─────────────────┐       ┌──────────────────┐
│    Prompt       │       │   PromptImage    │
│  - id           │       │  - id            │
│  - title        │ 1:N   │  - prompt_id     │
│  - text_en_full ├──────►│  - url           │  MinIO 路径或外链 URL
│  - text_zh_full │       │  - storage_type  │  'minio' | 'url'
│  - category     │       │  - sort_order    │  排序
│  - source_file  │       │  - width         │  图片宽度（可选）
│  - created_at   │       │  - height        │  图片高度（可选）
│  - updated_at   │       └──────────────────┘
└─────────────────┘
```

### 关键约束
- `Statement.type_id` 与 `StatementType.id` 之间**不建立数据库外键约束**，仅做逻辑关联
- `PromptWord` 同时关联 `statement_id` 和 `prompt_id`，支持按语句/按 Prompt 两种查询路径
- 删除 Prompt 时级联删除关联的 Statement、PromptWord、PromptImage
- 图片有两种存储方式：MinIO 存储（`storage_type='minio'`）和外部链接（`storage_type='url'`）

---

## 4. API 设计

所有接口前缀 `/api`，返回 JSON。

### Prompt
```
GET    /api/prompts              # 列表（?page=1&page_size=20&search=&category=）
POST   /api/prompts              # 新增
GET    /api/prompts/:id          # 详情（含 statements, words, images）
PUT    /api/prompts/:id          # 编辑
DELETE /api/prompts/:id          # 删除（级联）
```

### Statement
```
GET    /api/prompts/:id/statements   # 获取某 Prompt 所有拆分语句
POST   /api/prompts/:id/statements   # 新增语句
PUT    /api/statements/:id           # 编辑
DELETE /api/statements/:id           # 删除
```

### PromptWord
```
GET    /api/statements/:id/words     # 获取某语句关联的单词
POST   /api/statements/:id/words     # 新增单词
DELETE /api/words/:id                # 删除单词
```

### PromptImage
```
POST   /api/prompts/:id/images       # 上传图片（multipart → MinIO）或添加外链
DELETE /api/images/:id               # 删除图片（MinIO 同步删除）
GET    /api/images/:id/file          # 代理 MinIO 文件（可选鉴权）
```

### StatementType
```
GET    /api/statement-types          # 获取所有类型
POST   /api/statement-types          # 新增类型
PUT    /api/statement-types/:id      # 编辑
DELETE /api/statement-types/:id      # 删除
```

### Import
```
POST   /api/import/excel             # Excel 导入（接收文件，返回解析预览）
POST   /api/import/confirm           # 确认导入（将预览数据写入库）
```

### 统一响应格式
```json
{
  "code": 0,
  "data": {},
  "message": "ok"
}
```

### 分页格式
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 5. 前端设计

### 主题
- **深色背景**（`#1a1a2e` 或类似基调）
- 高亮单词使用**亮黄色背景**（`#ffe066` 或类似），文字深色
- 语句类型标签使用各自定义的颜色

### 路由
```
/                          → 重定向到 /prompts
/prompts                   → Prompt 列表页
/prompts/:id               → Prompt 详情页（左右分栏）
/prompts/new               → 新增 Prompt
/prompts/:id/edit          → 编辑 Prompt
/statement-types           → 语句类型管理
/import                    → Excel 导入页
```

### 核心页面

#### 列表页 (`/prompts`)
- 顶部：搜索框 + 分类筛选下拉 + 新增按钮 + 导入按钮
- 主体：表格布局，每行三列（缩略图 | 英文 Prompt 截断 | 中文翻译截断）
- 分页器在底部

#### 详情页 (`/prompts/:id`) 左右分栏
**左栏**：
- 完整英文 Prompt 文本
- 完整中文翻译
- 拆分语句列表，每条显示：`[类型标签] 英文语句 / 中文翻译`
- 单击某条语句 → 该语句中英文同时以亮黄色高亮
- 在高亮语句中再次点击某个单词 → 该单词在 Prompt 全文和语句中高亮，右侧单词卡片区展示

**右栏**：
- 图片墙（网格布局，支持放大查看、上传新图、删除）
- 高亮单词卡片区（单词卡片：英文 + 中文释义，亮黄色背景）

**交互状态**：
- 默认：无高亮
- 点击语句：语句中英文高亮（亮黄色）
- 点击单词：单词高亮 + 右侧单词卡片区展示
- 点击空白区域：清除所有高亮

#### 新增/编辑页 (`/prompts/new`, `/prompts/:id/edit`)
- 基本信息表单：标题、英文 Prompt、中文翻译、分类
- 语句拆分编辑器
- 图片上传/外链管理

#### 导入页 (`/import`)
- 上传 Excel 文件 → 预览解析结果（AI 分析后的数据） → 确认导入

---

## 6. AI Skill 设计

### Skill 1: `prompt-import` — Excel 导入分析

**触发**：用户在导入页上传 Excel 后调用

**流程**：
1. 解析 Excel 文件，读取列名和前几行样本数据
2. AI 识别：哪列是英文 Prompt、哪列是中文翻译、哪列是分类
3. 逐行提取数据，返回结构化预览（JSON）
4. 用户确认后，调用 API 批量写入数据库

### Skill 2: `prompt-split` — Prompt 拆句 + 难词提取

**触发**：Prompt 入库后自动触发，或手动对单条 Prompt 触发

**流程**：
1. 输入英文 Prompt + 中文翻译
2. AI 按语义边界拆分为 3-8 条短句，每句标注类型标签、提供中文翻译
3. AI 识别低频/专业词汇，提取英文单词 + 中文释义，跳过常见简单词
4. 记录单词在原文中的起止位置
5. 调用 API 批量写入 statements 和 words

### Skill 定义文件
- `backend/skills/prompt-import.md`
- `backend/skills/prompt-split.md`

---

## 7. 预设语句类型

| 名称 | 说明 | 颜色 |
|------|------|------|
| 固定开头 | Generate epic UE5... 等固定句式前缀 | `#4fc3f7` |
| 光照氛围 | 光线、天气、情绪氛围描述 | `#ffb74d` |
| 镜头构图 | 镜头角度、景别、构图方式 | `#81c784` |
| 场景主体 | 画面核心主体/被摄物 | `#e57373` |
| 材质细节 | 表面材质、纹理、细节层次 | `#ba68c8` |
| 画质风格 | 分辨率、渲染风格、艺术风格 | `#90a4ae` |
| 色彩色调 | 颜色偏好、色调方向 | `#f06292` |
| 环境背景 | 场景背景、环境元素 | `#4db6ac` |

用户可在类型管理页自由增删改。

---

## 8. 基础设施

### Docker Compose 服务

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 5173 | Vite dev server，`/api` 代理到后端 |
| backend | 8000 | FastAPI + uvicorn --reload |
| postgres | 5432 | 数据挂载 `./pg-data/` |
| minio | 9000 | S3 兼容 API |
| minio-console | 9001 | MinIO Web 管理界面 |

### MinIO
- Bucket：`prompt-images`（公开读取）
- 文件路径：`{bucket}/{prompt_id}/{uuid}.{ext}`

### 环境变量
```bash
POSTGRES_USER=promptweb
POSTGRES_PASSWORD=promptweb123
POSTGRES_DB=promptweb
DATABASE_URL=postgresql+asyncpg://promptweb:promptweb123@postgres:5432/promptweb

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=prompt-images
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

ANTHROPIC_API_KEY=sk-ant-...
```

---

## 9. 目录结构

```
prompt-web/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── api/
│   │   │   ├── prompts.py
│   │   │   ├── statements.py
│   │   │   ├── words.py
│   │   │   ├── images.py
│   │   │   ├── statement_types.py
│   │   │   └── import_.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── prompt_service.py
│   │   │   ├── import_service.py
│   │   │   ├── split_service.py
│   │   │   └── minio_service.py
│   │   └── skills/
│   │       ├── prompt-import.md
│   │       └── prompt-split.md
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── views/
│   │   ├── components/
│   │   └── styles/
│   │       ├── variables.css
│   │       └── global.css
│   └── public/
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-07-17-prompt-web-design.md
├── pg-data/           # gitignore
└── minio-data/        # gitignore
```

---

## 10. 非功能需求

- **性能**：列表页首屏加载 < 1s，单次请求 ≤ 20 条
- **可扩展**：预留公开访问模式（去除编辑入口、只读浏览）
- **数据安全**：MinIO bucket 不暴露公网，图片通过后端 API 代理访问

---

## 11. 不在本次范围

- 用户登录/权限系统（个人使用阶段不需要）
- CI/CD 流水线
- 生产级部署配置（仅提供 dev 环境 docker-compose）
- 多语言国际化（仅中英文 Prompt 内容）
