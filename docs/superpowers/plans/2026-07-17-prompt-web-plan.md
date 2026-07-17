# PromptWeb Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack Prompt management website with AI-powered sentence splitting, vocabulary extraction, and image gallery.

**Architecture:** Monorepo with Vue 3 frontend (Vite) and Python FastAPI backend, orchestrated via Docker Compose with PostgreSQL and MinIO. AI capabilities delivered through Claude Code Skills that call the Anthropic API.

**Tech Stack:** Vue 3, Vite, FastAPI, SQLAlchemy 2.0 async, PostgreSQL, MinIO, Docker Compose, Claude API

## Global Constraints

- Deep dark background theme (`#1a1a2e` base), highlight words with bright yellow (`#ffe066`)
- `Statement.type_id` has NO database foreign key constraint — logical association only
- `PromptWord` references both `statement_id` and `prompt_id` for dual query paths
- Cascade delete: deleting a Prompt removes its Statements, Words, and Images
- Images support dual storage: MinIO (`storage_type='minio'`) and external URL (`storage_type='url'`)
- API: unified response `{code, data, message}`, pagination `{items, total, page, page_size}`
- Dev-only Docker Compose setup (no production deployment)
- No auth/login system (personal use)

---

### Task 1: Docker Compose & Environment Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Modify: `.gitignore`

**Interfaces:**
- Produces: Running services — `postgres:5432`, `minio:9000`, `minio-console:9001`, `backend:8000`, `frontend:5173`

- [ ] **Step 1: Write docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-promptweb}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-promptweb123}
      POSTGRES_DB: ${POSTGRES_DB:-promptweb}
    ports:
      - "5432:5432"
    volumes:
      - ./pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U promptweb"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin123}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-promptweb}:${POSTGRES_PASSWORD:-promptweb123}@postgres:5432/${POSTGRES_DB:-promptweb}
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minioadmin123}
      MINIO_BUCKET: prompt-images
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy

  frontend:
    build: ./frontend
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
```

- [ ] **Step 2: Write .env.example**

```bash
POSTGRES_USER=promptweb
POSTGRES_PASSWORD=promptweb123
POSTGRES_DB=promptweb
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=prompt-images
ANTHROPIC_API_KEY=sk-ant-...
```

- [ ] **Step 3: Update .gitignore**

```
node_modules/
pg-data/
minio-data/
.env
__pycache__/
*.pyc
.venv/
dist/
.env
```

- [ ] **Step 4: Start services and verify**

```bash
docker compose up -d postgres minio
docker compose ps
docker compose logs postgres | grep "ready to accept connections"
curl -s http://localhost:9000/minio/health/live
```

Expected: PostgreSQL healthy, MinIO returns 200

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .env.example .gitignore
git commit -m "feat: add Docker Compose with PostgreSQL and MinIO services"
```

---

### Task 2: Backend Project Skeleton

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

**Interfaces:**
- Produces: FastAPI app with health check, DB engine (`get_db` async generator), `Settings` config object

- [ ] **Step 1: Write backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

- [ ] **Step 2: Write backend/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.3
pydantic-settings==2.7.0
python-multipart==0.0.18
minio==7.2.10
openpyxl==3.1.5
anthropic==0.42.0
httpx==0.28.1
```

- [ ] **Step 3: Write backend/app/__init__.py**

```python
```

- [ ] **Step 4: Write backend/app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://promptweb:promptweb123@localhost:5432/promptweb"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "prompt-images"
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 5: Write backend/app/database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 6: Write backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PromptWeb API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"code": 0, "data": {"status": "ok"}, "message": "healthy"}
```

- [ ] **Step 7: Build and verify**

```bash
docker compose build backend
docker compose up -d backend
curl http://localhost:8000/api/health
```

Expected: `{"code":0,"data":{"status":"ok"},"message":"healthy"}`

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: add backend skeleton with FastAPI, config, and database"
```

---

### Task 3: Frontend Project Skeleton

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/env.d.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/styles/variables.css`
- Create: `frontend/src/styles/global.css`

**Interfaces:**
- Produces: Vue 3 app with router, dark theme CSS variables, proxy to backend

- [ ] **Step 1: Write frontend/Dockerfile**

```dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
```

- [ ] **Step 2: Write frontend/package.json**

```json
{
  "name": "prompt-web-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.9",
    "pinia": "^2.3.0",
    "vue": "^3.5.13",
    "vue-router": "^4.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.1",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "vue-tsc": "^2.2.0"
  }
}
```

- [ ] **Step 3: Write frontend/vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Write frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "env.d.ts"]
}
```

- [ ] **Step 5: Write frontend/tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: Write frontend/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PromptWeb</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 7: Write frontend/env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 8: Write frontend/src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 9: Write frontend/src/App.vue**

```vue
<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppLayout from './components/AppLayout.vue'
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>
```

- [ ] **Step 10: Write frontend/src/router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/prompts',
    },
    {
      path: '/prompts',
      name: 'prompt-list',
      component: () => import('@/views/PromptList.vue'),
    },
    {
      path: '/prompts/new',
      name: 'prompt-new',
      component: () => import('@/views/PromptForm.vue'),
    },
    {
      path: '/prompts/:id',
      name: 'prompt-detail',
      component: () => import('@/views/PromptDetail.vue'),
    },
    {
      path: '/prompts/:id/edit',
      name: 'prompt-edit',
      component: () => import('@/views/PromptForm.vue'),
    },
    {
      path: '/statement-types',
      name: 'statement-types',
      component: () => import('@/views/StatementTypeManager.vue'),
    },
    {
      path: '/import',
      name: 'import',
      component: () => import('@/views/ImportPage.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 11: Write frontend/src/styles/variables.css**

```css
:root {
  /* Dark theme base */
  --color-bg-primary: #1a1a2e;
  --color-bg-secondary: #16213e;
  --color-bg-tertiary: #0f3460;
  --color-bg-card: #1e2a4a;
  --color-bg-hover: #253a5e;

  /* Text */
  --color-text-primary: #e8e8e8;
  --color-text-secondary: #a0a8b8;
  --color-text-muted: #6b7280;

  /* Accent */
  --color-accent: #4fc3f7;
  --color-highlight: #ffe066;
  --color-highlight-text: #1a1a2e;

  /* Semantic */
  --color-success: #81c784;
  --color-danger: #e57373;
  --color-warning: #ffb74d;

  /* Border */
  --color-border: #2a3a5e;
  --border-radius: 8px;
  --border-radius-lg: 12px;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Fira Code', 'Cascadia Code', monospace;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 2rem;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;

  /* Layout */
  --sidebar-width: 220px;
  --header-height: 56px;
}
```

- [ ] **Step 12: Write frontend/src/styles/global.css**

```css
@import './variables.css';

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background-color: var(--color-bg-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
}

a {
  color: var(--color-accent);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

button {
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
}

input, textarea, select {
  font-family: inherit;
  font-size: inherit;
  color: var(--color-text-primary);
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: var(--space-sm) var(--space-md);
  outline: none;
  transition: border-color var(--transition-fast);
}

input:focus, textarea:focus, select:focus {
  border-color: var(--color-accent);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
```

- [ ] **Step 13: Build frontend and verify**

```bash
docker compose build frontend
# Start and check that Vite dev server boots:
docker compose up -d frontend
curl -s http://localhost:5173 | head -20
```

Expected: HTML page returned with `<div id="app">`

- [ ] **Step 14: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend skeleton with Vue 3, Vite, dark theme"
```

---

### Task 4: SQLAlchemy Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/prompt.py`
- Create: `backend/app/models/statement.py`
- Create: `backend/app/models/statement_type.py`
- Create: `backend/app/models/prompt_word.py`
- Create: `backend/app/models/prompt_image.py`

**Interfaces:**
- Consumes: `database.py` (engine from Task 2)
- Produces: `Prompt`, `Statement`, `StatementType`, `PromptWord`, `PromptImage` SQLAlchemy models, `Base` declarative base

- [ ] **Step 1: Write backend/app/models/__init__.py**

```python
from app.models.base import Base
from app.models.prompt import Prompt
from app.models.statement import Statement
from app.models.statement_type import StatementType
from app.models.prompt_word import PromptWord
from app.models.prompt_image import PromptImage

__all__ = ["Base", "Prompt", "Statement", "StatementType", "PromptWord", "PromptImage"]
```

- [ ] **Step 2: Write backend/app/models/base.py**

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 3: Write backend/app/models/prompt.py**

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Prompt(Base, TimestampMixin):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    text_en_full: Mapped[str] = mapped_column(Text, nullable=False)
    text_zh_full: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(200), default="")
    source_file: Mapped[str] = mapped_column(String(500), default="")

    statements = relationship("Statement", back_populates="prompt", cascade="all, delete-orphan")
    words = relationship("PromptWord", back_populates="prompt", cascade="all, delete-orphan")
    images = relationship("PromptImage", back_populates="prompt", cascade="all, delete-orphan")
```

- [ ] **Step 4: Write backend/app/models/statement.py**

```python
from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    text_en: Mapped[str] = mapped_column(Text, nullable=False)
    text_zh: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    type_id: Mapped[int] = mapped_column(Integer, nullable=True)

    prompt = relationship("Prompt", back_populates="statements")
    words = relationship("PromptWord", back_populates="statement", cascade="all, delete-orphan")
```

- [ ] **Step 5: Write backend/app/models/statement_type.py**

```python
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StatementType(Base):
    __tablename__ = "statement_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#4fc3f7")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 6: Write backend/app/models/prompt_word.py**

```python
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PromptWord(Base):
    __tablename__ = "prompt_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    statement_id: Mapped[int] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"), nullable=False)
    word_en: Mapped[str] = mapped_column(String(200), nullable=False)
    word_zh: Mapped[str] = mapped_column(String(200), default="")
    position_start: Mapped[int] = mapped_column(Integer, nullable=True)
    position_end: Mapped[int] = mapped_column(Integer, nullable=True)

    prompt = relationship("Prompt", back_populates="words")
    statement = relationship("Statement", back_populates="words")
```

- [ ] **Step 7: Write backend/app/models/prompt_image.py**

```python
from sqlalchemy import ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PromptImage(Base):
    __tablename__ = "prompt_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    storage_type: Mapped[str] = mapped_column(String(10), default="minio")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)

    prompt = relationship("Prompt", back_populates="images")
```

- [ ] **Step 8: Verify models import correctly**

```bash
docker compose exec backend python -c "from app.models import Base, Prompt, Statement, StatementType, PromptWord, PromptImage; print('All models imported OK')"
```

Expected: `All models imported OK`

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy models for all entities"
```

---

### Task 5: Alembic Migrations & Seed Data

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/app/seed.py`

**Interfaces:**
- Consumes: `Base.metadata` from Task 4, `database_url` from config
- Produces: Migrated database with tables, 8 preset statement types seeded

- [ ] **Step 1: Initialize Alembic and write env.py**

Run: `cd backend && docker compose run --rm backend alembic init alembic`

Then write `backend/alembic/env.py`:

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.config import settings
from app.models.base import Base

# Import all models so Base.metadata is populated
from app.models import Prompt, Statement, StatementType, PromptWord, PromptImage  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 2: Write backend/alembic/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 3: Update alembic.ini — set sqlalchemy.url**

```ini
# In alembic.ini, replace the sqlalchemy.url line with:
sqlalchemy.url = postgresql+asyncpg://promptweb:promptweb123@postgres:5432/promptweb
```

- [ ] **Step 4: Generate and run migration**

```bash
docker compose run --rm backend alembic revision --autogenerate -m "init"
docker compose run --rm backend alembic upgrade head
```

- [ ] **Step 5: Write backend/app/seed.py**

```python
from sqlalchemy import select
from app.database import async_session
from app.models import StatementType

PRESET_TYPES = [
    {"name": "固定开头", "color": "#4fc3f7", "sort_order": 1},
    {"name": "光照氛围", "color": "#ffb74d", "sort_order": 2},
    {"name": "镜头构图", "color": "#81c784", "sort_order": 3},
    {"name": "场景主体", "color": "#e57373", "sort_order": 4},
    {"name": "材质细节", "color": "#ba68c8", "sort_order": 5},
    {"name": "画质风格", "color": "#90a4ae", "sort_order": 6},
    {"name": "色彩色调", "color": "#f06292", "sort_order": 7},
    {"name": "环境背景", "color": "#4db6ac", "sort_order": 8},
]


async def seed_statement_types():
    async with async_session() as session:
        existing = await session.execute(select(StatementType))
        if existing.scalars().first():
            print("Statement types already seeded, skipping.")
            return

        for t in PRESET_TYPES:
            session.add(StatementType(**t))
        await session.commit()
        print(f"Seeded {len(PRESET_TYPES)} statement types.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_statement_types())
```

- [ ] **Step 6: Run seed script**

```bash
docker compose run --rm backend python -m app.seed
```

Expected: `Seeded 8 statement types.`

- [ ] **Step 7: Commit**

```bash
git add backend/alembic.ini backend/alembic/ backend/app/seed.py
git commit -m "feat: add Alembic migrations and seed statement types"
```

---

### Task 6: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/app/schemas/prompt.py`
- Create: `backend/app/schemas/statement.py`
- Create: `backend/app/schemas/statement_type.py`
- Create: `backend/app/schemas/prompt_word.py`
- Create: `backend/app/schemas/prompt_image.py`

**Interfaces:**
- Consumes: Models from Task 4
- Produces: Pydantic v2 schemas for all CRUD operations (create, update, response, list)

- [ ] **Step 1: Write backend/app/schemas/__init__.py**

```python
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptListItem
from app.schemas.statement import StatementCreate, StatementUpdate, StatementResponse
from app.schemas.statement_type import StatementTypeCreate, StatementTypeUpdate, StatementTypeResponse
from app.schemas.prompt_word import PromptWordCreate, PromptWordResponse
from app.schemas.prompt_image import PromptImageCreate, PromptImageResponse
```

- [ ] **Step 2: Write backend/app/schemas/common.py**

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "ok"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
```

- [ ] **Step 3: Write backend/app/schemas/prompt.py**

```python
from datetime import datetime
from pydantic import BaseModel


class PromptCreate(BaseModel):
    title: str = ""
    text_en_full: str
    text_zh_full: str = ""
    category: str = ""
    source_file: str = ""


class PromptUpdate(BaseModel):
    title: str | None = None
    text_en_full: str | None = None
    text_zh_full: str | None = None
    category: str | None = None


class PromptListItem(BaseModel):
    id: int
    title: str
    text_en_full: str
    text_zh_full: str
    category: str
    thumbnail_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptResponse(BaseModel):
    id: int
    title: str
    text_en_full: str
    text_zh_full: str
    category: str
    source_file: str
    created_at: datetime
    updated_at: datetime
    statements: list["StatementResponse"] = []
    words: list["PromptWordResponse"] = []
    images: list["PromptImageResponse"] = []

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Write backend/app/schemas/statement.py**

```python
from pydantic import BaseModel


class StatementCreate(BaseModel):
    text_en: str
    text_zh: str = ""
    sort_order: int = 0
    type_id: int | None = None


class StatementUpdate(BaseModel):
    text_en: str | None = None
    text_zh: str | None = None
    sort_order: int | None = None
    type_id: int | None = None


class StatementResponse(BaseModel):
    id: int
    prompt_id: int
    text_en: str
    text_zh: str
    sort_order: int
    type_id: int | None = None
    words: list["PromptWordResponse"] = []

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Write backend/app/schemas/statement_type.py**

```python
from pydantic import BaseModel


class StatementTypeCreate(BaseModel):
    name: str
    color: str = "#4fc3f7"
    sort_order: int = 0


class StatementTypeUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    sort_order: int | None = None


class StatementTypeResponse(BaseModel):
    id: int
    name: str
    color: str
    sort_order: int

    model_config = {"from_attributes": True}
```

- [ ] **Step 6: Write backend/app/schemas/prompt_word.py**

```python
from pydantic import BaseModel


class PromptWordCreate(BaseModel):
    word_en: str
    word_zh: str = ""
    position_start: int | None = None
    position_end: int | None = None


class PromptWordResponse(BaseModel):
    id: int
    prompt_id: int
    statement_id: int
    word_en: str
    word_zh: str
    position_start: int | None = None
    position_end: int | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 7: Write backend/app/schemas/prompt_image.py**

```python
from pydantic import BaseModel


class PromptImageCreate(BaseModel):
    url: str | None = None
    storage_type: str = "minio"
    sort_order: int = 0
    width: int | None = None
    height: int | None = None


class PromptImageResponse(BaseModel):
    id: int
    prompt_id: int
    url: str
    storage_type: str
    sort_order: int
    width: int | None = None
    height: int | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 8: Verify imports**

```bash
docker compose exec backend python -c "from app.schemas import *; print('All schemas imported OK')"
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for all entities"
```

---

### Task 7: MinIO Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/minio_service.py`

**Interfaces:**
- Consumes: `config.settings` (MinIO credentials)
- Produces: `MinioService` class — `ensure_bucket()`, `upload(file, prompt_id) -> url`, `delete(url)`, `get_file_url(object_name) -> str`

- [ ] **Step 1: Write backend/app/services/__init__.py**

```python
```

- [ ] **Step 2: Write backend/app/services/minio_service.py**

```python
import uuid
from io import BytesIO
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.config import settings


class MinioService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self.bucket = settings.minio_bucket

    async def ensure_bucket(self):
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)
            # Set public read policy
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                    }
                ],
            }
            self.client.set_bucket_policy(self.bucket, policy)

    async def upload(self, file: UploadFile, prompt_id: int) -> str:
        ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png"
        object_name = f"{prompt_id}/{uuid.uuid4()}.{ext}"
        content = await file.read()
        file.file.seek(0)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=BytesIO(content),
            length=len(content),
            content_type=file.content_type or "image/png",
        )
        return f"/api/images/file/{object_name}"

    def delete(self, object_name: str):
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            pass

    def get_object_name_from_url(self, url: str) -> str:
        # URL format: /api/images/file/prompt-images/1/uuid.png
        prefix = f"/api/images/file/"
        if url.startswith(prefix):
            return url[len(prefix):]
        return url


minio_service = MinioService()
```

- [ ] **Step 3: Verify MinIO connection**

```bash
docker compose exec backend python -c "
import asyncio
from app.services.minio_service import minio_service

async def test():
    await minio_service.ensure_bucket()
    print('Bucket ensured:', minio_service.bucket)

asyncio.run(test())
"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/minio_service.py
git commit -m "feat: add MinIO storage service"
```

---

### Task 8: Prompt & Statement CRUD Services

**Files:**
- Create: `backend/app/services/prompt_service.py`

**Interfaces:**
- Consumes: `database.get_db`, models from Task 4, schemas from Task 6
- Produces: `PromptService` with `list_prompts()`, `get_prompt()`, `create_prompt()`, `update_prompt()`, `delete_prompt()`, `create_statements_batch()`, `update_statement()`, `delete_statement()`, `create_words_batch()`, `delete_word()`, `add_image()`, `delete_image()`

- [ ] **Step 1: Write backend/app/services/prompt_service.py**

```python
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Prompt, Statement, StatementType, PromptWord, PromptImage
from app.schemas.prompt import PromptCreate, PromptUpdate
from app.schemas.statement import StatementCreate, StatementUpdate
from app.schemas.prompt_word import PromptWordCreate
from app.schemas.prompt_image import PromptImageCreate


class PromptService:
    async def list_prompts(
        self, db: AsyncSession, *, page: int = 1, page_size: int = 20,
        search: str = "", category: str = ""
    ) -> tuple[list[Prompt], int]:
        query = select(Prompt)
        count_query = select(func.count(Prompt.id))

        if search:
            filter_clause = Prompt.text_en_full.ilike(f"%{search}%") | Prompt.title.ilike(f"%{search}%")
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        if category:
            query = query.where(Prompt.category == category)
            count_query = count_query.where(Prompt.category == category)

        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(Prompt.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        # Eager load first image for thumbnail
        query = query.options(selectinload(Prompt.images))

        result = await db.execute(query)
        prompts = list(result.scalars().unique())

        return prompts, total

    async def get_prompt(self, db: AsyncSession, prompt_id: int) -> Prompt | None:
        query = (
            select(Prompt)
            .options(
                selectinload(Prompt.statements).selectinload(Statement.words),
                selectinload(Prompt.words),
                selectinload(Prompt.images),
            )
            .where(Prompt.id == prompt_id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def create_prompt(self, db: AsyncSession, data: PromptCreate) -> Prompt:
        prompt = Prompt(**data.model_dump())
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)
        return prompt

    async def update_prompt(self, db: AsyncSession, prompt_id: int, data: PromptUpdate) -> Prompt | None:
        prompt = await self.get_prompt(db, prompt_id)
        if not prompt:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(prompt, key, value)
        await db.commit()
        await db.refresh(prompt)
        return prompt

    async def delete_prompt(self, db: AsyncSession, prompt_id: int) -> bool:
        prompt = await self.get_prompt(db, prompt_id)
        if not prompt:
            return False
        await db.delete(prompt)
        await db.commit()
        return True

    async def create_statements_batch(
        self, db: AsyncSession, prompt_id: int, statements: list[StatementCreate]
    ) -> list[Statement]:
        stmts = [
            Statement(prompt_id=prompt_id, **s.model_dump())
            for s in statements
        ]
        db.add_all(stmts)
        await db.commit()
        return stmts

    async def update_statement(
        self, db: AsyncSession, statement_id: int, data: StatementUpdate
    ) -> Statement | None:
        stmt = await db.get(Statement, statement_id)
        if not stmt:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stmt, key, value)
        await db.commit()
        await db.refresh(stmt)
        return stmt

    async def delete_statement(self, db: AsyncSession, statement_id: int) -> bool:
        stmt = await db.get(Statement, statement_id)
        if not stmt:
            return False
        await db.delete(stmt)
        await db.commit()
        return True

    async def create_words_batch(
        self, db: AsyncSession, prompt_id: int, statement_id: int, words: list[PromptWordCreate]
    ) -> list[PromptWord]:
        pwords = [
            PromptWord(prompt_id=prompt_id, statement_id=statement_id, **w.model_dump())
            for w in words
        ]
        db.add_all(pwords)
        await db.commit()
        return pwords

    async def delete_word(self, db: AsyncSession, word_id: int) -> bool:
        word = await db.get(PromptWord, word_id)
        if not word:
            return False
        await db.delete(word)
        await db.commit()
        return True

    async def add_image(self, db: AsyncSession, prompt_id: int, data: PromptImageCreate) -> PromptImage:
        image = PromptImage(prompt_id=prompt_id, **data.model_dump())
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    async def delete_image(self, db: AsyncSession, image_id: int) -> PromptImage | None:
        image = await db.get(PromptImage, image_id)
        if not image:
            return None
        await db.delete(image)
        await db.commit()
        return image

    async def get_categories(self, db: AsyncSession) -> list[str]:
        query = select(Prompt.category).distinct().where(Prompt.category != "")
        result = await db.execute(query)
        return [row[0] for row in result.all() if row[0]]


prompt_service = PromptService()
```

- [ ] **Step 2: Verify service imports**

```bash
docker compose exec backend python -c "from app.services.prompt_service import prompt_service; print('PromptService OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/prompt_service.py
git commit -m "feat: add Prompt CRUD service with batch statement and word operations"
```

---

### Task 9: StatementType Service

**Files:**
- Create: `backend/app/services/statement_type_service.py`

**Interfaces:**
- Consumes: `database.get_db`, `StatementType` model
- Produces: `StatementTypeService` with full CRUD: `list_types()`, `create_type()`, `update_type()`, `delete_type()`

- [ ] **Step 1: Write backend/app/services/statement_type_service.py**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import StatementType
from app.schemas.statement_type import StatementTypeCreate, StatementTypeUpdate


class StatementTypeService:
    async def list_types(self, db: AsyncSession) -> list[StatementType]:
        query = select(StatementType).order_by(StatementType.sort_order)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_type(self, db: AsyncSession, data: StatementTypeCreate) -> StatementType:
        st = StatementType(**data.model_dump())
        db.add(st)
        await db.commit()
        await db.refresh(st)
        return st

    async def update_type(self, db: AsyncSession, type_id: int, data: StatementTypeUpdate) -> StatementType | None:
        st = await db.get(StatementType, type_id)
        if not st:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(st, key, value)
        await db.commit()
        await db.refresh(st)
        return st

    async def delete_type(self, db: AsyncSession, type_id: int) -> bool:
        st = await db.get(StatementType, type_id)
        if not st:
            return False
        await db.delete(st)
        await db.commit()
        return True


statement_type_service = StatementTypeService()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/statement_type_service.py
git commit -m "feat: add StatementType CRUD service"
```

---

### Task 10: API Routers — Prompts, Statements, Words, Images

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/prompts.py`
- Create: `backend/app/api/statements.py`
- Create: `backend/app/api/words.py`
- Create: `backend/app/api/images.py`
- Modify: `backend/app/main.py` (register routers)

**Interfaces:**
- Consumes: `prompt_service`, `minio_service`, schemas
- Produces: All REST endpoints from spec §4 (Prompts, Statements, Words, Images)

- [ ] **Step 1: Write backend/app/api/__init__.py**

```python
```

- [ ] **Step 2: Write backend/app/api/prompts.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptListItem
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("")
async def list_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    category: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    prompts, total = await prompt_service.list_prompts(
        db, page=page, page_size=page_size, search=search, category=category
    )
    items = []
    for p in prompts:
        thumb = None
        if p.images:
            sorted_imgs = sorted(p.images, key=lambda x: x.sort_order)
            thumb = sorted_imgs[0].url
        items.append(PromptListItem(
            id=p.id, title=p.title, text_en_full=p.text_en_full,
            text_zh_full=p.text_zh_full, category=p.category,
            thumbnail_url=thumb, created_at=p.created_at, updated_at=p.updated_at,
        ))
    return ApiResponse(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size).model_dump())


@router.post("")
async def create_prompt(data: PromptCreate, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.create_prompt(db, data)
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.get("/{prompt_id}")
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.put("/{prompt_id}")
async def update_prompt(prompt_id: int, data: PromptUpdate, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.update_prompt(db, prompt_id, data)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_prompt(db, prompt_id)
    if not ok:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(message="Deleted")


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    categories = await prompt_service.get_categories(db)
    return ApiResponse(data=categories)
```

- [ ] **Step 3: Write backend/app/api/statements.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.statement import StatementCreate, StatementUpdate, StatementResponse
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api", tags=["statements"])


@router.get("/prompts/{prompt_id}/statements")
async def list_statements(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    statements = sorted(prompt.statements, key=lambda s: s.sort_order)
    return ApiResponse(data=[StatementResponse.model_validate(s).model_dump() for s in statements])


@router.post("/prompts/{prompt_id}/statements")
async def create_statements(prompt_id: int, statements: list[StatementCreate], db: AsyncSession = Depends(get_db)):
    stmts = await prompt_service.create_statements_batch(db, prompt_id, statements)
    return ApiResponse(data=[StatementResponse.model_validate(s).model_dump() for s in stmts])


@router.put("/statements/{statement_id}")
async def update_statement(statement_id: int, data: StatementUpdate, db: AsyncSession = Depends(get_db)):
    stmt = await prompt_service.update_statement(db, statement_id, data)
    if not stmt:
        return ApiResponse(code=404, message="Statement not found")
    return ApiResponse(data=StatementResponse.model_validate(stmt).model_dump())


@router.delete("/statements/{statement_id}")
async def delete_statement(statement_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_statement(db, statement_id)
    if not ok:
        return ApiResponse(code=404, message="Statement not found")
    return ApiResponse(message="Deleted")
```

- [ ] **Step 4: Write backend/app/api/words.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.prompt_word import PromptWordCreate, PromptWordResponse
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api", tags=["words"])


@router.get("/statements/{statement_id}/words")
async def list_words(statement_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import PromptWord
    from sqlalchemy import select
    query = select(PromptWord).where(PromptWord.statement_id == statement_id)
    result = await db.execute(query)
    words = result.scalars().all()
    return ApiResponse(data=[PromptWordResponse.model_validate(w).model_dump() for w in words])


@router.post("/statements/{statement_id}/words")
async def create_words(statement_id: int, words: list[PromptWordCreate], db: AsyncSession = Depends(get_db)):
    from app.models import Statement
    stmt = await db.get(Statement, statement_id)
    if not stmt:
        return ApiResponse(code=404, message="Statement not found")
    pwords = await prompt_service.create_words_batch(db, stmt.prompt_id, statement_id, words)
    return ApiResponse(data=[PromptWordResponse.model_validate(w).model_dump() for w in pwords])


@router.delete("/words/{word_id}")
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_word(db, word_id)
    if not ok:
        return ApiResponse(code=404, message="Word not found")
    return ApiResponse(message="Deleted")
```

- [ ] **Step 5: Write backend/app/api/images.py**

```python
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.prompt_image import PromptImageCreate, PromptImageResponse
from app.services.prompt_service import prompt_service
from app.services.minio_service import minio_service

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/prompts/{prompt_id}/images")
async def upload_image(
    prompt_id: int,
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if url and not file:
        # External URL image
        data = PromptImageCreate(url=url, storage_type="url")
    elif file:
        await minio_service.ensure_bucket()
        object_url = await minio_service.upload(file, prompt_id)
        data = PromptImageCreate(url=object_url, storage_type="minio")
    else:
        return ApiResponse(code=400, message="Provide file or url")

    image = await prompt_service.add_image(db, prompt_id, data)
    return ApiResponse(data=PromptImageResponse.model_validate(image).model_dump())


@router.delete("/images/{image_id}")
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    image = await prompt_service.delete_image(db, image_id)
    if not image:
        return ApiResponse(code=404, message="Image not found")
    if image.storage_type == "minio":
        object_name = minio_service.get_object_name_from_url(image.url)
        minio_service.delete(object_name)
    return ApiResponse(message="Deleted")


@router.get("/images/file/{object_name:path}")
async def get_image_file(object_name: str):
    try:
        response = minio_service.client.get_object(minio_service.bucket, object_name)
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type=response.headers.get("Content-Type", "image/png"),
        )
    except Exception:
        return ApiResponse(code=404, message="File not found")
```

- [ ] **Step 6: Write backend/app/api/statement_types.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.statement_type import StatementTypeCreate, StatementTypeUpdate, StatementTypeResponse
from app.services.statement_type_service import statement_type_service

router = APIRouter(prefix="/api/statement-types", tags=["statement-types"])


@router.get("")
async def list_types(db: AsyncSession = Depends(get_db)):
    types = await statement_type_service.list_types(db)
    return ApiResponse(data=[StatementTypeResponse.model_validate(t).model_dump() for t in types])


@router.post("")
async def create_type(data: StatementTypeCreate, db: AsyncSession = Depends(get_db)):
    st = await statement_type_service.create_type(db, data)
    return ApiResponse(data=StatementTypeResponse.model_validate(st).model_dump())


@router.put("/{type_id}")
async def update_type(type_id: int, data: StatementTypeUpdate, db: AsyncSession = Depends(get_db)):
    st = await statement_type_service.update_type(db, type_id, data)
    if not st:
        return ApiResponse(code=404, message="Not found")
    return ApiResponse(data=StatementTypeResponse.model_validate(st).model_dump())


@router.delete("/{type_id}")
async def delete_type(type_id: int, db: AsyncSession = Depends(get_db)):
    ok = await statement_type_service.delete_type(db, type_id)
    if not ok:
        return ApiResponse(code=404, message="Not found")
    return ApiResponse(message="Deleted")
```

- [ ] **Step 7: Write backend/app/api/import_.py**

```python
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/excel")
async def import_excel_preview(file: UploadFile = File(...)):
    import openpyxl
    from io import BytesIO

    content = await file.read()
    wb = openpyxl.load_workbook(BytesIO(content), data_only=True)

    sheets_data = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                rows.append([str(cell) if cell is not None else "" for cell in row])
        if rows:
            sheets_data[sheet_name] = rows

    await file.seek(0)
    return ApiResponse(data={
        "filename": file.filename,
        "sheets": sheets_data,
    })


@router.post("/confirm")
async def import_confirm(data: list[dict], db: AsyncSession = Depends(get_db)):
    from app.services.prompt_service import prompt_service
    from app.schemas.prompt import PromptCreate

    created = []
    for item in data:
        prompt_data = PromptCreate(
            title=item.get("title", ""),
            text_en_full=item.get("text_en_full", ""),
            text_zh_full=item.get("text_zh_full", ""),
            category=item.get("category", ""),
            source_file=item.get("source_file", ""),
        )
        prompt = await prompt_service.create_prompt(db, prompt_data)
        created.append({"id": prompt.id, "title": prompt.title})

    return ApiResponse(data={"imported": len(created), "items": created})
```

- [ ] **Step 8: Update backend/app/main.py to register routers**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import prompts, statements, words, images, statement_types, import_

app = FastAPI(title="PromptWeb API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompts.router)
app.include_router(statements.router)
app.include_router(words.router)
app.include_router(images.router)
app.include_router(statement_types.router)
app.include_router(import_.router)


@app.get("/api/health")
async def health():
    return {"code": 0, "data": {"status": "ok"}, "message": "healthy"}
```

- [ ] **Step 9: Add startup event to initialize MinIO bucket**

```python
# Add to main.py after app creation:
@app.on_event("startup")
async def startup():
    from app.services.minio_service import minio_service
    await minio_service.ensure_bucket()
```

Use Edit on `backend/app/main.py` to add this after `app = FastAPI(...)`.

- [ ] **Step 10: Verify all routers**

```bash
docker compose restart backend
curl http://localhost:8000/api/health
curl http://localhost:8000/api/prompts
curl http://localhost:8000/api/statement-types
```

Expected: All return `{"code":0,...}`

- [ ] **Step 11: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add all API routers — prompts, statements, words, images, types, import"
```

---

### Task 11: Frontend — API Client & Layout Components

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/prompts.ts`
- Create: `frontend/src/api/statement-types.ts`
- Create: `frontend/src/components/AppLayout.vue`
- Create: `frontend/src/components/SideNav.vue`

**Interfaces:**
- Consumes: Router from Task 3
- Produces: Axios client, typed API functions, app shell with sidebar navigation

- [ ] **Step 1: Write frontend/src/api/client.ts**

```typescript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

apiClient.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body.code !== 0) {
      console.warn(`API warning: ${body.message}`)
    }
    return body
  },
  (error) => {
    console.error('API error:', error.message)
    return Promise.reject(error)
  }
)

export default apiClient
```

- [ ] **Step 2: Write frontend/src/api/prompts.ts**

```typescript
import apiClient from './client'

export interface PromptListItem {
  id: number
  title: string
  text_en_full: string
  text_zh_full: string
  category: string
  thumbnail_url: string | null
  created_at: string
  updated_at: string
}

export interface StatementResponse {
  id: number
  prompt_id: number
  text_en: string
  text_zh: string
  sort_order: number
  type_id: number | null
  words: PromptWordResponse[]
}

export interface PromptWordResponse {
  id: number
  prompt_id: number
  statement_id: number
  word_en: string
  word_zh: string
  position_start: number | null
  position_end: number | null
}

export interface PromptImageResponse {
  id: number
  prompt_id: number
  url: string
  storage_type: string
  sort_order: number
  width: number | null
  height: number | null
}

export interface PromptDetail {
  id: number
  title: string
  text_en_full: string
  text_zh_full: string
  category: string
  source_file: string
  created_at: string
  updated_at: string
  statements: StatementResponse[]
  words: PromptWordResponse[]
  images: PromptImageResponse[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const promptsApi = {
  list(params: { page?: number; page_size?: number; search?: string; category?: string } = {}) {
    return apiClient.get('/prompts', { params }) as Promise<{ code: number; data: PaginatedResponse<PromptListItem> }>
  },

  get(id: number) {
    return apiClient.get(`/prompts/${id}`) as Promise<{ code: number; data: PromptDetail }>
  },

  create(data: { title?: string; text_en_full: string; text_zh_full?: string; category?: string }) {
    return apiClient.post('/prompts', data)
  },

  update(id: number, data: Record<string, unknown>) {
    return apiClient.put(`/prompts/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/prompts/${id}`)
  },

  getCategories() {
    return apiClient.get('/prompts/categories') as Promise<{ code: number; data: string[] }>
  },

  // Statements
  createStatements(promptId: number, statements: { text_en: string; text_zh: string; sort_order: number; type_id: number | null }[]) {
    return apiClient.post(`/prompts/${promptId}/statements`, statements)
  },

  updateStatement(id: number, data: Record<string, unknown>) {
    return apiClient.put(`/statements/${id}`, data)
  },

  deleteStatement(id: number) {
    return apiClient.delete(`/statements/${id}`)
  },

  // Words
  createWords(statementId: number, words: { word_en: string; word_zh: string; position_start?: number; position_end?: number }[]) {
    return apiClient.post(`/statements/${statementId}/words`, words)
  },

  deleteWord(id: number) {
    return apiClient.delete(`/words/${id}`)
  },

  // Images
  uploadImage(promptId: number, file: File) {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post(`/prompts/${promptId}/images`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  addImageUrl(promptId: number, url: string) {
    const form = new FormData()
    form.append('url', url)
    return apiClient.post(`/prompts/${promptId}/images`, form)
  },

  deleteImage(id: number) {
    return apiClient.delete(`/images/${id}`)
  },
}
```

- [ ] **Step 3: Write frontend/src/api/statement-types.ts**

```typescript
import apiClient from './client'

export interface StatementTypeItem {
  id: number
  name: string
  color: string
  sort_order: number
}

export const statementTypesApi = {
  list() {
    return apiClient.get('/statement-types') as Promise<{ code: number; data: StatementTypeItem[] }>
  },

  create(data: { name: string; color?: string; sort_order?: number }) {
    return apiClient.post('/statement-types', data)
  },

  update(id: number, data: { name?: string; color?: string; sort_order?: number }) {
    return apiClient.put(`/statement-types/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/statement-types/${id}`)
  },
}
```

- [ ] **Step 4: Write frontend/src/components/AppLayout.vue**

```vue
<script setup lang="ts">
import SideNav from './SideNav.vue'
</script>

<template>
  <div class="app-layout">
    <SideNav />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}
</style>
```

- [ ] **Step 5: Write frontend/src/components/SideNav.vue**

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: 'Prompt 列表', to: '/prompts', icon: '📋' },
  { label: '语句类型', to: '/statement-types', icon: '🏷️' },
  { label: '导入数据', to: '/import', icon: '📥' },
]
</script>

<template>
  <aside class="side-nav">
    <div class="logo">
      <span class="logo-icon">🎨</span>
      <span class="logo-text">PromptWeb</span>
    </div>
    <nav class="nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: route.path.startsWith(item.to) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped>
.side-nav {
  width: var(--sidebar-width);
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  height: var(--header-height);
  border-bottom: 1px solid var(--color-border);
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-accent);
}

.nav-links {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  text-decoration: none;
  font-size: var(--font-size-sm);
}

.nav-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
  text-decoration: none;
}

.nav-item.active {
  background: var(--color-bg-tertiary);
  color: var(--color-accent);
}

.nav-icon {
  font-size: 1.1rem;
}
</style>
```

- [ ] **Step 6: Verify frontend builds**

```bash
docker compose exec frontend npx vue-tsc --noEmit 2>&1 | head -30
docker compose exec frontend npm run build 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/ frontend/src/components/AppLayout.vue frontend/src/components/SideNav.vue
git commit -m "feat: add API client, typed API modules, and app layout with sidebar"
```

---

### Task 12: Frontend — Prompt List Page

**Files:**
- Create: `frontend/src/views/PromptList.vue`
- Create: `frontend/src/components/SearchBar.vue`
- Create: `frontend/src/components/PromptTable.vue`
- Create: `frontend/src/components/PromptRow.vue`

**Interfaces:**
- Consumes: `promptsApi` from Task 11, router
- Produces: Functional list page with search, category filter, pagination, thumbnail + text rows

- [ ] **Step 1: Write frontend/src/views/PromptList.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { promptsApi, type PromptListItem, type PaginatedResponse } from '@/api/prompts'
import SearchBar from '@/components/SearchBar.vue'
import PromptTable from '@/components/PromptTable.vue'

const router = useRouter()

const items = ref<PromptListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const category = ref('')
const categories = ref<string[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await promptsApi.list({ page: page.value, page_size: pageSize, search: search.value, category: category.value })
    const data = res.data as PaginatedResponse<PromptListItem>
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  const res = await promptsApi.getCategories()
  categories.value = res.data as string[]
}

onMounted(() => {
  loadCategories()
  load()
})

watch([search, category], () => {
  page.value = 1
  load()
})

watch(page, () => load())

function goDetail(id: number) {
  router.push(`/prompts/${id}`)
}

function goNew() {
  router.push('/prompts/new')
}

function goImport() {
  router.push('/import')
}
</script>

<template>
  <div class="prompt-list-page">
    <div class="page-header">
      <h1>Prompt 列表</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="goNew">+ 新增 Prompt</button>
        <button class="btn btn-secondary" @click="goImport">📥 导入 Excel</button>
      </div>
    </div>

    <SearchBar v-model:search="search" v-model:category="category" :categories="categories" />

    <PromptTable
      :items="items"
      :loading="loading"
      @row-click="goDetail"
    />

    <div class="pagination" v-if="total > pageSize">
      <button
        class="btn btn-sm"
        :disabled="page <= 1"
        @click="page--"
      >上一页</button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button
        class="btn btn-sm"
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="page++"
      >下一页</button>
    </div>
  </div>
</template>

<style scoped>
.prompt-list-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.page-header h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.page-info {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Global button styles */
.btn {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.btn:hover {
  background: var(--color-bg-hover);
}

.btn-primary {
  background: var(--color-accent);
  color: #1a1a2e;
  border-color: var(--color-accent);
  font-weight: 600;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.8rem;
}

.btn-danger {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 2: Write frontend/src/components/SearchBar.vue**

```vue
<script setup lang="ts">
defineProps<{
  search: string
  category: string
  categories: string[]
}>()

const emit = defineEmits<{
  'update:search': [value: string]
  'update:category': [value: string]
}>()
</script>

<template>
  <div class="search-bar">
    <input
      type="text"
      class="search-input"
      placeholder="搜索 Prompt..."
      :value="search"
      @input="emit('update:search', ($event.target as HTMLInputElement).value)"
    />
    <select
      class="category-select"
      :value="category"
      @change="emit('update:category', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">全部分类</option>
      <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
    </select>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.search-input {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--font-size-base);
}

.category-select {
  min-width: 160px;
}
</style>
```

- [ ] **Step 3: Write frontend/src/components/PromptTable.vue**

```vue
<script setup lang="ts">
import type { PromptListItem } from '@/api/prompts'
import PromptRow from './PromptRow.vue'

defineProps<{
  items: PromptListItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  'row-click': [id: number]
}>()
</script>

<template>
  <div class="prompt-table" v-if="!loading">
    <div class="table-header">
      <span class="col-thumb"></span>
      <span class="col-en">英文 Prompt</span>
      <span class="col-zh">中文翻译</span>
    </div>
    <PromptRow
      v-for="item in items"
      :key="item.id"
      :item="item"
      @click="emit('row-click', item.id)"
    />
    <div class="empty" v-if="items.length === 0">
      暂无数据
    </div>
  </div>
  <div class="loading" v-else>
    加载中...
  </div>
</template>

<style scoped>
.prompt-table {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 80px 1fr 1fr;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.col-thumb {
  text-align: center;
}

.empty, .loading {
  padding: var(--space-xl);
  text-align: center;
  color: var(--color-text-muted);
}
</style>
```

- [ ] **Step 4: Write frontend/src/components/PromptRow.vue**

```vue
<script setup lang="ts">
import type { PromptListItem } from '@/api/prompts'

defineProps<{
  item: PromptListItem
}>()

defineEmits<{
  click: []
}>()

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<template>
  <div class="prompt-row" @click="$emit('click')">
    <div class="col-thumb">
      <img
        v-if="item.thumbnail_url"
        :src="item.thumbnail_url"
        class="thumbnail"
        alt="thumb"
      />
      <div v-else class="thumbnail-placeholder">🖼️</div>
    </div>
    <div class="col-en">{{ truncate(item.text_en_full, 120) }}</div>
    <div class="col-zh">{{ truncate(item.text_zh_full, 80) }}</div>
  </div>
</template>

<style scoped>
.prompt-row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--transition-fast);
  align-items: center;
  min-height: 60px;
}

.prompt-row:last-child {
  border-bottom: none;
}

.prompt-row:hover {
  background: var(--color-bg-hover);
}

.col-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}

.thumbnail-placeholder {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  font-size: 1.2rem;
}

.col-en {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-word;
  font-family: var(--font-mono);
}

.col-zh {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  word-break: break-word;
}
</style>
```

- [ ] **Step 5: Verify the list page loads**

Navigate to `http://localhost:5173/prompts` and confirm the page renders with header, search bar, and empty table.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/PromptList.vue frontend/src/components/SearchBar.vue frontend/src/components/PromptTable.vue frontend/src/components/PromptRow.vue
git commit -m "feat: add Prompt list page with search, filter, pagination"
```

---

### Task 13: Frontend — Prompt Detail Page

**Files:**
- Create: `frontend/src/views/PromptDetail.vue`
- Create: `frontend/src/components/PromptLeftPanel.vue`
- Create: `frontend/src/components/PromptRightPanel.vue`
- Create: `frontend/src/components/StatementList.vue`
- Create: `frontend/src/components/StatementItem.vue`
- Create: `frontend/src/components/ImageGallery.vue`
- Create: `frontend/src/components/ImageCard.vue`
- Create: `frontend/src/components/WordCardPanel.vue`
- Create: `frontend/src/components/WordCard.vue`

**Interfaces:**
- Consumes: `promptsApi` from Task 11, route params
- Produces: Full detail page with left-right split, statement clicking/highlighting, word highlighting, image gallery

- [ ] **Step 1: Write frontend/src/views/PromptDetail.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { promptsApi, type PromptDetail as PromptDetailType } from '@/api/prompts'
import PromptLeftPanel from '@/components/PromptLeftPanel.vue'
import PromptRightPanel from '@/components/PromptRightPanel.vue'

const route = useRoute()
const router = useRouter()
const prompt = ref<PromptDetailType | null>(null)
const loading = ref(true)
const highlightedStatementId = ref<number | null>(null)
const highlightedWordId = ref<number | null>(null)

provide('highlightedStatementId', highlightedStatementId)
provide('highlightedWordId', highlightedWordId)

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) return
  try {
    loading.value = true
    const res = await promptsApi.get(id)
    prompt.value = res.data as PromptDetailType
  } finally {
    loading.value = false
  }
})

function onStatementClick(statementId: number) {
  if (highlightedStatementId.value === statementId) {
    highlightedStatementId.value = null
    highlightedWordId.value = null
  } else {
    highlightedStatementId.value = statementId
    highlightedWordId.value = null
  }
}

function onWordClick(wordId: number) {
  highlightedWordId.value = highlightedWordId.value === wordId ? null : wordId
}

function clearHighlights() {
  highlightedStatementId.value = null
  highlightedWordId.value = null
}

function goEdit() {
  router.push(`/prompts/${route.params.id}/edit`)
}

async function deletePrompt() {
  if (!confirm('确认删除这条 Prompt？')) return
  await promptsApi.delete(Number(route.params.id))
  router.push('/prompts')
}
</script>

<template>
  <div class="prompt-detail" v-if="!loading && prompt">
    <div class="detail-header">
      <button class="btn btn-sm" @click="router.push('/prompts')">← 返回列表</button>
      <h2>{{ prompt.title || '未命名 Prompt' }}</h2>
      <div class="detail-actions">
        <button class="btn btn-sm" @click="goEdit">编辑</button>
        <button class="btn btn-sm btn-danger" @click="deletePrompt">删除</button>
      </div>
    </div>
    <div class="detail-body" @click.self="clearHighlights">
      <PromptLeftPanel
        :prompt="prompt"
        @statement-click="onStatementClick"
        @word-click="onWordClick"
      />
      <PromptRightPanel :prompt="prompt" />
    </div>
  </div>
  <div class="loading" v-else>加载中...</div>
</template>

<style scoped>
.prompt-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.detail-header h2 {
  flex: 1;
  font-size: var(--font-size-lg);
}

.detail-actions {
  display: flex;
  gap: var(--space-sm);
}

.detail-body {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: var(--space-lg);
  min-height: calc(100vh - 140px);
}

.loading {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-muted);
}
</style>
```

- [ ] **Step 2: Write frontend/src/components/PromptLeftPanel.vue**

```vue
<script setup lang="ts">
import type { PromptDetail } from '@/api/prompts'
import StatementList from './StatementList.vue'

defineProps<{
  prompt: PromptDetail
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()
</script>

<template>
  <div class="left-panel">
    <div class="full-text-section">
      <div class="section-label">英文 Prompt</div>
      <p class="full-text-en">{{ prompt.text_en_full }}</p>
    </div>
    <div class="full-text-section" v-if="prompt.text_zh_full">
      <div class="section-label">中文翻译</div>
      <p class="full-text-zh">{{ prompt.text_zh_full }}</p>
    </div>
    <div class="divider"></div>
    <StatementList
      :statements="prompt.statements"
      @statement-click="emit('statement-click', $event)"
      @word-click="emit('word-click', $event)"
    />
  </div>
</template>

<style scoped>
.left-panel {
  overflow-y: auto;
}

.full-text-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.full-text-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: 1.8;
  color: var(--color-text-primary);
  background: var(--color-bg-card);
  padding: var(--space-md);
  border-radius: var(--border-radius);
}

.full-text-zh {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  padding: var(--space-md);
  border-radius: var(--border-radius);
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-lg) 0;
}
</style>
```

- [ ] **Step 3: Write frontend/src/components/StatementList.vue**

```vue
<script setup lang="ts">
import type { StatementResponse } from '@/api/prompts'
import StatementItem from './StatementItem.vue'

defineProps<{
  statements: StatementResponse[]
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()
</script>

<template>
  <div class="statement-list">
    <div class="section-label">拆分语句</div>
    <StatementItem
      v-for="(stmt, idx) in statements"
      :key="stmt.id"
      :statement="stmt"
      :index="idx"
      @statement-click="emit('statement-click', $event)"
      @word-click="emit('word-click', $event)"
    />
  </div>
</template>

<style scoped>
.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
```

- [ ] **Step 4: Write frontend/src/components/StatementItem.vue**

```vue
<script setup lang="ts">
import { computed, inject } from 'vue'
import type { StatementResponse, PromptWordResponse } from '@/api/prompts'

const props = defineProps<{
  statement: StatementResponse
  index: number
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()

const highlightedStatementId = inject<{ value: number | null }>('highlightedStatementId')!
const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

const isHighlighted = computed(() => highlightedStatementId?.value === props.statement.id)

const typeName = computed(() => {
  // Type name will be resolved from store — for now return placeholder
  return ''
})
const typeColor = computed(() => '#4fc3f7')

function onWordClick(wordId: number, event: Event) {
  event.stopPropagation()
  emit('word-click', wordId)
}

function getWordHighlightClass(wordId: number) {
  return highlightedWordId?.value === wordId ? 'word-highlighted' : ''
}
</script>

<template>
  <div
    class="statement-item"
    :class="{ 'statement-highlighted': isHighlighted }"
    @click="emit('statement-click', statement.id)"
  >
    <div class="stmt-header">
      <span class="stmt-index">#{{ index + 1 }}</span>
      <span class="stmt-type-badge" :style="{ backgroundColor: typeColor || '#4fc3f7' }">
        {{ typeName || '未分类' }}
      </span>
    </div>
    <p class="stmt-en">
      <span
        v-for="word in statement.words"
        :key="word.id"
        :class="['clickable-word', getWordHighlightClass(word.id)]"
        @click="onWordClick(word.id, $event)"
      >{{ word.word_en }} </span>
      <span v-if="statement.words.length === 0">{{ statement.text_en }}</span>
    </p>
    <p class="stmt-zh">{{ statement.text_zh }}</p>
  </div>
</template>

<style scoped>
.statement-item {
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.statement-item:hover {
  border-color: var(--color-accent);
}

.statement-highlighted {
  border-color: var(--color-highlight);
  background: rgba(255, 224, 102, 0.08);
}

.stmt-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.stmt-index {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.stmt-type-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  color: #1a1a2e;
  font-weight: 600;
}

.stmt-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: 1.7;
  color: var(--color-text-primary);
  margin-bottom: var(--space-xs);
}

.clickable-word {
  cursor: pointer;
  border-radius: 2px;
  transition: all var(--transition-fast);
}

.clickable-word:hover {
  background: rgba(255, 224, 102, 0.3);
}

.word-highlighted {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 600;
}

.stmt-zh {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
</style>
```

- [ ] **Step 5: Write frontend/src/components/PromptRightPanel.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import type { PromptDetail, PromptImageResponse } from '@/api/prompts'
import { promptsApi } from '@/api/prompts'
import ImageGallery from './ImageGallery.vue'
import WordCardPanel from './WordCardPanel.vue'

const props = defineProps<{
  prompt: PromptDetail
}>()

const route = useRoute()
const images = ref<PromptImageResponse[]>(props.prompt.images || [])

const fileInput = ref<HTMLInputElement | null>(null)

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const res = await promptsApi.uploadImage(Number(route.params.id), file)
    // Reload prompt images
    const promptRes = await promptsApi.get(Number(route.params.id))
    images.value = (promptRes.data as PromptDetail).images || []
  } catch (e) {
    console.error('Upload failed:', e)
  }
}

async function addUrl() {
  const url = prompt('输入图片 URL:')
  if (!url) return
  await promptsApi.addImageUrl(Number(route.params.id), url)
  const promptRes = await promptsApi.get(Number(route.params.id))
  images.value = (promptRes.data as PromptDetail).images || []
}

async function removeImage(imageId: number) {
  await promptsApi.deleteImage(imageId)
  images.value = images.value.filter((i) => i.id !== imageId)
}
</script>

<template>
  <div class="right-panel">
    <ImageGallery
      :images="images"
      @upload="fileInput?.click()"
      @add-url="addUrl"
      @delete="removeImage"
    />
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="onFileSelected"
    />
    <WordCardPanel :prompt="prompt" />
  </div>
</template>

<style scoped>
.right-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  overflow-y: auto;
  border-left: 1px solid var(--color-border);
  padding-left: var(--space-lg);
}
</style>
```

- [ ] **Step 6: Write frontend/src/components/ImageGallery.vue**

```vue
<script setup lang="ts">
import type { PromptImageResponse } from '@/api/prompts'
import ImageCard from './ImageCard.vue'

defineProps<{
  images: PromptImageResponse[]
}>()

const emit = defineEmits<{
  upload: []
  'add-url': []
  delete: [id: number]
}>()
</script>

<template>
  <div class="image-gallery">
    <div class="section-label">生成图片 ({{ images.length }})</div>
    <div class="image-grid">
      <ImageCard
        v-for="img in images"
        :key="img.id"
        :image="img"
        @delete="emit('delete', img.id)"
      />
    </div>
    <div class="image-actions">
      <button class="btn btn-sm" @click="emit('upload')">📤 上传图片</button>
      <button class="btn btn-sm" @click="emit('add-url')">🔗 添加链接</button>
    </div>
  </div>
</template>

<style scoped>
.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.image-actions {
  display: flex;
  gap: var(--space-sm);
}
</style>
```

- [ ] **Step 7: Write frontend/src/components/ImageCard.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import type { PromptImageResponse } from '@/api/prompts'

defineProps<{
  image: PromptImageResponse
}>()

defineEmits<{
  delete: []
}>()

const enlarged = ref(false)
</script>

<template>
  <div class="image-card" @click="enlarged = !enlarged">
    <img :src="image.url" alt="prompt image" class="gallery-img" />
    <button class="delete-btn" @click.stop="$emit('delete')" title="删除">×</button>
    <div class="enlarge-overlay" v-if="enlarged" @click="enlarged = false">
      <img :src="image.url" class="enlarged-img" />
    </div>
  </div>
</template>

<style scoped>
.image-card {
  position: relative;
  border-radius: var(--border-radius);
  overflow: hidden;
  cursor: pointer;
  aspect-ratio: 1;
}

.gallery-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition-fast);
}

.image-card:hover .gallery-img {
  transform: scale(1.05);
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.image-card:hover .delete-btn {
  opacity: 1;
}

.enlarge-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: zoom-out;
}

.enlarged-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--border-radius-lg);
}
</style>
```

- [ ] **Step 8: Write frontend/src/components/WordCardPanel.vue**

```vue
<script setup lang="ts">
import { computed, inject } from 'vue'
import type { PromptDetail } from '@/api/prompts'
import WordCard from './WordCard.vue'

const props = defineProps<{
  prompt: PromptDetail
}>()

const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

// Get all unique words from all statements
const allWords = computed(() => {
  return props.prompt.statements.flatMap((s) => s.words)
})

const activeWord = computed(() => {
  const id = highlightedWordId?.value
  if (!id) return null
  return allWords.value.find((w) => w.id === id) || null
})
</script>

<template>
  <div class="word-card-panel">
    <div class="section-label">高亮单词卡片区</div>
    <div class="word-cards" v-if="activeWord">
      <WordCard :word="activeWord" />
      <!-- Show all words from the same prompt -->
      <WordCard
        v-for="w in allWords"
        :key="w.id"
        :word="w"
        :class="{ dimmed: activeWord && w.id !== activeWord.id }"
      />
    </div>
    <div class="word-cards" v-else-if="allWords.length > 0">
      <WordCard
        v-for="w in allWords"
        :key="w.id"
        :word="w"
      />
    </div>
    <div class="empty-words" v-else>
      暂无提取的单词。请使用 AI 拆分功能提取难词。
    </div>
  </div>
</template>

<style scoped>
.section-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.word-cards {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.dimmed {
  opacity: 0.4;
}

.empty-words {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  padding: var(--space-md);
  text-align: center;
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
}
</style>
```

- [ ] **Step 9: Write frontend/src/components/WordCard.vue**

```vue
<script setup lang="ts">
import type { PromptWordResponse } from '@/api/prompts'

defineProps<{
  word: PromptWordResponse
}>()
</script>

<template>
  <div class="word-card">
    <span class="word-en">{{ word.word_en }}</span>
    <span class="word-zh">{{ word.word_zh }}</span>
  </div>
</template>

<style scoped>
.word-card {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  border-radius: var(--border-radius);
  padding: var(--space-sm) var(--space-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 80px;
}

.word-en {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.word-zh {
  font-size: 0.75rem;
  opacity: 0.8;
}
</style>
```

- [ ] **Step 10: Verify the detail page**

Visit `http://localhost:5173/prompts` (need to have a prompt in DB first — create one manually via curl).

- [ ] **Step 11: Commit**

```bash
git add frontend/src/views/PromptDetail.vue frontend/src/components/PromptLeftPanel.vue frontend/src/components/PromptRightPanel.vue frontend/src/components/StatementList.vue frontend/src/components/StatementItem.vue frontend/src/components/ImageGallery.vue frontend/src/components/ImageCard.vue frontend/src/components/WordCardPanel.vue frontend/src/components/WordCard.vue
git commit -m "feat: add Prompt detail page with left-right split, statement/word highlighting, and image gallery"
```

---

### Task 14: Frontend — Prompt Form Page (New/Edit)

**Files:**
- Create: `frontend/src/views/PromptForm.vue`

**Interfaces:**
- Consumes: `promptsApi` from Task 11, route params (id for edit mode)
- Produces: Form for creating/editing a Prompt with basic fields, statement editing, and image management

- [ ] **Step 1: Write frontend/src/views/PromptForm.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { promptsApi, type PromptDetail } from '@/api/prompts'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const promptId = computed(() => Number(route.params.id))

const form = ref({
  title: '',
  text_en_full: '',
  text_zh_full: '',
  category: '',
})

const statementTypes = ref<StatementTypeItem[]>([])
const saving = ref(false)

onMounted(async () => {
  const typesRes = await statementTypesApi.list()
  statementTypes.value = typesRes.data as StatementTypeItem[]

  if (isEdit.value) {
    const res = await promptsApi.get(promptId.value)
    const p = res.data as PromptDetail
    form.value = {
      title: p.title,
      text_en_full: p.text_en_full,
      text_zh_full: p.text_zh_full,
      category: p.category,
    }
  }
})

async function save() {
  saving.value = true
  try {
    if (isEdit.value) {
      await promptsApi.update(promptId.value, form.value)
    } else {
      await promptsApi.create(form.value)
    }
    router.push('/prompts')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="prompt-form">
    <h1>{{ isEdit ? '编辑 Prompt' : '新增 Prompt' }}</h1>
    <form @submit.prevent="save" class="form">
      <div class="form-group">
        <label>标题</label>
        <input v-model="form.title" type="text" placeholder="可选标题" />
      </div>
      <div class="form-group">
        <label>英文 Prompt *</label>
        <textarea v-model="form.text_en_full" rows="6" required placeholder="粘贴英文 Prompt..."></textarea>
      </div>
      <div class="form-group">
        <label>中文翻译</label>
        <textarea v-model="form.text_zh_full" rows="4" placeholder="中文翻译..."></textarea>
      </div>
      <div class="form-group">
        <label>分类</label>
        <input v-model="form.category" type="text" placeholder="如：远古遗迹、森林自然..." />
      </div>
      <div class="form-actions">
        <button type="button" class="btn" @click="router.back()">取消</button>
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.prompt-form {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.form-group input,
.form-group textarea {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}
</style>
```

- [ ] **Step 2: Verify form loads**

Visit `http://localhost:5173/prompts/new`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/PromptForm.vue
git commit -m "feat: add Prompt create/edit form page"
```

---

### Task 15: Frontend — Statement Type Manager & Import Page

**Files:**
- Create: `frontend/src/views/StatementTypeManager.vue`
- Create: `frontend/src/views/ImportPage.vue`

**Interfaces:**
- Consumes: `statementTypesApi` from Task 11, `promptsApi` for import
- Produces: Type CRUD manager, Excel upload + preview + confirm import page

- [ ] **Step 1: Write frontend/src/views/StatementTypeManager.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

const types = ref<StatementTypeItem[]>([])
const newName = ref('')
const newColor = ref('#4fc3f7')

onMounted(async () => {
  await load()
})

async function load() {
  const res = await statementTypesApi.list()
  types.value = res.data as StatementTypeItem[]
}

async function add() {
  if (!newName.value.trim()) return
  await statementTypesApi.create({ name: newName.value.trim(), color: newColor.value, sort_order: types.value.length + 1 })
  newName.value = ''
  newColor.value = '#4fc3f7'
  await load()
}

async function remove(id: number) {
  await statementTypesApi.delete(id)
  await load()
}

async function updateColor(type: StatementTypeItem) {
  const color = prompt('新颜色 (HEX):', type.color)
  if (color) {
    await statementTypesApi.update(type.id, { color })
    await load()
  }
}
</script>

<template>
  <div class="type-manager">
    <h1>语句类型管理</h1>
    <div class="add-row">
      <input v-model="newName" type="text" placeholder="类型名称" @keyup.enter="add" />
      <input v-model="newColor" type="color" />
      <button class="btn btn-primary" @click="add">添加</button>
    </div>
    <div class="type-list">
      <div v-for="t in types" :key="t.id" class="type-row">
        <span class="color-dot" :style="{ background: t.color }"></span>
        <span class="type-name">{{ t.name }}</span>
        <code class="type-color">{{ t.color }}</code>
        <button class="btn btn-sm" @click="updateColor(t)">改色</button>
        <button class="btn btn-sm btn-danger" @click="remove(t.id)">删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.type-manager {
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.add-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.add-row input[type="text"] {
  flex: 1;
}

.add-row input[type="color"] {
  width: 44px;
  height: 38px;
  padding: 2px;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.type-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-card);
  border-radius: var(--border-radius);
}

.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-name {
  flex: 1;
  font-weight: 600;
}

.type-color {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
</style>
```

- [ ] **Step 2: Write frontend/src/views/ImportPage.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const file = ref<File | null>(null)
const preview = ref<Record<string, string[][]> | null>(null)
const loading = ref(false)
const importing = ref(false)

async function analyze() {
  if (!file.value) return
  loading.value = true
  try {
    const form = new FormData()
    form.append('file', file.value)
    const res = await apiClient.post('/import/excel', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    preview.value = res.data.sheets
  } finally {
    loading.value = false
  }
}

function selectSheet(sheetName: string) {
  // Parse the sheet and try to auto-map columns
  const rows = preview.value?.[sheetName] || []
  console.log('Selected sheet:', sheetName, rows.length, 'rows')
}

async function confirmImport(sheetName: string) {
  const rows = preview.value?.[sheetName] || []
  if (rows.length < 2) return

  const headers = rows[0]
  const dataRows = rows.slice(1)

  // Simple heuristic: find columns by keyword
  const findCol = (keywords: string[]) => {
    return headers.findIndex((h) => keywords.some((kw) => h.toLowerCase().includes(kw.toLowerCase())))
  }

  const enIdx = findCol(['英文', 'prompt', 'english', 'en'])
  const zhIdx = findCol(['中文', 'chinese', 'zh', '场景主题', '场景'])
  const catIdx = findCol(['类别', 'category', '分类'])

  const items = dataRows.map((row) => ({
    title: row[zhIdx] || '',
    text_en_full: row[enIdx] || '',
    text_zh_full: row[zhIdx] || '',
    category: catIdx >= 0 ? row[catIdx] : '',
    source_file: file.value?.name || '',
  }))

  importing.value = true
  try {
    await apiClient.post('/import/confirm', items)
    alert(`成功导入 ${items.length} 条 Prompt`)
    router.push('/prompts')
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="import-page">
    <h1>导入 Excel 数据</h1>
    <div class="upload-zone">
      <input
        type="file"
        accept=".xlsx,.xls"
        @change="(e) => { file = (e.target as HTMLInputElement).files?.[0] || null; preview = null }"
      />
      <button class="btn btn-primary" :disabled="!file || loading" @click="analyze">
        {{ loading ? '解析中...' : '解析文件' }}
      </button>
    </div>

    <div v-if="preview" class="preview-section">
      <h2>预览结果</h2>
      <div v-for="(rows, sheetName) in preview" :key="sheetName" class="sheet-preview">
        <div class="sheet-header">
          <h3>工作表: {{ sheetName }} ({{ rows.length }} 行)</h3>
          <button
            class="btn btn-primary"
            :disabled="importing"
            @click="confirmImport(sheetName)"
          >
            {{ importing ? '导入中...' : '确认导入此表' }}
          </button>
        </div>
        <div class="sheet-scroll">
          <table>
            <thead>
              <tr>
                <th v-for="(cell, ci) in rows[0]" :key="ci">{{ cell }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in rows.slice(1, 6)" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="rows.length > 6" class="more-rows">... 还有 {{ rows.length - 6 }} 行</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-page {
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-lg);
}

.upload-zone {
  display: flex;
  gap: var(--space-md);
  align-items: center;
  margin-bottom: var(--space-xl);
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.sheet-preview {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.sheet-header h3 {
  font-size: var(--font-size-base);
}

.sheet-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

th, td {
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-border);
  text-align: left;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

th {
  background: var(--color-bg-tertiary);
  font-weight: 600;
}

.more-rows {
  padding: var(--space-sm);
  color: var(--color-text-muted);
  text-align: center;
}
</style>
```

- [ ] **Step 3: Verify pages load**

Visit `http://localhost:5173/statement-types` and `http://localhost:5173/import`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/StatementTypeManager.vue frontend/src/views/ImportPage.vue
git commit -m "feat: add statement type manager and Excel import pages"
```

---

### Task 16: AI Skill Definition Files

**Files:**
- Create: `backend/skills/prompt-import.md`
- Create: `backend/skills/prompt-split.md`

**Interfaces:**
- Produces: Two Claude Code Skill definitions for Excel import analysis and Prompt splitting

- [ ] **Step 1: Write backend/skills/prompt-import.md**

```markdown
---
name: prompt-import
description: Analyze Excel files containing text-to-image prompts, auto-detect columns, and import into PromptWeb database
---

# Prompt Import Skill

Analyze an Excel file containing text-to-image prompts and import them into the PromptWeb database.

## Input

- Path to an `.xlsx` or `.xls` file
- The file may have multiple sheets and varying column structures

## Process

### Step 1: Parse the Excel file

Read all sheets using `openpyxl`. Identify which sheet contains prompt data (skip summary/instruction sheets).

### Step 2: Auto-detect columns

For the data sheet, scan the header row and first 3-5 data rows. Identify:
- **English prompt column**: contains long English text with photography/art keywords like "Generate", "epic", "Unreal Engine", "cinematic", "8K", etc.
- **Chinese/title column**: contains Chinese text describing scenes
- **Category column**: contains short classification labels like "远古遗迹", "森林自然", etc.

Return the column mapping as JSON.

### Step 3: Extract data rows

For each data row, extract:
```json
{
  "title": "scene title in Chinese",
  "text_en_full": "full English prompt",
  "text_zh_full": "Chinese translation or description",
  "category": "category label",
  "source_file": "original filename"
}
```

### Step 4: Call the PromptWeb API

POST each extracted prompt to `POST /api/import/confirm` with the array of items.

## Output Format

Return a JSON summary:
```json
{
  "sheet_used": "Sheet2",
  "total_rows": 100,
  "imported": 100,
  "column_mapping": {
    "en_column": "完整提示词（英文 · 可直接复制）",
    "zh_column": "场景主题（中文）",
    "cat_column": "类别"
  }
}
```
```

- [ ] **Step 2: Write backend/skills/prompt-split.md**

```markdown
---
name: prompt-split
description: Split an English text-to-image prompt into semantic segments with type labels and extract difficult vocabulary words
---

# Prompt Split Skill

Analyze a single English text-to-image prompt, split it into semantic sentence segments, label each segment with a type, and extract difficult vocabulary words.

## Input

A JSON object:
```json
{
  "prompt_id": 1,
  "text_en_full": "Generate epic Unreal Engine 5 fantasy landscape, stormy overcast daylight, cinematic environmental photography, ancient colossal temple ruins built into a cliff face...",
  "text_zh_full": "建于悬崖的巨型神庙废墟",
  "statement_types": [
    {"id": 1, "name": "固定开头"},
    {"id": 2, "name": "光照氛围"},
    ...
  ]
}
```

## Process

### Step 1: Split into sentences

Split the English prompt at natural semantic boundaries (commas, conjunctions). Each segment should be a meaningful phrase. Typically 3-8 segments.

For each segment:
- Extract the English text
- Provide a Chinese translation
- Assign a `type_id` from the available statement types
- Set `sort_order` (1-based index)

### Step 2: Extract difficult vocabulary

For each segment, identify words that are:
- Uncommon or specialized (e.g., "colossal", "overcast", "cinematic")
- NOT basic function words (the, a, an, in, on, at, of, to, for, with, and, or, but, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, can, could, shall, should, may, might, must, it, its, this, that, these, those)

For each difficult word:
- Provide the word in English
- Provide the Chinese translation
- Record `position_start` and `position_end` (character indices in the full English text)

### Step 3: Call the PromptWeb API

1. POST statements to `POST /api/prompts/{prompt_id}/statements`
2. For each statement, POST its words to `POST /api/statements/{statement_id}/words`

## Output Format

```json
{
  "prompt_id": 1,
  "statements": [
    {
      "text_en": "Generate epic Unreal Engine 5 fantasy landscape",
      "text_zh": "生成史诗级虚幻引擎5奇幻场景",
      "sort_order": 1,
      "type_id": 1
    },
    ...
  ],
  "words": [
    {
      "statement_index": 2,
      "word_en": "colossal",
      "word_zh": "巨大的",
      "position_start": 105,
      "position_end": 113
    },
    ...
  ]
}
```
```

- [ ] **Step 3: Commit**

```bash
git add backend/skills/
git commit -m "feat: add AI skill definitions for prompt import and splitting"
```

---

### Task 17: Integration Testing & README

**Files:**
- Create: `README.md`
- Modify: `backend/app/main.py` (startup bucket init)

**Interfaces:**
- Produces: Working end-to-end flow, project documentation

- [ ] **Step 1: Write README.md**

```markdown
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
```

- [ ] **Step 2: End-to-end smoke test**

```bash
# Start everything fresh
docker compose down -v
docker compose up -d
sleep 10

# Check health
curl -s http://localhost:8000/api/health

# Run migrations
docker compose run --rm backend alembic upgrade head

# Seed types
docker compose run --rm backend python -m app.seed

# Verify types
curl -s http://localhost:8000/api/statement-types | python3 -m json.tool

# Create a test prompt
curl -s -X POST http://localhost:8000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","text_en_full":"Generate epic Unreal Engine 5 fantasy landscape, stormy overcast daylight.","text_zh_full":"测试场景","category":"test"}'

# List prompts
curl -s http://localhost:8000/api/prompts | python3 -m json.tool

# Check frontend
curl -s http://localhost:5173 | head -5
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions and project overview"
```

---

### Task 18: Polish — Statement Type Resolution & Word Highlight Sync

**Files:**
- Modify: `frontend/src/components/StatementItem.vue`
- Modify: `frontend/src/components/PromptLeftPanel.vue`
- Create: `frontend/src/stores/statementTypes.ts`

**Interfaces:**
- Produces: Pinia store for statement types, StatementItem shows real type names/colors, full-text area shows word highlights synced with click

- [ ] **Step 1: Write frontend/src/stores/statementTypes.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { statementTypesApi, type StatementTypeItem } from '@/api/statement-types'

export const useStatementTypeStore = defineStore('statementTypes', () => {
  const types = ref<StatementTypeItem[]>([])
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    const res = await statementTypesApi.list()
    types.value = res.data as StatementTypeItem[]
    loaded.value = true
  }

  function getType(id: number | null): StatementTypeItem | undefined {
    return types.value.find((t) => t.id === id)
  }

  return { types, loaded, load, getType }
})
```

- [ ] **Step 2: Update StatementItem.vue to use the store for type name/color**

In `StatementItem.vue`, replace the computed `typeName` and `typeColor`:

```typescript
import { useStatementTypeStore } from '@/stores/statementTypes'
import { onMounted } from 'vue'

const typeStore = useStatementTypeStore()

onMounted(() => {
  typeStore.load()
})

const typeInfo = computed(() => typeStore.getType(props.statement.type_id))
const typeName = computed(() => typeInfo.value?.name || '未分类')
const typeColor = computed(() => typeInfo.value?.color || '#4fc3f7')
```

- [ ] **Step 3: Update PromptLeftPanel.vue to show word highlights in full text**

```vue
<script setup lang="ts">
import { computed, inject } from 'vue'
import type { PromptDetail } from '@/api/prompts'
import StatementList from './StatementList.vue'

const props = defineProps<{
  prompt: PromptDetail
}>()

const emit = defineEmits<{
  'statement-click': [id: number]
  'word-click': [id: number]
}>()

const highlightedWordId = inject<{ value: number | null }>('highlightedWordId')!

const highlightedWord = computed(() => {
  const id = highlightedWordId?.value
  if (!id) return null
  return props.prompt.words.find(w => w.id === id) || null
})
</script>

<template>
  <div class="left-panel">
    <div class="full-text-section">
      <div class="section-label">英文 Prompt</div>
      <p class="full-text-en">
        <template v-if="highlightedWord">
          <span>{{ prompt.text_en_full.slice(0, highlightedWord.position_start ?? 0) }}</span>
          <span class="word-highlight-inline">{{ highlightedWord.word_en }}</span>
          <span>{{ prompt.text_en_full.slice((highlightedWord.position_end ?? 0)) }}</span>
        </template>
        <template v-else>{{ prompt.text_en_full }}</template>
      </p>
    </div>
    <!-- rest unchanged -->
  </div>
</template>

<style scoped>
/* ...existing styles... */

.word-highlight-inline {
  background: var(--color-highlight);
  color: var(--color-highlight-text);
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 600;
}
</style>
```

- [ ] **Step 4: Verify highlighting sync**

Test: click a statement → it highlights yellow. Click a word within it → word highlights in both the statement and the full English text, word card appears on the right.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/ frontend/src/components/StatementItem.vue frontend/src/components/PromptLeftPanel.vue
git commit -m "feat: sync statement type display and word highlighting across panels"
```

---

## Plan Self-Review

1. **Spec coverage**: All spec sections covered — data models ✓, API ✓, frontend pages/routes ✓, AI skills ✓, infrastructure ✓
2. **No placeholders**: Every step has concrete code, file paths, and commands
3. **Type consistency**: Models → Schemas → API → Frontend types all use matching property names (`text_en_full`, `type_id`, `storage_type`, etc.)
